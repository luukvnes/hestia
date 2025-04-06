import hestia
import logging
import requests
import secrets_1
import login_bouwinvest
from datetime import datetime, timedelta
from asyncio import run
from telegram.error import Forbidden


async def main() -> None:
    
    # Once a day at 7pm, check some stuff and send an alert if necessary
    if datetime.now().hour == 19 and datetime.now().minute < 4:
        message = ""
        if hestia.check_dev_mode():
            message += "\n\nDev mode is enabled."
        if hestia.check_scraper_halted() and 'dev' not in hestia.APP_VERSION:
            message += "\n\nScraper is halted."
    
        # Check if the donation link is expiring soon
        # Expiry of ING payment links is 35 days, start warning after 32
        last_updated = hestia.query_db("SELECT donation_link_updated FROM hestia.meta", fetchOne=True)["donation_link_updated"]
        if datetime.now() - last_updated >= timedelta(days=32):
            message += "\n\nDonation link expiring soon, use /setdonate."
            
        if message:
            await hestia.BOT.send_message(text=message[2:], chat_id=secrets_1.OWN_CHAT_ID)
    
    if not hestia.check_scraper_halted():
        for target in hestia.query_db("SELECT * FROM hestia.targets WHERE enabled = true"):
            try:
                await scrape_site(target)
            except BaseException as e:
                error = f"[{target['agency']} ({target['id']})] {repr(e)}"
                logging.error(error)
                if "Connection reset by peer" not in error:
                    await hestia.BOT.send_message(text=error, chat_id=secrets_1.OWN_CHAT_ID)
    else:
        logging.warning("Scraper is halted.")


async def broadcast(homes: list[hestia.Home]) -> None:
    subs = set()
    
    if hestia.check_dev_mode():
        subs = hestia.query_db("SELECT * FROM hestia.subscribers WHERE subscription_expiry IS NOT NULL AND telegram_enabled = true AND user_level > 1")
    else:
        subs = hestia.query_db("SELECT * FROM hestia.subscribers WHERE subscription_expiry IS NOT NULL AND telegram_enabled = true")
        
    
    for sub in subs:
        filtered_homes = []
        for home in homes:
            # Apply filters
            if (home.price >= sub["filter_min_price"] and home.price <= sub["filter_max_price"]) and \
               (home.city.lower() in sub["filter_cities"]) and \
               (home.agency in sub["filter_agencies"]):
                filtered_homes.append(home)
        for home in filtered_homes:
                if home.agency == "bouwinvest":
                    # If the home is from Bouwinvest, we need to log in first
                    # Create a session
                    session = requests.Session()
                    session.max_redirects = 5
                    login_bouwinvest.sign_in(session, sub['username'], sub['password'])
                    login_bouwinvest.add_house(session, home.url.split("/")[-2])
                    login_bouwinvest.save_preferences(session)
                    message = f"{hestia.HOUSE_EMOJI} SIGNED UP FOR THIS HOME\n" 


            
                message += f"{hestia.HOUSE_EMOJI} {home.address}, {home.city}\n"
                message += f"{hestia.EURO_EMOJI} €{home.price}/m\n\n"
                message = hestia.escape_markdownv2(message)
                message += f"{hestia.LINK_EMOJI} [{home.agency}]({home.url})"
                
                try:
                    await hestia.BOT.send_message(text=message, chat_id=sub["telegram_id"], parse_mode="MarkdownV2")
                except Forbidden as e:
                    # This means the user deleted their account or blocked the bot, so disable them
                    hestia.query_db("UPDATE hestia.subscribers SET telegram_enabled = false WHERE id = %s", params=[str(sub["id"])])
                    log_msg = f"Removed subscriber with Telegram id {str(sub['telegram_id'])} due to broadcast failure: {repr(e)}"
                    logging.warning(log_msg)
                except Exception as e:
                    # Log any other exceptions
                    logging.warning(f"Failed to broadcast to {sub['telegram_id']}: {repr(e)}")


async def scrape_site(target: dict) -> None:
    if target["method"] == "GET":
        r = requests.get(target["queryurl"], headers=target["headers"])
    elif target["method"] == "POST":
        r = requests.post(target["queryurl"], json=target["post_data"], headers=target["headers"])
        
    if r.status_code == 200:
        prev_homes: list[hestia.Home] = []
        new_homes: list[hestia.Home] = []
        
        # Check retrieved homes against previously scraped homes (of the last 6 months)
        for home in hestia.query_db("SELECT address, city FROM hestia.homes WHERE date_added > now() - interval '180 day'"):
            prev_homes.append(hestia.Home(home["address"], home["city"]))
        for home in hestia.HomeResults(target["agency"], r):
            if home not in prev_homes:
                new_homes.append(home)

        # Write new homes to database
        for home in new_homes:
            hestia.query_db("INSERT INTO hestia.homes VALUES (%s, %s, %s, %s, %s, %s)",
                (home.url,
                home.address,
                home.city,
                home.price,
                home.agency,
                datetime.now().isoformat()))

        await broadcast(new_homes)
    else:
        raise ConnectionError(f"Got a non-OK status code: {r.status_code}")
    

if __name__ == '__main__':
    run(main())

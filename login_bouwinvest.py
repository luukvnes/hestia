import requests
import re
import json
import urllib.parse
import time
def sign_in(session: requests.Session, username: str, password: str):
    # Disable redirects to see what's happening
    # First step: Initial login page request
    response = session.get("https://www.wonenbijbouwinvest.nl/login", headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-NL,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    })

    # The login form is likely at the final URL
    login_url = response.url

    # Extract CSRF token from the HTML itself if it exists
    csrf_token = None
    token_match = re.search(r'name="__RequestVerificationToken".*?value="([^"]+)"', response.text, re.DOTALL)
    if token_match:
        csrf_token = token_match.group(1)
        print(f"Found CSRF token in HTML: {csrf_token[:10]}...")
    else:
        # Try to get it from cookies as a fallback
        try:
            csrf_token = response.cookies.get("__RequestVerificationToken") or response.cookies.get(list(response.cookies.get_dict().keys())[0])
            print(f"Using CSRF token from cookies: {csrf_token[:10]}...")
        except:
            print("No CSRF token found!")

    # Extract return URL if it exists in the URL or form
    return_url = None
    url_match = re.search(r'returnUrl=([^&"]+)', response.url)
    if url_match:
        return_url = urllib.parse.unquote(url_match.group(1))
        print(f"Found return URL in URL: {return_url[:30]}...")
    else:
        # Try to extract from form
        form_match = re.search(r'name="returnUrl".*?value="([^"]+)"', response.text, re.DOTALL)
        if form_match:
            return_url = urllib.parse.unquote(form_match.group(1))
        else:
            try:
                # Try your original method as a fallback
                return_url = urllib.parse.unquote(response.history[-1].headers.get("Location", "")).split('returnUrl=')[1]
            except:
                print("No return URL found!")

    # Define the login payload with correct form field names
    payload = {
        "InputModel.ReturnUrl": return_url,
        "InputModel.Username": username,
        "InputModel.Password": password,
    }

    # Add CSRF token if found
    if csrf_token:
        payload["__RequestVerificationToken"] = csrf_token

    print(f"\nSending login request to: {login_url}")
    print(f"Payload keys: {list(payload.keys())}")

    # Add proper headers for a form submission
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-NL,en;q=0.9",
        "Origin": login_url.split('/login')[0],
        "Referer": login_url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Upgrade-Insecure-Requests": "1"
    }

    response_2 = session.post(login_url, data=payload, headers=headers, allow_redirects=True)

    response_25 = session.get("https://www.wonenbijbouwinvest.nl/js/recaptcha.js?id=keepMePosted", headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-NL,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"    
    })

def add_house(session: requests.Session, house_id: int):
    # Add the house to the favorites list
    response_3 = session.get(f"https://www.wonenbijbouwinvest.nl/api/project-property/{house_id}", headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-NL,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    })


    response_4 = session.get(f"https://www.wonenbijbouwinvest.nl/voorkeuren/{house_id}/toevoegen", headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-NL,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    })

def save_preferences(session: requests.Session):
    response_5 = session.get(f"https://www.wonenbijbouwinvest.nl/voorkeuren/opslaan", headers={
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-NL,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    })
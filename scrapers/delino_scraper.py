# scrapers/delino_scraper.py
import json
import re
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
import time

def scrape(url: str) -> dict:
    """
    Scrapes a Delino-based URL. It tries a direct config.json fetch first,
    and falls back to browser-based HTML parsing if the first method fails.
    """
    print(f"  -> Scraping Delino URL: {url}")
    
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    scheme = parsed_url.scheme
    record = {"url": url, "id": None, "hostname": hostname, "api_data": None}
    restaurant_uuid = None

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Referer": url
    })

    # --- Method 1: Try fetching config.json directly ---
    try:
        print("     Attempting Method 1: Direct config.json fetch...")
        config_url = f"{scheme}://{hostname}/config.json?{int(time.time() * 1000)}"
        response = session.get(config_url, timeout=10)
        response.raise_for_status()
        config_data = response.json()
        restaurant_uuid = config_data.get("delinoBaseId")
        if not restaurant_uuid:
            raise ValueError("'delinoBaseId' not in config.json")
        print(f"     Method 1 SUCCESS. Found UUID via config.json: {restaurant_uuid}")

    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
        print(f"     Method 1 FAILED ({e}). Trying Method 2: Browser-based HTML parsing...")
        
        # --- Method 2: Fallback to using Playwright ---
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            html_content = page.content()
            browser.close()

            match = re.search(r"window\.restaurantData\s*=\s*({.*?});", html_content)
            if not match:
                raise ValueError("Could not find 'window.restaurantData' data block on the page.")
            
            data_str = match.group(1)
            data = json.loads(data_str)
            restaurant_uuid = data.get("id")
            print(f"     Method 2 SUCCESS. Found UUID via HTML parsing: {restaurant_uuid}")

    if not restaurant_uuid:
        raise ValueError("Failed to find restaurant UUID using all available methods.")

    record["id"] = restaurant_uuid

    # --- Final API calls for profile and menu data ---
    profile_api_url = f"https://restaurant.delino.com/restaurant/data/{restaurant_uuid}"
    menu_api_url = f"https://restaurant.delino.com/restaurant/menu/{restaurant_uuid}"
    
    print("     Getting profile data...")
    profile_response = session.get(profile_api_url, timeout=20)
    profile_response.raise_for_status()
    profile_data = profile_response.json()
    
    print("     Getting menu data...")
    menu_response = session.get(menu_api_url, timeout=20)
    menu_response.raise_for_status()
    menu_data = menu_response.json()

    record["api_data"] = {"profile": profile_data, "menu": menu_data}
    
    return record
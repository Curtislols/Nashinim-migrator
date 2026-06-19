import json
import re
import requests
import time
from urllib.parse import urlparse
# ❗️THIS LINE MUST BE CHANGED❗️
from scrapers.scraper_helpers import get_browser_page # Was: from .shared...


def scrape(url: str) -> dict:
    """
    Scrapes a Delino-based URL. Tries a direct config.json fetch first,
    and falls back to browser-based HTML parsing if the first method fails.
    """
    print(f"  -> Scraping Delino URL: {url}")
    
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    record = {"url": url, "id": None, "hostname": hostname, "api_data": None}
    restaurant_uuid = None

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": url})

    try:
        print("     Attempting Method 1: Direct config.json fetch...")
        config_url = f"{parsed_url.scheme}://{hostname}/config.json?{int(time.time() * 1000)}"
        response = session.get(config_url, timeout=10)
        response.raise_for_status()
        restaurant_uuid = response.json().get("delinoBaseId")
        if not restaurant_uuid: raise ValueError("'delinoBaseId' not in config.json")
        print(f"     Method 1 SUCCESS. Found UUID: {restaurant_uuid}")

    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
        print(f"     Method 1 FAILED ({e}). Trying Method 2: Browser-based parsing...")
        with get_browser_page() as page:
            page.goto(url, wait_until="domcontentloaded")
            html_content = page.content()
            match = re.search(r"window.restaurantData\s*=\s*({.*?});", html_content)
            if not match: raise ValueError("Could not find 'window.restaurantData' on the page.")
            restaurant_uuid = json.loads(match.group(1)).get("id")
            print(f"     Method 2 SUCCESS. Found UUID: {restaurant_uuid}")

    if not restaurant_uuid:
        raise ValueError("Failed to find restaurant UUID using all methods.")

    record["id"] = restaurant_uuid
    profile_api_url = f"https://restaurant.delino.com/restaurant/data/{restaurant_uuid}"
    menu_api_url = f"https://restaurant.delino.com/restaurant/menu/{restaurant_uuid}"
    
    profile_data = session.get(profile_api_url, timeout=20).json()
    menu_data = session.get(menu_api_url, timeout=20).json()

    record["api_data"] = {"profile": profile_data, "menu": menu_data}
    return record
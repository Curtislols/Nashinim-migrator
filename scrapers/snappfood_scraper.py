# scrapers/snappfood_scraper.py
import json
import requests
import re
from urllib.parse import urlparse

def scrape(url: str) -> dict:
    """
    Scrapes a Snappfood URL by extracting the vendor code and making
    direct API calls for both menu and vendor details.
    """
    print(f"  -> Scraping Snappfood URL: {url}")
    
    # Use a regex to extract the vendor code from the URL
    # e.g., '.../رستوران_نوبهار-r-nn5ln8/' -> 'nn5ln8'
    match = re.search(r'-r-([a-zA-Z0-9]+)', url)
    if not match:
        raise ValueError("Could not find vendor code in the URL.")
    
    vendor_code = match.group(1)
    print(f"     Found vendor code: {vendor_code}")
    
    record = {"url": url, "id": vendor_code, "hostname": urlparse(url).netloc, "api_data": None}
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": url})

    # Snappfood APIs require a lat/long, we can use a generic Tehran location
    api_params = {
        "lat": "35.774",
        "long": "51.418",
        "optionalClient": "PWA",
        "client": "PWA",
        "deviceType": "PWA",
        "appVersion": "6.0.0",
        "UDID": "d93f82f4-5125-49e7-b17b-c58838fa719a", # A static UDID
        "Bonyan": "true"
    }

    # --- Step 1: Get Vendor Details ---
    profile_api_url = f"https://apigw.snappfood.ir/menu-read-model/vendor-details/{vendor_code}"
    print("     Getting vendor details...")
    profile_response = session.get(profile_api_url, params=api_params, timeout=20)
    profile_response.raise_for_status()
    profile_data = profile_response.json().get('data', {})

    # --- Step 2: Get Menu Data ---
    menu_api_url = f"https://apigw.snappfood.ir/menu-read-model/{vendor_code}"
    print("     Getting menu data...")
    menu_response = session.get(menu_api_url, params=api_params, timeout=20)
    menu_response.raise_for_status()
    menu_data = menu_response.json().get('data', {})

    record["api_data"] = {
        "profile": profile_data,
        "menu": menu_data
    }
    
    return record
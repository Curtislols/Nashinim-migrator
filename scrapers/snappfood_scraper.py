# scrapers/snappfood_scraper.py
import httpx
import re
from urllib.parse import urlparse
from .scraper_helpers import sanitize_url # <-- Import our new function

async def scrape(url: str) -> dict:
    """
    Scrapes a Snappfood URL using async API calls. Includes URL sanitization
    and robust error handling.
    """
    # --- THIS IS THE FIX ---
    # Sanitize the URL as the very first step. All subsequent logging and
    # error messages will use this safe, ASCII-only version.
    safe_url = sanitize_url(url)
    print(f"  -> Scraping Snappfood URL: {safe_url}")
    # --- END OF FIX ---

    match = re.search(r'-r-([a-zA-Z0-9]+)', url)
    if not match:
        raise ValueError("Could not find vendor code in the URL.")
    
    vendor_code = match.group(1)
    print(f"     Found vendor code: {vendor_code}")
    
    record = {"url": url, "id": vendor_code, "hostname": urlparse(url).netloc, "api_data": None}
    
    api_params = { "lat": "35.774", "long": "51.418", "client": "PWA" }
    headers = {"User-Agent": "Mozilla/5.0", "Referer": safe_url}

    profile_api_url = f"https://apigw.snappfood.ir/menu-read-model/vendor-details/{vendor_code}"
    menu_api_url = f"https://apigw.snappfood.ir/menu-read-model/{vendor_code}"

    try:
        async with httpx.AsyncClient() as client:
            print("     Getting vendor details...")
            # httpx is smart enough to work with the sanitized URL
            profile_response = await client.get(profile_api_url, params=api_params, headers=headers, timeout=20)
            profile_response.raise_for_status()

            print("     Getting menu data...")
            menu_response = await client.get(menu_api_url, params=api_params, headers=headers, timeout=20)
            menu_response.raise_for_status()

            profile_data = profile_response.json().get('data', {})
            menu_data = menu_response.json().get('data', {})

    except httpx.RequestError as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else "N/A"
        raise ValueError(f"Snappfood API request failed with status code: {status_code}")

    record["api_data"] = {"profile": profile_data, "menu": menu_data}
    return record
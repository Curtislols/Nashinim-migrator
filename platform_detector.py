# platform_detector.py
import requests
from urllib.parse import urlparse
from scrapers.scraper_helpers import get_browser_page

PLATFORM_DOMAINS = {
    "menew": "menew.ir",
    "qbar": "qbar.ir",
    "qrmenusaz": "qrmenusaz.com",
    "menusaz": "menusaz.com",
    "snappfood": "snappfood.ir",
    "menudigital": "menudigital.ir",
}

# --- UPDATED FINGERPRINTS ---
# We now check for the more reliable footer credit first for HidigiMenu.
HTML_FINGERPRINTS = {
    "delino": ["delinoBaseId", "window.restaurantData"],
    "hidigimenu": ["HiDigiMenu.Com", "collectionCode="],
}

def detect_platform(url: str) -> str | None:
    """
    Detects a website's platform by checking the URL and page content for fingerprints.
    """
    print(f"  -> Detecting platform for {url}...")
    
    hostname = urlparse(url).hostname
    
    # Method 1: Check for known domains in the URL
    for platform_name, domain_clue in PLATFORM_DOMAINS.items():
        if domain_clue in hostname:
            print(f"     Platform detected: {platform_name} (via URL)")
            return platform_name
            
    # Method 2: Check for Delino's unique config.json file
    try:
        config_url = f"{urlparse(url).scheme}://{hostname}/config.json"
        res = requests.get(config_url, timeout=7)
        if res.ok and "delinoBaseId" in res.text:
            print("     Platform detected: delino (via config.json)")
            return "delino"
    except requests.exceptions.RequestException:
        pass

    # Method 3: As a fallback, load in a browser and check the HTML
    try:
        with get_browser_page() as page:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            content = page.content()

        for platform_name, clues in HTML_FINGERPRINTS.items():
            if any(clue in content for clue in clues):
                print(f"     Platform detected: {platform_name} (via HTML content)")
                return platform_name
                
    except Exception as e:
        print(f"     Could not analyze page with browser to detect platform: {e}")

    return None
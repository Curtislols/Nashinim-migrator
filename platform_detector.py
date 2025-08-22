# platform_detector.py
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
import time

# --- This dictionary maps the platform's short name to a unique URL clue ---
PLATFORM_DOMAINS = {
    "menew": "menew.ir",
    "qbar": "qbar.ir",
    "menusaz": "menusaz.com",
    "qrmenusaz": "qrmenusaz.com",
    "snappfood": "snappfood.ir",
    "menudigital": "menudigital.ir", # <-- ADDED THIS
}

# --- This dictionary defines clues found in the page's HTML content ---
HTML_FINGERPRINTS = {
    "delino": ["delinoBaseId", "window.restaurantData"],
    "hidigimenu": ["collectionCode="],
}

def detect_platform(url: str) -> str | None:
    """
    Detects a website's platform by checking the URL and page content for fingerprints.
    """
    print(f"  -> Detecting platform for {url}...")
    
    hostname = urlparse(url).hostname
    
    # --- Method 1: Check for known domains in the URL ---
    for platform_name, domain_clue in PLATFORM_DOMAINS.items():
        if domain_clue in hostname:
            print(f"     Platform detected: {platform_name} (via URL)")
            return platform_name
            
    # --- Method 2: Check for Delino's unique config.json file ---
    try:
        config_url = f"{urlparse(url).scheme}://{hostname}/config.json"
        res = requests.get(config_url, timeout=7)
        if res.ok and "delinoBaseId" in res.text:
            print("     Platform detected: delino (via config.json)")
            return "delino"
    except requests.exceptions.RequestException:
        pass

    # --- Method 3: As a fallback, load in a browser and check the HTML ---
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            content = page.content()
            browser.close()

        # Scan the real HTML for our fingerprints
        for platform_name, clues in HTML_FINGERPRINTS.items():
            if any(clue in content for clue in clues):
                print(f"     Platform detected: {platform_name} (via HTML content)")
                return platform_name
                
    except Exception as e:
        print(f"     Could not analyze page with browser to detect platform: {e}")

    return None
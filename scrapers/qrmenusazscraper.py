# scrapers/qrmenusazscraper.py
import json
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def scrape(url: str) -> dict:
    """Scrapes a single QRmenusaz URL automatically and returns the data."""
    print(f"  -> Scraping QRMenusaz URL: {url}")
    api_path_keyword = "/Script/get_categories_items.php"
    button_selector = ".m6_main_cat"
    record = {"url": url, "hostname": urlparse(url).netloc, "api_data": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(url, wait_until="networkidle")

        menu_button = page.locator(button_selector).first
        if not menu_button.is_visible():
            raise ValueError(f"No visible button found with selector '{button_selector}'")
        
        print(f"     Found and clicking button: '{menu_button.locator('span').inner_text().strip()}'")
        
        with page.expect_response(f"**{api_path_keyword}") as response_info:
            menu_button.click()
        
        response = response_info.value
        if not response.ok:
            raise ValueError(f"API responded with status {response.status}")
        
        record["api_data"] = response.json()
        browser.close()
        
    return record
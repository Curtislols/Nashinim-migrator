# scrapers/qbarscraper.py
import json
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def scrape(url: str) -> dict:
    """
    Scrapes a QBar URL. Uses Playwright for initial navigation to handle
    potential landing pages, then uses direct API calls for data extraction.
    """
    print(f"  -> Scraping QBar URL: {url}")
    
    final_menu_url = ""

    # --- STAGE 1: Use Playwright for Navigation ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("     Navigating to handle intro pages...")
        page.goto(url, wait_until="domcontentloaded")
        
        # Add checks for entry/branch buttons if they exist on QBar sites
        # For now, we assume it lands on the menu, but this is where you'd add clicks.
        # Example check:
        # if page.locator("#some-entry-button").is_visible():
        #     page.locator("#some-entry-button").click()
        #     page.wait_for_load_state("domcontentloaded")

        final_menu_url = page.url # Get the URL after any navigation
        print(f"     On final menu page: {final_menu_url}")
        browser.close()

    # --- STAGE 2: Use direct API calls with the final URL ---
    restaurant_api_url = "https://api.qbar.ir/v1/res/restaurant-title/{slug}/"
    category_api_url = "https://api.qbar.ir/v1/res/foodcategory/?restaurant__url_title={slug}&sf_active=true"
    items_api_url = "https://api.qbar.ir/v1/res/food/?restaurant={rest_id}&category={cat_id}"
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    path_parts = urlparse(final_menu_url).path.strip('/').split('/')
    slug = path_parts[0]
    
    record = {"url": url, "slug": slug, "api_data": None}
    
    print(f"     Extracting slug: '{slug}'")
    res_info_url = restaurant_api_url.format(slug=slug)
    response = session.get(res_info_url, timeout=20)
    response.raise_for_status()
    restaurant_data = response.json()
    restaurant_id = restaurant_data.get("id")
    
    if not restaurant_id: raise ValueError("Restaurant ID not found.")

    cat_list_url = category_api_url.format(slug=slug)
    response = session.get(cat_list_url, timeout=20)
    response.raise_for_status()
    categories = response.json().get("results", [])
    
    for category in categories:
        category_id = category.get("id")
        if not category_id: continue
        items_url = items_api_url.format(rest_id=restaurant_id, cat_id=category_id)
        response = session.get(items_url, timeout=20)
        category["products"] = response.json().get("results", [])
    
    restaurant_data["menu_with_products"] = categories
    record["api_data"] = restaurant_data
    
    return record
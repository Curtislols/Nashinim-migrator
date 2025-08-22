import json
import re
import requests
import time
from urllib.parse import urlparse
# ❗️THIS LINE MUST BE CHANGED❗️
from scrapers.shared.scraper_helpers import get_browser_page # Was: from .shared...


def scrape(url: str) -> dict:
    """
    Scrapes a QBar URL. Uses Playwright for initial navigation, then uses
    direct API calls for data extraction.
    """
    print(f"  -> Scraping QBar URL: {url}")
    
    with get_browser_page() as page:
        print("     Navigating to handle intro pages...")
        page.goto(url, wait_until="domcontentloaded")
        final_menu_url = page.url
        print(f"     On final menu page: {final_menu_url}")

    restaurant_api_url = "https://api.qbar.ir/v1/res/restaurant-title/{slug}/"
    items_api_url = "https://api.qbar.ir/v1/res/food/?restaurant__url_title={slug}&sf_active=true"
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    slug = urlparse(final_menu_url).path.strip('/').split('/')[0]
    record = {"url": url, "slug": slug, "api_data": None}
    
    print(f"     Extracting slug: '{slug}'")
    res_info_url = restaurant_api_url.format(slug=slug)
    response = session.get(res_info_url, timeout=20)
    response.raise_for_status()
    restaurant_data = response.json()
    
    items_list_url = items_api_url.format(slug=slug)
    response = session.get(items_list_url, timeout=20)
    response.raise_for_status()
    
    # QBar API returns items and categories mixed, so we need to rebuild the structure
    items_by_category = {}
    for item in response.json().get("results", []):
        category = item.get("category")
        if not category: continue
        cat_id = category.get("id")
        if cat_id not in items_by_category:
            items_by_category[cat_id] = {
                "id": cat_id,
                "title": category.get("title"),
                "sf_active": category.get("sf_active", True),
                "products": []
            }
        items_by_category[cat_id]["products"].append(item)

    restaurant_data["menu_with_products"] = list(items_by_category.values())
    record["api_data"] = restaurant_data
    
    return record
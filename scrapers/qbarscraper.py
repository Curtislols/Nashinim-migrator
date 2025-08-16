# scrapers/qbarscraper.py
import json
import requests
from urllib.parse import urlparse

def scrape(url: str) -> dict:
    """Scrapes a single QBar URL using its direct API and returns the data."""
    print(f"  -> Scraping QBar URL: {url}")
    
    restaurant_api_url = "https://api.qbar.ir/v1/res/restaurant-title/{slug}/"
    category_api_url = "https://api.qbar.ir/v1/res/foodcategory/?restaurant__url_title={slug}&sf_active=true"
    items_api_url = "https://api.qbar.ir/v1/res/food/?restaurant={rest_id}&category={cat_id}"
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # --- THIS IS THE FIX ---
    # The slug is the FIRST part of the path (index 0), not the second.
    path_parts = urlparse(url).path.strip('/').split('/')
    slug = path_parts[0]
    
    record = {"url": url, "slug": slug, "api_data": None}
    
    # Step 1: Get Restaurant Info and ID
    print(f"     Extracting slug: '{slug}'")
    res_info_url = restaurant_api_url.format(slug=slug)
    response = session.get(res_info_url, timeout=20)
    response.raise_for_status()
    restaurant_data = response.json()
    restaurant_id = restaurant_data.get("id")
    
    if not restaurant_id:
        raise ValueError("Restaurant ID not found.")

    # Step 2: Get Food Categories
    cat_list_url = category_api_url.format(slug=slug)
    response = session.get(cat_list_url, timeout=20)
    response.raise_for_status()
    categories = response.json().get("results", [])
    
    # Step 3: Get Items for Each Category
    for category in categories:
        category_id = category.get("id")
        if not category_id:
            continue
        items_url = items_api_url.format(rest_id=restaurant_id, cat_id=category_id)
        response = session.get(items_url, timeout=20)
        category["products"] = response.json().get("results", [])
    
    restaurant_data["menu_with_products"] = categories
    record["api_data"] = restaurant_data
    
    return record
import json
import re
import requests
import time
from urllib.parse import urlparse
# ❗️THIS LINE MUST BE CHANGED❗️
from scrapers.scraper_helpers import get_browser_page # Was: from .shared...


def scrape(url: str) -> dict:
    """
    Scrapes a MeNew URL, handling multi-step landing pages with the
    shared user prompt helper.
    """
    print(f"  -> Scraping MeNew URL: {url}")
    api_endpoint = "https://citadel.menew.ir/api"
    headers = {"Content-Type": "application/json"}
    record = {"url": url, "id": None, "hostname": urlparse(url).netloc, "api_data": None}
    found = {"id": None}

    with get_browser_page() as page:
        print("     Navigating to page...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        enter_button = page.locator('button:has-text("ورود")').first
        if enter_button.is_visible():
            print("     Entry page detected. Clicking 'Enter'...")
            enter_button.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
        
        prompt_user_for_choice(
            page,
            selector='div[class*="styles_container__"] a',
            prompt_message="Branch selection page detected. Please choose one:"
        )
        
        print("     On final menu page. Looking for API data...")
        def handle_request(request):
            if "citadel.menew.ir/api" in request.url and request.post_data and '"operationName":"getEntityItems"' in request.post_data:
                try:
                    payload = json.loads(request.post_data)
                    found["id"] = payload.get("variables", {}).get("id")
                except Exception: pass
        
        page.on("request", handle_request)
        page.reload(wait_until="networkidle")
        page.remove_listener("request", handle_request)
        
        record["id"] = found["id"]
        
    if record["id"]:
        payload = {
            "query": """query getEntityItems($id: UUID!, $flavour: QueryFlavour = VILLAGE) {
              entity(id: $id, flavour: $flavour) {
                menus { id label categories { id label items {
                  id name description thumbnail
                  shopItem { id isSoldOut shopItemPrice { price } }
                }}}
              }}""",
            "variables": {"id": record["id"], "flavour": "VILLAGE"},
            "operationName": "getEntityItems",
        }
        r = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        record["api_data"] = r.json()
    else:
        raise ValueError("Could not find the menu ID after navigating to the page.")

    return record
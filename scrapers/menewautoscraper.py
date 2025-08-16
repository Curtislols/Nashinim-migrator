# scrapers/menewautoscraper.py
from playwright.sync_api import sync_playwright
import json
import requests
from urllib.parse import urlparse

def scrape(url: str) -> dict:
    """Scrapes a single MeNew URL and returns the data as a dictionary."""
    print(f"  -> Scraping MeNew URL: {url}")
    api_endpoint = "https://citadel.menew.ir/api"
    headers = {"Content-Type": "application/json"}
    record = {"url": url, "id": None, "hostname": urlparse(url).netloc, "api_data": None}
    found = {"id": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_request(request):
            if "citadel.menew.ir/api" in request.url:
                if request.post_data and '"operationName":"getEntityItems"' in request.post_data:
                    try:
                        payload = json.loads(request.post_data)
                        found["id"] = payload.get("variables", {}).get("id")
                    except Exception:
                        pass
        
        page.on("request", handle_request)
        page.goto(url, wait_until="networkidle")
        page.remove_listener("request", handle_request)
        
        record["id"] = found["id"]
        
        if found["id"]:
            payload = {
                "query": """
                query getEntityItems($id: UUID!, $language: String, $flavour: QueryFlavour = VILLAGE) {
                  entity(id: $id, language: $language, flavour: $flavour) {
                    menus {
                      id label slug description isActive
                      categories {
                        id label thumbnail status
                        items {
                          id name thumbnail description
                          shopItem {
                            id isSoldOut
                            shopItemPrice { originalPrice price }
                          }
                        }
                      }
                    }
                  }
                }""",
                "variables": {"id": found["id"], "flavour": "VILLAGE"},
                "operationName": "getEntityItems",
            }
            try:
                r = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
                record["api_data"] = r.json()
            except Exception as e:
                record["api_data"] = {"error": str(e)}
        
        browser.close()

    return record
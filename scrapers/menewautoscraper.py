# scrapers/menewautoscraper.py
from playwright.sync_api import sync_playwright
import json
import requests
from urllib.parse import urlparse

def scrape(url: str) -> dict:
    """
    Scrapes a single MeNew URL. It can now handle multi-step landing pages
    (language/entry -> branch selection) by asking for user input.
    """
    print(f"  -> Scraping MeNew URL: {url}")
    api_endpoint = "https://citadel.menew.ir/api"
    headers = {"Content-Type": "application/json"}
    record = {"url": url, "id": None, "hostname": urlparse(url).netloc, "api_data": None}
    found = {"id": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # --- STAGE 1: Navigate and handle entry/branch pages ---
        print("     Navigating to page...")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000) # Wait for animations

        # Check for the main "Enter" (ورود) button
        enter_button = page.locator('button:has-text("ورود")').first
        if enter_button.is_visible():
            print("     Entry page detected. Clicking 'Enter'...")
            enter_button.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)
        
        # Check for branch selection page
        # These are links inside a div with class 'styles_container__...'
        branch_links = page.locator('div[class*="styles_container__"] a').all()
        if branch_links:
            print("\n     Branch selection page detected. Please choose one:")
            for i, branch in enumerate(branch_links, start=1):
                print(f"       [{i}] {branch.text_content().strip()}")
            
            while True:
                try:
                    user_choice_idx = int(input("\n     Enter the number of your choice: ")) - 1
                    if 0 <= user_choice_idx < len(branch_links):
                        chosen_branch = branch_links[user_choice_idx]
                        break
                    else:
                        print("     Invalid number.")
                except ValueError:
                    print("     Invalid input.")

            print(f"     You chose: '{chosen_branch.text_content().strip()}'. Navigating to branch menu...")
            chosen_branch.click()
            page.wait_for_load_state("networkidle")
        
        # --- STAGE 2: Capture the menu API data ---
        print("     On final menu page. Looking for API data...")
        def handle_request(request):
            if "citadel.menew.ir/api" in request.url:
                if request.post_data and '"operationName":"getEntityItems"' in request.post_data:
                    try:
                        payload = json.loads(request.post_data)
                        found["id"] = payload.get("variables", {}).get("id")
                    except Exception: pass
        
        page.on("request", handle_request)
        # Reload the page if needed to ensure we capture the request
        page.reload(wait_until="networkidle")
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
        else:
             raise ValueError("Could not find the menu ID after navigating to the page.")
        
        browser.close()

    return record
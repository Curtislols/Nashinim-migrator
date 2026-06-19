# scrapers/menew_scraper.py
from playwright.sync_api import sync_playwright
import json
import requests
from urllib.parse import urlparse

def get_menu_choices(url: str) -> list:
    """
    Navigates to a MeNew URL, handles any entry pages, and returns a list
    of available branch choices. If no choices are found, it returns an empty list.
    """
    print("  -> Discovering choices for MeNew...")
    branch_selector = 'div[class*="styles_container__"] a'
    choices = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            enter_button = page.locator('button:has-text("ورود")').first
            if enter_button.is_visible(timeout=5000):
                print("     Entry page detected. Clicking 'Enter'...")
                enter_button.click()
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
            
            if page.locator(branch_selector).first.is_visible(timeout=5000):
                print("     Branch selection page found. Getting choices...")
                buttons = page.locator(branch_selector).all()
                for i, button in enumerate(buttons):
                    text = button.text_content()
                    choices.append({"id": i, "name": text.strip()})
            else:
                print("     No branch selection page found. Proceeding directly.")
        except Exception as e:
            print(f"     Could not find branch choices, proceeding directly. Reason: {e}")
        finally:
            browser.close()
    
    return choices


def scrape(url: str, choice_id: int = 0) -> dict:
    """
    Scrapes a MeNew URL. If branch choices exist, it clicks the chosen one.
    """
    print(f"  -> Scraping MeNew URL with choice ID: {choice_id}")
    
    # --- ❗️ THIS LINE WAS MISSING IN MY PREVIOUS RESPONSE ❗️ ---
    record = {"url": url, "id": None, "hostname": urlparse(url).netloc, "api_data": None}
    
    api_endpoint = "https://citadel.menew.ir/api"
    headers = {"Content-Type": "application/json"}
    found = {"id": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            enter_button = page.locator('button:has-text("ورود")').first
            if enter_button.is_visible(timeout=5000):
                enter_button.click()
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
            
            branch_selector = 'div[class*="styles_container__"] a'
            if page.locator(branch_selector).first.is_visible(timeout=5000):
                branch_links = page.locator(branch_selector).all()
                if not branch_links or choice_id >= len(branch_links):
                    raise ValueError(f"Invalid choice_id '{choice_id}'. Only {len(branch_links)} options found.")
                
                chosen_branch = branch_links[choice_id]
                print(f"     Clicking chosen branch: '{chosen_branch.text_content().strip()}'")
                chosen_branch.click()
                page.wait_for_load_state("networkidle", timeout=20000)
            else:
                print("     No branch selection needed. Capturing data from current page.")
            
            def handle_request(request):
                if "citadel.menew.ir/api" in request.url and '"operationName":"getEntityItems"' in request.post_data:
                    try:
                        found["id"] = json.loads(request.post_data).get("variables", {}).get("id")
                    except Exception: pass
            
            page.on("request", handle_request)
            page.reload(wait_until="networkidle", timeout=20000)
            page.remove_listener("request", handle_request)

            if not found["id"]:
                raise ValueError("Could not find the menu ID after navigating to the page.")
            
            record["id"] = found["id"]
        finally:
            browser.close()
    
    payload = {
        "query": "query getEntityItems($id: UUID!, $flavour: QueryFlavour = VILLAGE) { entity(id: $id, flavour: $flavour) { menus { id label categories { id label items { id name description thumbnail shopItem { id isSoldOut shopItemPrice { price } } } } } } }",
        "variables": {"id": record["id"], "flavour": "VILLAGE"},
        "operationName": "getEntityItems",
    }
    r = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    record["api_data"] = r.json()

    return record
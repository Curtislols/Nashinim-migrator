# scrapers/menusaz_scraper.py
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright # <-- Reverted to sync_api

# This is now a regular 'def' function
def get_menu_choices(url: str) -> list:
    print(f"  -> Discovering choices for: {url}")
    button_selector = ".t9_category"
    choices = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print("     Scanning for menu options...")
            page.wait_for_selector(button_selector, state="visible", timeout=7000)
            
            buttons = page.locator(button_selector).all()
            for i, button in enumerate(buttons):
                text = button.text_content()
                choices.append({"id": i, "name": text.strip()})
        finally:
            browser.close()
            
    return choices

# This is also a regular 'def' function now
def scrape(url: str, choice_id: int = 0) -> dict:
    print(f"  -> Scraping Menusaz URL: {url} with choice ID: {choice_id}")
    api_path_keyword = "/Script/get_categories_items.php"
    button_selector = ".t9_category"
    record = {"url": url, "hostname": urlparse(url).netloc, "api_data": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            buttons = page.locator(button_selector).all()
            if not buttons or choice_id >= len(buttons):
                raise ValueError(f"Invalid choice_id '{choice_id}'. Only {len(buttons)} options found.")

            chosen_button = buttons[choice_id]
            button_text = chosen_button.text_content()
            print(f"     Found and clicking chosen option: '{button_text.strip()}'")

            with page.expect_response(lambda res: api_path_keyword in res.url) as response_info:
                chosen_button.click()
            
            response = response_info.value
            if not response.ok:
                raise ValueError(f"API responded with status {response.status}")
            
            record["api_data"] = response.json()
        finally:
            browser.close()
            
    return record
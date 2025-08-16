# scrapers/menusazscraper.py
import json
import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def scrape(url: str) -> dict:
    """
    Interactively scrapes a single Menusaz URL by simulating a user click
    on a chosen menu and capturing the resulting API call.
    """
    print(f"  -> Scraping Menusaz URL: {url}")
    api_path_keyword = "/Script/get_categories_items.php"
    button_selector = ".t9_category"
    record = {"url": url, "hostname": urlparse(url).netloc, "api_data": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # --- STAGE 1: Scan for Menu Options ---
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print("     Scanning for menu options...")
            page.wait_for_selector(button_selector, timeout=5000) # Wait for buttons to appear

            choices = page.locator(button_selector).all()
            if not choices:
                raise ValueError("No clickable menu options were found.")

            print("\n     Found the following options. Please choose one:")
            for i, choice in enumerate(choices, start=1):
                print(f"       [{i}] {choice.text_content().strip()}")
            
            # Get user's choice from the terminal
            while True:
                try:
                    user_choice_idx = int(input("\n     Enter the number of your choice: ")) - 1
                    if 0 <= user_choice_idx < len(choices):
                        chosen_button = choices[user_choice_idx]
                        break
                    else:
                        print("     Invalid number. Please try again.")
                except ValueError:
                    print("     Invalid input. Please enter a number.")
            
            print(f"     You chose: '{chosen_button.text_content().strip()}'")

            # --- STAGE 2: Click and Capture the Real Network Response ---
            print("     Clicking button and waiting for API data...")
            
            # Use page.expect_response to wait for the POST request triggered by the click
            with page.expect_response(lambda res: api_path_keyword in res.url and res.request.method == "POST") as response_info:
                chosen_button.click()
            
            response = response_info.value
            if not response.ok:
                raise ValueError(f"API responded with status {response.status}")
            
            record["api_data"] = response.json()
            
        finally:
            browser.close()

    return record
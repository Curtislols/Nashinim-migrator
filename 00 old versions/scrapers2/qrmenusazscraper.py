import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# The starting URL for the QRmenusaz platform
start_url = "http://volume.qrmenusaz.com/"

# The API path keyword to listen for
api_path_keyword = "/Script/get_categories_items.php"

# The CORRECT CSS selector for the menu buttons
button_selector = ".m6_main_cat"

# Directory to save results
out_dir = Path("out_qrmenusaz_final")
out_dir.mkdir(exist_ok=True)

print("🚀 Starting final scraper for QRmenusaz...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    try:
        # --- STAGE 1: Scan for Menu Options on the Main Page ---
        print(f"\nNavigating to {start_url}...")
        page.goto(start_url, wait_until="networkidle", timeout=30000)

        # Search for the buttons directly on the page
        print(f"Scanning for buttons with selector: '{button_selector}'...")
        choices = page.locator(button_selector).all()

        if not choices:
            raise ValueError("No clickable menu options were found.")

        print("\nFound the following options. Please choose one:")
        for i, choice in enumerate(choices, start=1):
            # The text is inside a <span> child element
            print(f"  [{i}] {choice.locator('span').inner_text().strip()}")
        
        # Get user's choice
        while True:
            try:
                user_choice_idx = int(input("\nEnter the number of your choice: ")) - 1
                if 0 <= user_choice_idx < len(choices):
                    chosen_button = choices[user_choice_idx]
                    break
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        print(f"\n✅ You chose: '{chosen_button.locator('span').inner_text().strip()}'")

        # --- STAGE 2: Click and Capture POST Response ---
        print("Clicking the button and waiting for the API response...")

        with page.expect_response(f"**{api_path_keyword}") as response_info:
            chosen_button.click()
        
        response = response_info.value
        print(f"API call successful! Status: {response.status}")

        if not response.ok:
            raise ValueError(f"API responded with status {response.status}")
        
        # --- Save the Data ---
        api_data = response.json()
        hostname = urlparse(start_url).netloc
        short_name = hostname.split('.')[0]
        filename = out_dir / f"{short_name}_menu.json"
        filename.write_text(json.dumps(api_data, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"\n🎉 Successfully captured and saved menu data to: {filename}")

    except Exception as e:
        print(f"  -> FAILED: {e}")
    finally:
        browser.close()
        print("\nProcess finished.")
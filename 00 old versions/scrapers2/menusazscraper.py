import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Add all the URLs you want to scrape here
urls_to_scrape = [
    "https://sowon.menusaz.com/",
    # Add other menusaz.com sites here
]

# The API path to listen for
api_path_keyword = "/Script/get_categories_items.php"

# The CSS selector for the menu buttons
button_selector = ".t9_category"

# Directory to save results
out_dir = Path("out_menusaz_final")
out_dir.mkdir(exist_ok=True)

print("🚀 Starting FINAL automated scraper...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for url in urls_to_scrape:
        try:
            hostname = urlparse(url).netloc
            print(f"\n--- Processing: {hostname} ---")
            
            # Navigate to the main page
            page.goto(url, wait_until="networkidle")

            # Find the first available menu button
            menu_button = page.locator(button_selector).first
            if not menu_button.is_visible():
                raise ValueError(f"No visible button found with selector '{button_selector}'")
            
            print(f"  -> Found menu button: '{menu_button.text_content().strip()}'")

            # Click the button and wait for the specific API response
            print("  -> Clicking button and waiting for API data...")
            with page.expect_response(f"**{api_path_keyword}") as response_info:
                menu_button.click()
            
            response = response_info.value
            if not response.ok:
                raise ValueError(f"API responded with status {response.status}")
            
            api_data = response.json()
            
            # Save the file
            short_name = hostname.split('.')[0]
            filename = out_dir / f"{short_name}_menu.json"
            filename.write_text(json.dumps(api_data, indent=2, ensure_ascii=False), encoding="utf-8")

            print(f"  ✅ Success! Data saved to: {filename}")

        except Exception as e:
            print(f"  ❌ FAILED to process {url}: {e}")
        
    browser.close()

print("\n🎉 All tasks finished.")
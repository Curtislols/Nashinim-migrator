import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# List of URLs
urls = [
    "https://sowon.menusaz.com/",
    "http://volume.qrmenusaz.com/", # This one will likely still fail due to a server error
]

# The API path we expect to be called after the click
api_path = "/Script/get_categories_items.php"

# A list of possible button texts to click on the landing page
# The script will try these in order.
BUTTON_SELECTORS = [
    'text="منوی فارسی"',
    'text="RESTAURANT"',
    'text="English Menu"',
    'text="한국어 메뉴"'
]

out_dir = Path("out_menusaz_final_click")
out_dir.mkdir(exist_ok=True)
results = []

print("Processing menus by simulating user clicks with Playwright...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for idx, url in enumerate(urls, start=1):
        record = {"url": url, "hostname": None, "api_data": None}
        
        try:
            # --- 1. Get hostname and base URL ---
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc
            base_url = f"{parsed_url.scheme}://{hostname}/"
            
            if not hostname:
                raise ValueError("Could not parse hostname.")

            record["hostname"] = hostname
            print(f"\n[{idx}/{len(urls)}] Processing '{hostname}'...")

            # --- 2. Navigate to the main landing page ---
            print(f"  -> Navigating to main page: {base_url}")
            page.goto(base_url, wait_until="networkidle", timeout=30000)

            # --- 3. Click the menu button and capture the API response ---
            print("  -> Waiting for API response after click...")
            
            # This tells Playwright: "Get ready to catch a response from the API"
            with page.expect_response(f"**{api_path}") as response_info:
                # Now, find a visible button from our list and click it
                clicked = False
                for selector in BUTTON_SELECTORS:
                    button = page.locator(selector).first
                    if button.is_visible():
                        print(f"     Found and clicking button: '{selector}'")
                        button.click()
                        clicked = True
                        break # Stop after finding the first valid button
                
                if not clicked:
                    raise ValueError("Could not find a valid menu button to click.")

            # --- 4. Get the JSON from the captured response ---
            response = response_info.value
            if not response.ok:
                 raise ValueError(f"API responded with status {response.status}")

            api_data = response.json()
            record["api_data"] = api_data

            # --- 5. Save the data ---
            short_name = hostname.split('.')[0]
            filename = out_dir / f"{idx:03d}_{short_name}.json"
            filename.write_text(json.dumps(api_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  -> Successfully captured and saved data to: {filename}")

        except Exception as e:
            print(f"  -> FAILED to process {url}: {e}")
            record["api_data"] = {"error": str(e)}

        results.append(record)

    browser.close()

# --- Save the combined results file ---
combined_file = out_dir / "menusaz_results_all_final_click.json"
combined_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n✅ All processing finished. Results saved to {combined_file}")
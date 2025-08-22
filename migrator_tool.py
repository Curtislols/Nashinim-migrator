import json
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse
import time

# --- Import your specialized functions from your folders ---
try:
    from scrapers import (
        qbarscraper, menusazscraper, qrmenusazscraper,
        menewautoscraper, delino_scraper, hidigimenu_scraper, snappfood_scraper, menudigital_scraper
    )
    from data_transformers import (
        qbar_transformer, menusaz_transformer, menew_transformer,
        qrmenusaz_transformer, delino_transformer, hidigimenu_transformer, snappfood_transformer,menudigital_transformer
    )
    from platform_detector import detect_platform
except ImportError as e:
    print(f"ERROR: Could not import a required module. Make sure all scraper and transformer files exist. Details: {e}")
    sys.exit(1)

print("✅ Migrator Tool script started...")

# --- ❗️ CONFIGURATION: YOU MUST EDIT THESE TWO VALUES ---
YOUR_API_ENDPOINT = "https://api.yoursite.com/v1/images"
YOUR_API_TOKEN = "your_secret_bearer_token_here"
# ---------------------------------------------------------

# --- Get the directory where this script itself is located ---
SCRIPT_DIR = Path(__file__).resolve().parent

# --- Create output directories relative to the script's location ---
RAW_DATA_DIR = SCRIPT_DIR / "output/raw_data"
TRANSFORMED_DATA_DIR = SCRIPT_DIR / "output/transformed_data"
FINAL_DATA_DIR = SCRIPT_DIR / "output/final_data"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
TRANSFORMED_DATA_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


# --- Platform to Module Mapping ---
PLATFORM_MAPPING = {
    "delino": {"scraper": delino_scraper.scrape, "transformer": delino_transformer.transform},
    "menew": {"scraper": menewautoscraper.scrape, "transformer": menew_transformer.transform},
    "menusaz": {"scraper": menusazscraper.scrape, "transformer": menusaz_transformer.transform},
    "qrmenusaz": {"scraper": qrmenusazscraper.scrape, "transformer": qrmenusaz_transformer.transform},
    "qbar": {"scraper": qbarscraper.scrape, "transformer": qbar_transformer.transform},
    "hidigimenu": {"scraper": hidigimenu_scraper.scrape, "transformer": hidigimenu_transformer.transform},
    "snappfood": {"scraper": snappfood_scraper.scrape, "transformer": snappfood_transformer.transform},
    "menudigital": {"scraper": menudigital_scraper.scrape, "transformer": menudigital_transformer.transform}, # <-- ADD THIS LINE
}
# --- IMAGE MIGRATION LOGIC (Integrated) ---
def migrate_image(image_url: str) -> str | None:
    if not image_url or not image_url.startswith('http'):
        print("     -> Skipping invalid or missing URL.")
        return None
    try:
        print(f"     -> Downloading: {image_url[:60]}...")
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()
        image_content = response.content

        headers = {"Authorization": f"Bearer {YOUR_API_TOKEN}"}
        files = {"image_file": ("image.jpg", image_content)}
        
        print("        ...Uploading to your system...")
        upload_response = requests.post(YOUR_API_ENDPOINT, headers=headers, files=files, timeout=30)
        upload_response.raise_for_status()
        
        new_url = upload_response.json().get("url")
        if not new_url:
            print("        ERROR: New URL not found in API response.")
            return None
        return new_url
    except Exception as e:
        print(f"        ERROR migrating image: {e}")
        return None

def migrate_images_for_menu(menu_data: dict):
    for category in menu_data.get("categories", []):
        print(f"  Scanning category for images: {category.get('name')}")
        for item in category.get("items", []):
            original_url = item.get("original_image_url")
            if original_url:
                print(f"    Processing image for: {item.get('name')}")
                new_image_url = migrate_image(original_url)
                item["image"] = new_image_url
            if "original_image_url" in item:
                del item["original_image_url"]
    return menu_data

# --- MAIN PIPELINE ---
def process_restaurant(url: str, should_migrate_images: bool):
    print(f"\n=============================================")
    print(f"STARTING PIPELINE FOR: {url}")
    print(f"=============================================")

    try:
        platform_name = detect_platform(url)
        if not platform_name:
            raise Exception(f"Could not identify the platform for {url}")
            
        scraper_func = PLATFORM_MAPPING[platform_name]["scraper"]
        transformer_func = PLATFORM_MAPPING[platform_name]["transformer"]

        # STAGE 1: SCRAPE
        raw_data = scraper_func(url)
        
        slug = (
            raw_data.get("slug")
            or raw_data.get("api_data", {}).get("profile", {}).get("domain")
            or raw_data.get("hostname", "data").split('.')[0]
        )
        
        raw_file_path = RAW_DATA_DIR / f"{platform_name}_{slug}_raw.json"
        with raw_file_path.open('w', encoding='utf-8') as f: json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 1 Complete: Raw data saved to {raw_file_path}")

        # STAGE 2: TRANSFORM
        transformed_data = transformer_func(raw_data)
        if not transformed_data: raise Exception("Transformation failed.")

        transformed_file_path = TRANSFORMED_DATA_DIR / f"{platform_name}_{slug}_transformed.json"
        with transformed_file_path.open('w', encoding='utf-8') as f: json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 2 Complete: Transformed menu saved to {transformed_file_path}")

        # STAGE 3: MIGRATE IMAGES
        if should_migrate_images:
            print("  -> Starting Stage 3: Image Migration...")
            final_data = migrate_images_for_menu(transformed_data)
            final_file_path = FINAL_DATA_DIR / f"{platform_name}_{slug}_complete.json"
            with final_file_path.open('w', encoding='utf-8') as f: json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"  -> Stage 3 Complete: Final data saved to {final_file_path}")
        else:
            print("  -> Stage 3 (Image Migration) was skipped. Use the --with-images flag to run it.")

    except Exception as e:
        print(f"  -> !!! PIPELINE FAILED for {url}: {e}")

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Error: No URLs provided.")
        print("✅ Usage: python migrator_tool.py <url1> <url2> ... [--with-images]")
        sys.exit(1)

    urls_to_process = [arg for arg in sys.argv[1:] if arg != "--with-images"]
    migrate_flag = "--with-images" in sys.argv

    if not urls_to_process:
        print("\n❌ Error: No URLs provided to process.")
        sys.exit(1)

    print(f"Found {len(urls_to_process)} URL(s) to process. Image migration is {'ENABLED' if migrate_flag else 'DISABLED'}.")

    for restaurant_url in urls_to_process:
        process_restaurant(restaurant_url, should_migrate_images=migrate_flag)

    print("\n\n🎉 All pipelines finished.")
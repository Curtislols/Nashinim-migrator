# migrator_tool.py
import json
import sys
from pathlib import Path

# --- Import your modules ---
from scrapers import qbarscraper, menusazscraper, qrmenusazscraper, menewautoscraper, delino_scraper, hidigimenu_scraper
from data_transformers import qbar_transformer, menusaz_transformer, menew_transformer, qrmenusaz_transformer, delino_transformer, hidigimenu_transformer
from platform_detector import detect_platform # <-- NEW, CLEAN IMPORT

print("✅ Migrator Tool script started...")

# --- ❗️ CONFIGURATION ---
YOUR_API_ENDPOINT = "https://api.yoursite.com/v1/images"
YOUR_API_TOKEN = "your_secret_bearer_token_here"
# -------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
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
}

# --- Image migration functions (unchanged) ---
# ... (Full, unchanged image migration functions go here) ...
def migrate_image(image_url: str) -> str | None: pass
def migrate_images_for_menu(menu_data: dict): pass

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
        slug = (raw_data.get("slug") or
                raw_data.get("api_data", {}).get("profile", {}).get("domain") or
                raw_data.get("hostname", "data").split('.')[0])
        
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
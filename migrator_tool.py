import json
import sys
from pathlib import Path

# --- Import your specialized functions from your folders ---
from scrapers import qbarscraper, menusazscraper, qrmenusazscraper, menewautoscraper
from data_transformers import qbar_transformer, menusaz_transformer, menew_transformer

# Note: This assumes you have a qrmenusaz_transformer.py file.
# If qrmenusaz and menusaz use the same logic, you can point both to menusaz_transformer.
from data_transformers import qrmenusaz_transformer


# --- Get the directory where this script itself is located ---
SCRIPT_DIR = Path(__file__).resolve().parent

# --- Create output directories relative to the script's location ---
RAW_DATA_DIR = SCRIPT_DIR / "output/raw_data"
TRANSFORMED_DATA_DIR = SCRIPT_DIR / "output/transformed_data"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
TRANSFORMED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def process_restaurant(url: str):
    """
    Runs the full scrape and transform pipeline for a single restaurant URL.
    """
    print(f"\n=============================================")
    print(f"STARTING PIPELINE FOR: {url}")
    print(f"=============================================")

    try:
        # --- STAGE 1: SCRAPE ---
        raw_data = None
        source_name = None
        slug = url.split('/')[-2] or url.split('/')[-1] # A simple way to get a name for filenames

        # Decide which scraper to use based on the URL
        if "qbar.ir" in url:
            source_name = "qbar"
            raw_data = qbarscraper.scrape(url)
        elif "qrmenusaz.com" in url:
            source_name = "qrmenusaz"
            raw_data = qrmenusazscraper.scrape(url)
            slug = raw_data.get("hostname", "").split('.')[0]
        elif "menusaz.com" in url:
            source_name = "menusaz"
            raw_data = menusazscraper.scrape(url)
            slug = raw_data.get("hostname", "").split('.')[0]
        elif "menew.ir" in url:
            source_name = "menew"
            raw_data = menewautoscraper.scrape(url)
            slug = raw_data.get("hostname", "").split('.')[0]
        else:
            print(f"  -> ERROR: No scraper found for URL: {url}")
            return

        raw_file_path = RAW_DATA_DIR / f"{source_name}_{slug}_raw.json"
        with raw_file_path.open('w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 1 Complete: Raw data saved to {raw_file_path}")

        # --- STAGE 2: TRANSFORM ---
        transformed_data = None
        
        # Decide which transformer to use based on the source name
        if source_name == "qbar":
            transformed_data = qbar_transformer.transform(raw_data)
        elif source_name == "qrmenusaz":
            transformed_data = qrmenusaz_transformer.transform(raw_data['api_data'])
        elif source_name == "menusaz":
            transformed_data = menusaz_transformer.transform(raw_data['api_data'])
        elif source_name == "menew":
            transformed_data = menew_transformer.transform(raw_data)
        
        if not transformed_data:
            raise Exception("Transformation failed, returned no data.")

        transformed_file_path = TRANSFORMED_DATA_DIR / f"{source_name}_{slug}_transformed.json"
        with transformed_file_path.open('w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 2 Complete: Transformed menu saved to {transformed_file_path}")

        # --- STAGE 3 (Placeholder) ---
        print(f"  -> Stage 3 (Image Migration) is the next step for '{transformed_file_path}'.")

    except Exception as e:
        print(f"  -> !!! PIPELINE FAILED for {url}: {e}")


if __name__ == "__main__":
    # The script takes URLs from the command line instead of a hardcoded list.
    
    # sys.argv is a list containing the script name followed by all arguments.
    if len(sys.argv) < 2:
        print("\n❌ Error: No URLs provided.")
        print("✅ Usage: python migrator_tool.py <url1> <url2> ...")
        sys.exit(1) # Exit the script with an error code

    # The URLs to process are all arguments after the script name.
    urls_to_process = sys.argv[1:]
    
    print(f"Found {len(urls_to_process)} URL(s) to process.")

    for restaurant_url in urls_to_process:
        process_restaurant(restaurant_url)

    print("\n\n🎉 All pipelines finished.")
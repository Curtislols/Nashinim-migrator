import sys
import json
from pathlib import Path
import asyncio
import inspect

# --- Add the project root to Python's path ---
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

# --- Import scrapers ---
from scrapers import (
    qbar_scraper, menusaz_scraper, qrmenusaz_scraper,
    menew_scraper, delino_scraper, hidigimenu_scraper,
    snappfood_scraper, menudigital_scraper
)

# --- Import Transformer CLASSES ---
from data_transformers.delino_transformer import DelinoTransformer
from data_transformers.hidigimenu_transformer import HidigimenuTransformer
from data_transformers.menew_transformer import MenewTransformer
from data_transformers.menusaz_transformer import MenusazTransformer
from data_transformers.menudigital_transformer import MenudigitalTransformer
from data_transformers.qbar_transformer import QbarTransformer
from data_transformers.qrmenusaz_transformer import QrmenusazTransformer
from data_transformers.snappfood_transformer import SnappfoodTransformer

# --- Import other project modules ---
from platform_detector import detect_platform
from scrapers.menusaz_scraper import get_menu_choices
# from image_migrator import migrate_images_for_menu # <-- THIS LINE IS NOW REMOVED

# --- Custom Exception Classes ---
class ScrapingError(Exception):
    """Raised when a scraper fails to access or retrieve data from a website."""
    pass

class MenuNotFoundError(ScrapingError):
    """A specific type of ScrapingError raised when a menu cannot be found (404)."""
    pass

class TransformationError(Exception):
    """Raised when the transformer fails to process the raw data."""
    pass


# --- Load Configuration ---
try:
    with open(SCRIPT_DIR / "config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    ICON_MAPPING = config["icon_mapping"]
    DEFAULT_ICON = config["default_icon"]
except FileNotFoundError:
    print("❌ FATAL ERROR: config.json not found. Please create it.")
    sys.exit(1)

# --- Platform to Class Instance Mapping ---
PLATFORM_MAPPING = {
    "menusaz": {
        "scraper": menusaz_scraper.scrape,
        "transformer": MenusazTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": True,
        "choice_finder": get_menu_choices
    },
    "delino": {"scraper": delino_scraper.scrape, "transformer": DelinoTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "menew": {"scraper": menew_scraper.scrape, "transformer": MenewTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "qrmenusaz": {"scraper": qrmenusaz_scraper.scrape, "transformer": QrmenusazTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "qbar": {"scraper": qbar_scraper.scrape, "transformer": QbarTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "hidigimenu": {"scraper": hidigimenu_scraper.scrape, "transformer": HidigimenuTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "snappfood": {"scraper": snappfood_scraper.scrape, "transformer": SnappfoodTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
    "menudigital": {"scraper": menudigital_scraper.scrape, "transformer": MenudigitalTransformer(ICON_MAPPING, DEFAULT_ICON).transform, "interactive": False},
}


# --- MAIN PIPELINE for Command-Line Tool ---
async def process_restaurant(url: str, output_path: Path):
    print(f"\n=============================================")
    print(f"STARTING PIPELINE FOR: {url}")
    print(f"=============================================")
    try:
        platform_name = await asyncio.to_thread(detect_platform, url)
        if not platform_name:
            raise Exception(f"Could not identify the platform for {url}")

        platform_config = PLATFORM_MAPPING[platform_name]
        scraper_func = platform_config["scraper"]
        transformer_func = platform_config["transformer"]
        
        if inspect.iscoroutinefunction(scraper_func):
            raw_data = await scraper_func(url)
        else:
            raw_data = await asyncio.to_thread(scraper_func, url)

        slug = raw_data.get("id") or raw_data.get("slug") or raw_data.get("hostname", "data").split('.')[0]
        
        (output_path / "raw_data").mkdir(parents=True, exist_ok=True)
        raw_file_path = output_path / "raw_data" / f"{platform_name}_{slug}_raw.json"
        with raw_file_path.open('w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 1 Complete: Raw data saved to {raw_file_path}")

        transformed_data = transformer_func(raw_data)
        if not transformed_data:
            raise Exception("Transformation failed.")

        (output_path / "transformed_data").mkdir(parents=True, exist_ok=True)
        transformed_file_path = output_path / "transformed_data" / f"{platform_name}_{slug}_transformed.json"
        with transformed_file_path.open('w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        print(f"  -> Stage 2 Complete: Transformed menu saved to {transformed_file_path}")
        print("  -> Pipeline finished successfully.")

    except Exception as e:
        print(f"  -> !!! PIPELINE FAILED for {url}: {e}")

# --- MAIN ASYNC EXECUTION FUNCTION for Command-Line Tool ---
async def main():
    print("✅ Migrator Tool script started...")
    
    if len(sys.argv) < 2:
        print("\n❌ Error: No URLs provided.")
        print("✅ Usage: python migrator_tool.py <url1> <url2> ...")
        sys.exit(1)

    urls_to_process = sys.argv[1:]
    print(f"Found {len(urls_to_process)} URL(s) to process.")
    OUTPUT_DIR = SCRIPT_DIR / "output"

    tasks = [process_restaurant(url, output_path=OUTPUT_DIR) for url in urls_to_process]
    await asyncio.gather(*tasks)

    print("\n\n🎉 All pipelines finished.")

# --- MAIN EXECUTION BLOCK for Command-Line Tool ---
if __name__ == "__main__":
    asyncio.run(main())
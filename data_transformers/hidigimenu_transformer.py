# data_transformers/hidigimenu_transformer.py
import json
import re

# --- Universal Helper Functions ---
ICON_MAPPING = {
    "پیتزا": "pizza-slice", "برگر": "hamburger", "مرغ": "chicken-dish",
    "ماهی": "fish", "سالاد": "leaf", "نوشیدنی": "soda-can",
    "قهوه": "coffee", "چای": "hot-tea", "دمنوش": "hot-tea",
    "کیک": "cake-slice", "دسر": "cake-slice", "پاستا": "utensils",
    "صبحانه": "croissant", "سوپ": "utensils", "ساید": "utensils",
}
DEFAULT_ICON = "utensils"

def assign_icon(category_name: str) -> str:
    """Assigns an icon by checking for keywords in the category title."""
    if not category_name:
        return DEFAULT_ICON
    for keyword, icon in ICON_MAPPING.items():
        if keyword in category_name:
            return icon
    return DEFAULT_ICON

def convert_price_to_toman(price_input) -> int:
    """
    Converts a price from an unknown unit to an integer in Toman using a heuristic.
    """
    if not price_input: return 0
    try:
        price_num = int(float(price_input))
    except (ValueError, TypeError):
        return 0

    if price_num > 1000000: return price_num // 10
    elif 0 < price_num < 1000: return price_num * 1000
    else: return price_num

def _clean_and_convert_price(price_str: str) -> int:
    """
    Cleans complex price strings (e.g., "125,000 تومان") and converts to Toman.
    """
    if not price_str:
        return 0
    # Remove commas and any non-digit characters
    cleaned_str = re.sub(r'[^\d]', '', price_str)
    # Use the universal converter
    return convert_price_to_toman(cleaned_str)

# --- Main Transformer Logic ---
def transform(source_data: dict) -> dict | None:
    """
    Transforms a raw HidigiMenu (scraped HTML) object into our standard menu format.
    """
    try:
        menu_data = source_data.get("api_data", {})
        if not menu_data:
            print("  -> 'api_data' key not found for HidigiMenu transformer.")
            return None

        transformed_menu = {
            "name": menu_data.get("name", "منو اصلی"),
            "categories": []
        }

        source_categories = menu_data.get("categories", [])

        for source_cat in source_categories:
            category_name = source_cat.get("name", "")
            new_category = {
                "name": category_name,
                "icon": assign_icon(category_name),
                "visibleInMenu": True,
                "items": []
            }

            for item in source_cat.get("items", []):
                new_item = {
                    "name": item.get("name", "").strip(),
                    "description": item.get("description", "").strip(),
                    "price": _clean_and_convert_price(item.get("price", "0")),
                    "status": "available", # Assumed available
                    "image": None,
                    "original_image_url": item.get("image"),
                }
                new_category["items"].append(new_item)

            if new_category["items"]:
                transformed_menu["categories"].append(new_category)
            
        return transformed_menu

    except Exception as e:
        print(f"  -> An unexpected error occurred in HidigiMenu transformer: {e}")
        return None
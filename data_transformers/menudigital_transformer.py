# data_transformers/menudigital_transformer.py
import json
import re

# --- Universal Helper Functions ---
def assign_icon(category_name: str, icon_mapping: dict, default_icon: str) -> str:
    """Assigns an icon by checking for keywords in the category title."""
    if not category_name:
        return default_icon
    for keyword, icon in icon_mapping.items():
        if keyword in category_name:
            return icon
    return default_icon

def assign_icon(category_name: str) -> str:
    if not category_name: return DEFAULT_ICON
    for keyword, icon in ICON_MAPPING.items():
        if keyword in category_name: return icon
    return DEFAULT_ICON

def convert_price_to_toman(price_input) -> int:
    if not price_input: return 0
    try:
        price_num = int(float(price_input))
    except (ValueError, TypeError):
        return 0
    if price_num > 1000000: return price_num // 10
    elif 0 < price_num < 1000: return price_num * 1000
    else: return price_num

def _clean_and_convert_price(price_str: str) -> int:
    if not price_str: return 0
    cleaned_str = re.sub(r'[^\d]', '', price_str)
    return convert_price_to_toman(cleaned_str)

# --- Main Transformer Logic ---
def transform(source_data: dict) -> dict | None:
    """Transforms a raw MenuDigital object into our standard menu format."""
    try:
        menu_data = source_data.get("api_data", {})
        if not menu_data:
            return None

        transformed_menu = {"name": menu_data.get("name", "منو اصلی"), "categories": []}
        for source_cat in menu_data.get("categories", []):
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
                    "status": "available",
                    "image": None,
                    "original_image_url": item.get("image"),
                }
                new_category["items"].append(new_item)
            if new_category["items"]:
                transformed_menu["categories"].append(new_category)
        return transformed_menu
    except Exception as e:
        print(f"  -> An unexpected error in MenuDigital transformer: {e}")
        return None
# data_transformers/menusaz_transformer.py
import json
import re

# --- Universal Helper Functions ---
ICON_MAPPING = {
    "چای": "hot-tea", "دمنوش": "hot-tea", "قهوه": "coffee",
    "نوشیدنی": "soda-can", "اسموتی": "glass-water", "شیک": "glass-water",
    "صبحانه": "croissant", "دسر": "cake-slice", "کیک": "cake-slice",
    "سالاد": "leaf", "سوخاری": "drumstick-bite", "کیمباپ": "utensils",
    "نودل": "utensils",
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

def convert_price_to_toman(price_str: str) -> int:
    """
    Converts a price string from an unknown unit (Rial, Toman, or KiloToman)
    to an integer in Toman using a heuristic.
    """
    if not price_str or not price_str.strip().isdigit():
        return 0
    price_num = int(price_str.strip())
    if price_num > 1000000:
        return price_num // 10
    elif 0 < price_num < 1000:
        return price_num * 1000
    else:
        return price_num

def transform(source_data: dict) -> dict | None:
    """
    Transforms a raw Menusaz/QRmenusaz JSON object into our standard menu format.
    """
    if not source_data or not source_data.get("status"):
        print("  -> Invalid or empty source data for Menusaz transformer.")
        return None

    transformed_menu = { "name": "منو اصلی", "categories": [] }
    source_categories = source_data.get("items", [])

    for source_cat in source_categories:
        category_name = source_cat.get("name", "")
        new_category = {
            "name": category_name,
            "icon": assign_icon(category_name),
            "visibleInMenu": True,
            "items": []
        }

        for item in source_cat.get("items", []):
            item_name = item.get("name", "")
            price_number_str = item.get("price_number", "0")
            
            # Logic to handle variations (items with multiple prices)
            if "/" in price_number_str:
                prices = [p.strip() for p in price_number_str.split('/')]
                match = re.search(r'\((.*?)\)', item_name)
                if match:
                    variation_names = [v.strip() for v in match.group(1).split('/')]
                    base_name = item_name.split('(')[0].strip()
                    
                    if len(prices) == len(variation_names):
                        for i, price_str in enumerate(prices):
                            new_item = {
                                "name": f"{base_name} ({variation_names[i]})",
                                "description": item.get("description", "").strip(),
                                "price": convert_price_to_toman(price_str), # Using correct function
                                "status": "available" if item.get("e_enable") == "1" else "unavailable",
                                "image": None,
                                "original_image_url": item.get("image") if item.get("image") else None,
                            }
                            new_category["items"].append(new_item)
                        continue
            
            # Logic for simple, single-price items
            new_item = {
                "name": item_name.strip(),
                "description": item.get("description", "").strip(),
                "price": convert_price_to_toman(price_number_str), # Using correct function
                "status": "available" if item.get("e_enable") == "1" else "unavailable",
                "image": None,
                "original_image_url": item.get("image") if item.get("image") else None,
            }
            new_category["items"].append(new_item)

        if new_category["items"]:
            transformed_menu["categories"].append(new_category)
            
    return transformed_menu
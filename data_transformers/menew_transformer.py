import json
import re

# --- Universal Helper Functions ---
# We use the same helper functions for icons and prices to keep all transformers consistent.

ICON_MAPPING = {
    "قهوه": "coffee",
    "نوشیدنی": "soda-can",
    "گرم": "hot-tea", # For "نوشیدنی‌های گرم"
    "سرد": "snowflake",
    "چای": "hot-tea",
    "دمنوش": "hot-tea",
    "کیک": "cake-slice",
    "دسر": "cake-slice",
    "صبحانه": "croissant",
    "سالاد": "leaf",
    "غذا": "utensils", # Generic for "غذای ایرانی"
    "پیش‌غذا": "utensils",
    "شیک": "glass-water",
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
    Converts a price from an unknown unit (Rial, Toman, or KiloToman)
    to an integer in Toman using a heuristic. Handles both strings and numbers.
    """
    if not price_input:
        return 0
        
    try:
        price_num = int(float(price_input))
    except (ValueError, TypeError):
        return 0

    if price_num > 1000000:
        return price_num // 10
    elif 0 < price_num < 1000:
        return price_num * 1000
    else:
        return price_num

def clean_html(raw_html: str) -> str:
    """Removes HTML tags from a string."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

# --- Main Transformer Logic ---

def transform(source_data: dict) -> dict | None:
    """
    Transforms a raw MeNew JSON object into our standard menu format.
    """
    try:
        # Navigate deep into the nested GraphQL-like structure
        entity = source_data.get("api_data", {}).get("data", {}).get("entity", {})
        if not entity:
            print("  -> 'entity' key not found in source data for MeNew transformer.")
            return None
        
        menus = entity.get("menus", [])
        if not menus:
            print("  -> No menus found in source data.")
            return None

        # We'll process the first menu found
        main_menu = menus[0]
        
        transformed_menu = {
            "name": main_menu.get("label", "منو اصلی"),
            "categories": []
        }

        for source_cat in main_menu.get("categories", []):
            category_name = source_cat.get("label", "")
            new_category = {
                "name": category_name,
                "icon": assign_icon(category_name),
                "visibleInMenu": source_cat.get("status") == "V",
                "items": []
            }

            for item in source_cat.get("items", []):
                shop_item = item.get("shopItem")
                if not shop_item:
                    continue # Skip items that can't be purchased

                shop_item_price = shop_item.get("shopItemPrice")
                price = shop_item_price.get("price") if shop_item_price else 0

                new_item = {
                    "name": item.get("name"),
                    "description": clean_html(item.get("description", "")),
                    "price": convert_price_to_toman(price),
                    "status": "available" if not shop_item.get("isSoldOut") else "unavailable",
                    "image": None,
                    "original_image_url": item.get("thumbnail") if item.get("thumbnail") else None,
                }
                new_category["items"].append(new_item)

            if new_category["items"]:
                transformed_menu["categories"].append(new_category)
            
        return transformed_menu

    except Exception as e:
        print(f"  -> An unexpected error occurred in MeNew transformer: {e}")
        return None
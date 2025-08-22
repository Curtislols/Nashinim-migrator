# data_transformers/delino_transformer.py
import json

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

def clean_image_url(url: str) -> str | None:
    """Removes the #SIZEOFIMAGE# placeholder from Delino URLs."""
    if not url:
        return None
    return url.replace("_#SIZEOFIMAGE#", "")

# --- Main Transformer Logic ---
def transform(source_data: dict) -> dict | None:
    """
    Transforms a raw Delino JSON object into our standard menu format.
    """
    try:
        api_data = source_data.get("api_data", {})
        menu_data = api_data.get("menu", {})
        profile_data = api_data.get("profile", {})
        
        if not menu_data:
            print("  -> 'menu' key not found in source data for Delino transformer.")
            return None

        transformed_menu = {
            "name": profile_data.get("name", "منو اصلی").strip(),
            "categories": []
        }

        source_categories = menu_data.get("categories", [])

        for source_cat in source_categories:
            category_name = source_cat.get("title", "")
            new_category = {
                "name": category_name,
                "icon": assign_icon(category_name),
                "visibleInMenu": source_cat.get("isActive", True),
                "items": []
            }

            # In Delino's structure, items are nested deeply
            if source_cat.get("sub") and len(source_cat["sub"]) > 0:
                items_list = source_cat["sub"][0].get("food", [])
                for item in items_list:
                    new_item = {
                        "name": item.get("title", "").strip(),
                        "description": item.get("ingredient", "").strip(),
                        "price": convert_price_to_toman(item.get("price", 0)),
                        "status": "available" if item.get("available") else "unavailable",
                        "image": None, # Placeholder
                        "original_image_url": clean_image_url(item.get("img")),
                    }
                    new_category["items"].append(new_item)

            if new_category["items"]:
                transformed_menu["categories"].append(new_category)
            
        return transformed_menu

    except Exception as e:
        print(f"  -> An unexpected error occurred in Delino transformer: {e}")
        return None
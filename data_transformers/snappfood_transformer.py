# data_transformers/snappfood_transformer.py
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

# --- Main Transformer Logic ---
def transform(source_data: dict) -> dict | None:
    """
    Transforms a raw Snappfood JSON object into our standard menu format.
    """
    try:
        # --- THIS IS THE FIX ---
        # Look inside the 'api_data' key for the profile and menu
        api_data = source_data.get("api_data", {})
        profile_data = api_data.get("profile", {})
        menu_data = api_data.get("menu", {})
        
        if not menu_data or not profile_data:
            print("  -> Invalid or empty source data for Snappfood transformer.")
            return None

        transformed_menu = {
            "name": profile_data.get("title", "منو اصلی"),
            "categories": []
        }

        for category in menu_data.get("menuCategories", []):
            category_name = category.get("title", "")
            new_category = {
                "name": category_name,
                "icon": assign_icon(category_name),
                "visibleInMenu": True,
                "items": []
            }
            
            for product in category.get("products", []):
                for variation in product.get("variations", []):
                    item_name = product.get("title", "")
                    if variation.get("title"):
                        item_name = f"{item_name} ({variation['title']})"
                    
                    image_url = (variation.get("images") or product.get("images") or [{}])[0].get("src")

                    new_item = {
                        "name": item_name.strip(),
                        "description": variation.get("description", "").strip(),
                        "price": convert_price_to_toman(variation.get("price")),
                        "status": "available" if variation.get("active") else "unavailable",
                        "image": None,
                        "original_image_url": image_url,
                    }
                    new_category["items"].append(new_item)
            
            if new_category["items"]:
                transformed_menu["categories"].append(new_category)
            
        return transformed_menu

    except Exception as e:
        print(f"  -> An unexpected error occurred in Snappfood transformer: {e}")
        return None
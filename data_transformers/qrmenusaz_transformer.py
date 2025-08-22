import json

# Keyword mapping for category icons for the Menusaz platform
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

def convert_price_to_rial(price_str: str) -> int:
    """
    Converts a price string from Menusaz's "KiloToman" format to an integer in Rial.
    - Assumes the number is in thousands of Toman (e.g., "343" -> 343,000 Toman).
    - Converts the final Toman value to Rial by multiplying by 10.
    """
    if not price_str or not price_str.isdigit():
        return 0
    price_num = int(price_str)
    
    # The format is consistently KiloToman
    price_in_toman = price_num * 1000
    price_in_rial = price_in_toman * 10
    return price_in_rial

def transform(source_data: dict) -> dict:
    """
    Transforms a raw Menusaz/QRmenusaz JSON object into our standard menu format.
    """
    if not source_data or not source_data.get("status"):
        print("  -> Invalid or empty source data for Menusaz transformer.")
        return None

    transformed_menu = {
        "name": "منو اصلی", # Provide a default name
        "categories": []
    }

    source_categories = source_data.get("items", [])

    for source_cat in source_categories:
        category_name = source_cat.get("name", "")
        new_category = {
            "name": category_name,
            "icon": assign_icon(category_name),
            "visibleInMenu": True, # Default to True as this info isn't provided
            "items": []
        }

        for item in source_cat.get("items", []):
            new_item = {
                "name": item.get("name", "").strip(), # Add .strip(),
                "description": item.get("description", "").strip(), # Add .strip()
                "price": convert_price_to_rial(item.get("price_number", "0")),
                "status": "available" if item.get("e_enable") == "1" else "unavailable",
                "image": None, # Placeholder for the new image URL
                "original_image_url": item.get("image") if item.get("image") else None,
            }
            new_category["items"].append(new_item)

        if new_category["items"]:
            transformed_menu["categories"].append(new_category)
            
    return transformed_menu

# Example of how you would run this from your main.py
if __name__ == '__main__':
    # This is for testing. You would normally call this from your main.py
    try:
        with open('source_menusaz_menu.json', 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        transformed = transform(test_data)
        
        if transformed:
            with open('transformed_menusaz_menu.json', 'w', encoding='utf-8') as f:
                json.dump(transformed, f, indent=2, ensure_ascii=False)
            print("Test transformation was successful!")

    except FileNotFoundError:
        print("Create a 'source_menusaz_menu.json' file to test this transformer.")
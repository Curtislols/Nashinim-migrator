# data_transformers/qbar_transformer.py
import json

# --- Universal Helper Functions ---
# You can share these across transformers or keep them separate.

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
    Transforms a raw QBar JSON object into our standard menu format.
    """
    qbar_api_data = source_data.get("api_data")
    if not qbar_api_data or "error" in qbar_api_data:
        print("  -> Invalid or empty 'api_data' for Qbar transformer.")
        return None

    transformed_menu = {
        "name": qbar_api_data.get("title", "منو اصلی"),
        "categories": []
    }

    source_categories = qbar_api_data.get("menu_with_products", [])

    for source_cat in source_categories:
        category_name = source_cat.get("title", "")
        new_category = {
            "name": category_name,
            "icon": assign_icon(category_name),
            "visibleInMenu": source_cat.get("sf_active", True),
            "items": []
        }

        for product in source_cat.get("products", []):
            base_item = {
                "name": product.get("title"),
                "description": product.get("content", ""),
                "price": 0,
                "status": "available" if product.get("state") == "active" else "unavailable",
                "image": None,
            }
            if product.get("food_images"):
                base_item["original_image_url"] = product["food_images"][0].get("picture")

            sub_foods = product.get("sub_foods", [])
            if sub_foods:
                for sub_food in sub_foods:
                    variation_item = base_item.copy()
                    variation_item["name"] = f"{base_item['name']} ({sub_food['title']})"
                    variation_item["price"] = convert_price_to_toman(sub_food.get("price", "0"))
                    new_category["items"].append(variation_item)
            else:
                base_item["price"] = convert_price_to_toman(product.get("price", "0"))
                new_category["items"].append(base_item)

        if new_category["items"]:
            transformed_menu["categories"].append(new_category)
            
    return transformed_menu
# data_transformers/snappfood_transformer.py
from .base_transformer import BaseTransformer

class SnappfoodTransformer(BaseTransformer):
    """Transforms raw Snappfood JSON into our standard menu format."""
    
    def _is_source_valid(self, api_data: dict) -> bool:
        return "menu" in api_data and "profile" in api_data

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        return menu_data.get("profile", {}).get("title", "منو اصلی")

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("menu", {}).get("menuCategories", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("title", "")

    def _is_category_visible(self, category: dict) -> bool:
        return True

    def _get_items(self, category: dict) -> list:
        # Flatten products and their variations into one list
        all_items = []
        for product in category.get("products", []):
            # If no variations, treat the product itself as the item
            if not product.get("variations"):
                all_items.append({"product": product, "variation": product})
                continue
            # If there are variations, create an item for each
            for variation in product.get("variations", []):
                all_items.append({"product": product, "variation": variation})
        return all_items

    def _get_item_name(self, item: dict) -> str:
        product_name = item["product"].get("title", "")
        # Variation might be the product itself if no variations exist
        variation_name = item["variation"].get("title")
        
        # Avoid redundant names like "Pizza (Pizza)"
        if variation_name and variation_name != product_name:
            return f"{product_name} ({variation_name})"
        return product_name

    def _get_item_description(self, item: dict) -> str:
        return item["variation"].get("description", "")

    def _get_item_price(self, item: dict):
        return item["variation"].get("price", 0)

    def _get_item_status(self, item: dict) -> str:
        is_active = item["variation"].get("active", False)
        return "available" if is_active else "unavailable"

    def _get_item_image_url(self, item: dict) -> str | None:
        var_images = item["variation"].get("images")
        prod_images = item["product"].get("images")
        image_list = var_images or prod_images or []
        return image_list[0].get("src") if image_list else None
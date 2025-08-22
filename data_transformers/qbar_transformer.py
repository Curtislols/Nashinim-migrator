# data_transformers/qbar_transformer.py
from .base_transformer import BaseTransformer

class QbarTransformer(BaseTransformer):
    """Transforms raw QBar JSON into our standard menu format."""
    
    def _is_source_valid(self, api_data: dict) -> bool:
        return "id" in api_data

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        return menu_data.get("title", "منو اصلی")

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("menu_with_products", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("title", "")

    def _is_category_visible(self, category: dict) -> bool:
        return category.get("sf_active", True)

    def _get_items(self, category: dict) -> list:
        # Flatten products and their sub-foods (variations) into one list
        all_items = []
        for product in category.get("products", []):
            sub_foods = product.get("sub_foods", [])
            if sub_foods:
                for sub_food in sub_foods:
                    # Create a new item for each variation
                    var_item = {
                        "base_product": product,
                        "variation": sub_food
                    }
                    all_items.append(var_item)
            else:
                # This is a simple product with no variations
                all_items.append({"base_product": product, "variation": None})
        return all_items

    def _get_item_name(self, item: dict) -> str:
        base_name = item["base_product"].get("title", "")
        if item["variation"]:
            var_name = item["variation"].get("title", "")
            return f"{base_name} ({var_name})"
        return base_name

    def _get_item_description(self, item: dict) -> str:
        return item["base_product"].get("content", "")

    def _get_item_price(self, item: dict):
        if item["variation"]:
            return item["variation"].get("price", "0")
        return item["base_product"].get("price", "0")

    def _get_item_status(self, item: dict) -> str:
        return "available" if item["base_product"].get("state") == "active" else "unavailable"

    def _get_item_image_url(self, item: dict) -> str | None:
        images = item["base_product"].get("food_images", [])
        return images[0].get("picture") if images else None
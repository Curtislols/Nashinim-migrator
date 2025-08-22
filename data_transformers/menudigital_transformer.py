# data_transformers/menudigital_transformer.py
from .base_transformer import BaseTransformer

class MenudigitalTransformer(BaseTransformer):
    """Transforms raw MenuDigital HTML data into our standard menu format."""
    
    def _is_source_valid(self, api_data: dict) -> bool:
        return "categories" in api_data

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        return menu_data.get("name", "منو اصلی")

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("categories", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("name", "")

    def _is_category_visible(self, category: dict) -> bool:
        return True

    def _get_items(self, category: dict) -> list:
        return category.get("items", [])

    def _get_item_name(self, item: dict) -> str:
        return item.get("name", "").strip()

    def _get_item_description(self, item: dict) -> str:
        return item.get("description", "").strip()

    def _get_item_price(self, item: dict):
        return item.get("price", "0")

    def _get_item_status(self, item: dict) -> str:
        return "available"

    def _get_item_image_url(self, item: dict) -> str | None:
        return item.get("image")
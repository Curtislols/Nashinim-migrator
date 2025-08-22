# data_transformers/delino_transformer.py
from .base_transformer import BaseTransformer
from .helpers import clean_delino_image_url

class DelinoTransformer(BaseTransformer):
    """Transforms raw Delino JSON into our standard menu format."""

    def _is_source_valid(self, api_data: dict) -> bool:
        return "menu" in api_data and "categories" in api_data["menu"]

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        return menu_data.get("profile", {}).get("name", "منو اصلی").strip()

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("menu", {}).get("categories", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("title", "")

    def _is_category_visible(self, category: dict) -> bool:
        return category.get("isActive", True)

    def _get_items(self, category: dict) -> list:
        if category.get("sub") and len(category["sub"]) > 0:
            return category["sub"][0].get("food", [])
        return []

    def _get_item_name(self, item: dict) -> str:
        return item.get("title", "").strip()

    def _get_item_description(self, item: dict) -> str:
        return item.get("ingredient", "").strip()

    def _get_item_price(self, item: dict):
        return item.get("price", 0)

    def _get_item_status(self, item: dict) -> str:
        return "available" if item.get("available") else "unavailable"

    def _get_item_image_url(self, item: dict) -> str | None:
        return clean_delino_image_url(item.get("img"))
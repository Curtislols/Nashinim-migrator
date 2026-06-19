# data_transformers/menew_transformer.py
from .base_transformer import BaseTransformer
from .helpers import clean_html

class MenewTransformer(BaseTransformer):
    """Transforms raw MeNew GraphQL data into our standard menu format."""

    def _is_source_valid(self, api_data: dict) -> bool:
        return "data" in api_data and "entity" in api_data["data"]

    def _get_menu_data(self, api_data: dict) -> dict:
        # We process the first menu found in the entity
        menus = api_data.get("data", {}).get("entity", {}).get("menus", [])
        return menus[0] if menus else {}

    def _get_menu_name(self, menu_data: dict) -> str:
        return menu_data.get("label", "منو اصلی")

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("categories", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("label", "")

    def _is_category_visible(self, category: dict) -> bool:
        return category.get("status") == "V"

    def _get_items(self, category: dict) -> list:
        # Filter for items that can be purchased
        return [item for item in category.get("items", []) if item.get("shopItem")]

    def _get_item_name(self, item: dict) -> str:
        return item.get("name", "")

    def _get_item_description(self, item: dict) -> str:
        return clean_html(item.get("description", ""))

    def _get_item_price(self, item: dict):
        shop_item_price = item.get("shopItem", {}).get("shopItemPrice", {})
        return shop_item_price.get("price", 0)

    def _get_item_status(self, item: dict) -> str:
        is_sold_out = item.get("shopItem", {}).get("isSoldOut", False)
        return "unavailable" if is_sold_out else "available"

    def _get_item_image_url(self, item: dict) -> str | None:
        return item.get("thumbnail")
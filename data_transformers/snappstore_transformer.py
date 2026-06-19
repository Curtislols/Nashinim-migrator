from .base_transformer import BaseTransformer


class SnappstoreTransformer(BaseTransformer):
    """Transforms raw Snapp-Store __NEXT_DATA__ into our standard menu format."""

    def _is_source_valid(self, api_data: dict) -> bool:
        return "vendor" in api_data and "menuCategories" in api_data.get("vendor", {})

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        # Prefer the vendor API name; fall back to SSR vendor name field
        vi = menu_data.get("vendor_info", {})
        return vi.get("name") or menu_data.get("vendor", {}).get("name", "منو اصلی")

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("vendor", {}).get("menuCategories", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("title", "")

    def _is_category_visible(self, category: dict) -> bool:
        return category.get("isActive", True) and category.get("snappIsActive", True)

    def _get_items(self, category: dict) -> list:
        return [
            {"item": item, "cdn_base": ""}   # cdn_base injected in _get_item_image_url
            for item in category.get("menuItems", [])
        ]

    # Override transform to thread cdn_base through
    def transform(self, source_data: dict) -> dict | None:
        self._cdn_base = source_data.get("api_data", {}).get("cdn_base", "")
        return super().transform(source_data)

    def _get_item_name(self, item: dict) -> str:
        return item["item"].get("title", "").strip()

    def _get_item_description(self, item: dict) -> str:
        return (item["item"].get("description") or "").strip()

    def _get_item_price(self, item: dict):
        return item["item"].get("price", 0)

    def _get_item_status(self, item: dict) -> str:
        i = item["item"]
        return "available" if i.get("available") and i.get("active") else "unavailable"

    def _get_item_image_url(self, item: dict) -> str | None:
        images = item["item"].get("images", [])
        if not images:
            return None
        filename = images[0]
        if filename.startswith("http"):
            return filename
        return f"{self._cdn_base}{filename}" if self._cdn_base else None

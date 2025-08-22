# data_transformers/menusaz_transformer.py
import re
from .base_transformer import BaseTransformer

class MenusazTransformer(BaseTransformer):
    """Transforms raw Menusaz JSON into our standard menu format."""

    def _is_source_valid(self, api_data: dict) -> bool:
        return api_data.get("status") == True

    def _get_menu_data(self, api_data: dict) -> dict:
        return api_data

    def _get_menu_name(self, menu_data: dict) -> str:
        return "منو اصلی"

    def _get_categories(self, menu_data: dict) -> list:
        return menu_data.get("items", [])

    def _get_category_name(self, category: dict) -> str:
        return category.get("name", "")

    def _is_category_visible(self, category: dict) -> bool:
        return True

    def _get_items(self, category: dict) -> list:
        # This platform has complex variation logic that we handle here
        all_items = []
        for item in category.get("items", []):
            item_name = item.get("name", "")
            price_str = item.get("price_number", "0")
            
            # If price contains '/', it's a variation product
            if "/" in price_str:
                prices = [p.strip() for p in price_str.split('/')]
                # Try to extract variation names from parenthesis
                match = re.search(r'\((.*?)\)', item_name)
                if match:
                    var_names = [v.strip() for v in match.group(1).split('/')]
                    base_name = item_name.split('(')[0].strip()
                    
                    if len(prices) == len(var_names):
                        for i, price in enumerate(prices):
                            # Create a unique item for each variation
                            var_item = item.copy()
                            var_item["name"] = f"{base_name} ({var_names[i]})"
                            var_item["price_number"] = price
                            all_items.append(var_item)
                        continue # Skip appending the original item

            # If no variations, add the simple item
            all_items.append(item)
        return all_items

    def _get_item_name(self, item: dict) -> str:
        return item.get("name", "").strip()

    def _get_item_description(self, item: dict) -> str:
        return item.get("description", "").strip()

    def _get_item_price(self, item: dict):
        return item.get("price_number", "0")

    def _get_item_status(self, item: dict) -> str:
        return "available" if item.get("e_enable") == "1" else "unavailable"

    def _get_item_image_url(self, item: dict) -> str | None:
        return item.get("image")
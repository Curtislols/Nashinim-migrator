# data_transformers/shared/base_transformer.py
from abc import ABC, abstractmethod
from . import helpers

class BaseTransformer(ABC):
    """
    An abstract base class for all menu transformers. It handles the
    generic structure of transformation, leaving the specific data
    extraction details to its subclasses.
    """
    def __init__(self, icon_mapping: dict, default_icon: str):
        self.icon_mapping = icon_mapping
        self.default_icon = default_icon

    def transform(self, source_data: dict) -> dict | None:
        """Transforms raw source data into our standard menu format."""
        try:
            api_data = source_data.get("api_data", {})
            if not self._is_source_valid(api_data):
                print(f"  -> Invalid or empty source data for {self.__class__.__name__}.")
                return None

            menu_data = self._get_menu_data(api_data)
            transformed_menu = {
                "name": self._get_menu_name(menu_data),
                "categories": []
            }

            for source_cat in self._get_categories(menu_data):
                category_name = self._get_category_name(source_cat)
                new_category = {
                    "name": category_name,
                    "icon": helpers.assign_icon(category_name, self.icon_mapping, self.default_icon),
                    "visibleInMenu": self._is_category_visible(source_cat),
                    "items": []
                }

                for item in self._get_items(source_cat):
                    new_item = {
                        "name": self._get_item_name(item),
                        "description": self._get_item_description(item),
                        "price": helpers.convert_price_to_toman(self._get_item_price(item)),
                        "status": self._get_item_status(item),
                        "image": None,
                        "original_image_url": self._get_item_image_url(item),
                    }
                    new_category["items"].append(new_item)

                if new_category["items"]:
                    transformed_menu["categories"].append(new_category)
            
            return transformed_menu
        except Exception as e:
            print(f"  -> An unexpected error occurred in {self.__class__.__name__}: {e}")
            return None

    # --- Abstract Methods (to be implemented by each subclass) ---
    @abstractmethod
    def _is_source_valid(self, api_data: dict) -> bool: pass
    @abstractmethod
    def _get_menu_data(self, api_data: dict) -> dict: pass
    @abstractmethod
    def _get_menu_name(self, menu_data: dict) -> str: pass
    @abstractmethod
    def _get_categories(self, menu_data: dict) -> list: pass
    @abstractmethod
    def _get_category_name(self, category: dict) -> str: pass
    @abstractmethod
    def _is_category_visible(self, category: dict) -> bool: pass
    @abstractmethod
    def _get_items(self, category: dict) -> list: pass
    @abstractmethod
    def _get_item_name(self, item: dict) -> str: pass
    @abstractmethod
    def _get_item_description(self, item: dict) -> str: pass
    @abstractmethod
    def _get_item_price(self, item: dict): pass
    @abstractmethod
    def _get_item_status(self, item: dict) -> str: pass
    @abstractmethod
    def _get_item_image_url(self, item: dict) -> str | None: pass
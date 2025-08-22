# data_transformers/shared/base_transformer.py
from abc import ABC, abstractmethod
from . import helpers # Import our new helpers

class BaseTransformer(ABC):
    """
    An abstract base class for all menu transformers. It handles the
    generic structure of transformation, leaving the specific data
    extraction details to its subclasses.
    """
    def __init__(self, icon_mapping: dict, default_icon: str):
        self.icon_mapping = icon_mapping
        self.default_icon = default_icon

    # --- The Main Transformation Logic (No longer duplicated!) ---
    def transform(self, source_data: dict) -> dict | None:
        """Transforms raw source data into our standard menu format."""
        try:
            # 1. Check if the data is valid first
            if not self._is_source_valid(source_data.get("api_data", {})):
                print(f"  -> Invalid or empty source data for {self.__class__.__name__}.")
                return None

            # 2. Get the main menu data object
            menu_data = self._get_menu_data(source_data.get("api_data", {}))

            transformed_menu = {
                "name": self._get_menu_name(menu_data),
                "categories": []
            }

            # 3. Universal category and item processing loop
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
    # These methods define the "contract" that each transformer must follow.

    @abstractmethod
    def _is_source_valid(self, api_data: dict) -> bool:
        """Check if the essential keys exist in the source data."""
        pass

    @abstractmethod
    def _get_menu_data(self, api_data: dict) -> dict:
        """Return the root object of the menu."""
        pass
    
    @abstractmethod
    def _get_menu_name(self, menu_data: dict) -> str:
        """Extract the menu's top-level name."""
        pass

    @abstractmethod
    def _get_categories(self, menu_data: dict) -> list:
        """Extract the list of category objects."""
        pass

    @abstractmethod
    def _get_category_name(self, category: dict) -> str:
        """Extract name from a single category object."""
        pass

    @abstractmethod
    def _is_category_visible(self, category: dict) -> bool:
        """Determine if a category is visible."""
        pass

    @abstractmethod
    def _get_items(self, category: dict) -> list:
        """Extract the list of item objects from a category."""
        pass

    # --- Item-level abstract methods ---
    @abstractmethod
    def _get_item_name(self, item: dict) -> str:
        """Extract name from a single item object."""
        pass

    @abstractmethod
    def _get_item_description(self, item: dict) -> str:
        """Extract description from a single item object."""
        pass

    @abstractmethod
    def _get_item_price(self, item: dict):
        """Extract price from a single item object."""
        pass

    @abstractmethod
    def _get_item_status(self, item: dict) -> str:
        """Extract availability status from a single item object."""
        pass

    @abstractmethod
    def _get_item_image_url(self, item: dict) -> str | None:
        """Extract the original image URL from a single item object."""
        pass
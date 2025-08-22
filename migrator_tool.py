# In migrator_tool.py

# --- Make sure the new choice-finding function is imported ---
from scrapers.menusaz_scraper import get_menu_choices

# ... (other imports)

# --- Updated Platform Mapping ---
PLATFORM_MAPPING = {
    # --- Interactive Platform Example ---
    "menusaz": {
        "scraper": menusaz_scraper.scrape,
        "transformer": MenusazTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": True, # <-- Flag to mark it as interactive
        "choice_finder": get_menu_choices # <-- Reference to the choice function
    },

    # --- Non-Interactive Platforms ---
    "delino": {
        "scraper": delino_scraper.scrape,
        "transformer": DelinoTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False
    },
    "menew": {
        "scraper": menew_scraper.scrape,
        "transformer": MenewTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False # <-- Assuming menew is not interactive for now
    },
    "qrmenusaz": {
        "scraper": qrmenusaz_scraper.scrape,
        "transformer": QrmenusazTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False
    },
    "qbar": {
        "scraper": qbar_scraper.scrape,
        "transformer": QbarTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False
    },
    "hidigimenu": {
        "scraper": hidigimenu_scraper.scrape,
        "transformer": HidigimenuTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False
    },
    "snappfood": {
        "scraper": snappfood_scraper.scrape,
        "transformer": SnappfoodTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False
    },
    "menudigital": {
        "scraper": menudigital_scraper.scrape,
        "transformer": MenudigitalTransformer(ICON_MAPPING, DEFAULT_ICON).transform,
        "interactive": False # <-- Assuming this is not interactive
    },
}
# data_transformers/shared/helpers.py
import re

def assign_icon(category_name: str, icon_mapping: dict, default_icon: str) -> str:
    """
    Assigns an icon by checking for keywords in the category title.
    This is the single, standardized version of this function.
    """
    if not category_name:
        return default_icon
    # Use case-insensitive matching for more robustness
    category_name_lower = category_name.lower()
    for keyword, icon in icon_mapping.items():
        if keyword.lower() in category_name_lower:
            return icon
    return default_icon

def convert_price_to_toman(price_input) -> int:
    """
    Converts a price from various formats (Rial, Toman, string, number)
    to an integer in Toman using a robust heuristic.
    """
    if price_input is None:
        return 0
    try:
        # Clean the string of any non-digit characters (e.g., "125,000 تومان")
        cleaned_str = re.sub(r'[^\d]', '', str(price_input))
        if not cleaned_str:
            return 0
        price_num = int(cleaned_str)
    except (ValueError, TypeError):
        return 0

    # Heuristic logic to standardize the price
    if price_num > 1000000:  # Assumed to be in Rial
        return price_num // 10
    elif 0 < price_num < 1000:  # Assumed to be in KiloToman (e.g., 125 -> 125,000)
        return price_num * 1000
    else:  # Assumed to be already in Toman
        return price_num

def clean_html(raw_html: str) -> str:
    """Removes HTML tags from a string."""
    if not raw_html:
        return ""
    cleaner = re.compile('<.*?>')
    return re.sub(cleaner, '', raw_html).strip()

def clean_delino_image_url(url: str) -> str | None:
    """Removes the #SIZEOFIMAGE# placeholder from Delino URLs."""
    if not url:
        return None
    return url.replace("_#SIZEOFIMAGE#", "")
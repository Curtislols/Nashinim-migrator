# scrapers/scraper_helpers.py
from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Page
# Add these imports at the top of scraper_helpers.py
from urllib.parse import urlsplit, urlunsplit, quote

def sanitize_url(url: str) -> str:
    """
    Safely URL-encodes non-ASCII characters in a URL's path to prevent
    Unicode errors in logging and error handling.
    """
    try:
        # Break the URL into its components (scheme, netloc, path, etc.)
        parts = urlsplit(url)
        # Safely encode only the path component
        safe_path = quote(parts.path)
        # Rebuild the URL with the encoded path
        return urlunsplit(parts._replace(path=safe_path))
    except Exception:
        # If anything goes wrong, just return the original URL
        return url
# The 'get_browser_page' function is unchanged and correct.
@contextmanager
def get_browser_page(headless: bool = True) -> Page:
    """A context manager to handle Playwright browser setup and teardown."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            yield page
        finally:
            browser.close()

# --- THIS FUNCTION IS THE FIX ---
def prompt_user_for_choice(page: Page, selector: str, prompt_message: str) -> bool:
    """
    Finds elements, prompts the user to choose one, and clicks their choice.
    It no longer waits for a navigation, making it flexible for SPAs.
    """
    try:
        page.wait_for_selector(selector, timeout=7000)
        choices = page.locator(selector).all()
        visible_choices = [c for c in choices if c.is_visible()]

        if not visible_choices:
            print("     No choices found to prompt the user.")
            return False

        print(f"\n{prompt_message}")
        for i, choice in enumerate(visible_choices, start=1):
            text = choice.text_content().strip().replace('\n', ' ')
            print(f"       [{i}] {text}")
        
        while True:
            try:
                user_idx = int(input("\n     Enter the number of your choice: ")) - 1
                if 0 <= user_idx < len(visible_choices):
                    chosen_button = visible_choices[user_idx]
                    break
                else:
                    print("     Invalid number.")
            except ValueError:
                print("     Invalid input.")
        
        print(f"     You chose: '{chosen_button.text_content().strip()}'. Clicking...")
        
        # --- REMOVED ---
        # The 'with page.expect_navigation(...)' block has been removed.
        # We just perform the click and let the calling script decide what to wait for.
        chosen_button.click()
        return True

    except Exception as e:
        print(f"     Could not prompt user for choice (or no choices found): {e}")
        return False
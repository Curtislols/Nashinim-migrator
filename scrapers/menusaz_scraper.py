# scrapers/menusaz_scraper.py
from urllib.parse import urlparse
from playwright.async_api import async_playwright

async def get_menu_choices(url: str) -> list:
    """
    Navigates to a Menusaz URL and returns a list of available menu choices.
    """
    print(f"  -> Discovering choices for: {url}")
    button_selector = ".t9_category"
    choices = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print("     Scanning for menu options...")
            await page.wait_for_selector(button_selector, state="visible", timeout=7000)
            
            buttons = await page.locator(button_selector).all()
            for i, button in enumerate(buttons):
                text = await button.text_content()
                choices.append({"id": i, "name": text.strip()})
        finally:
            await browser.close()
    return choices

async def scrape(url: str, choice_id: int = 0) -> dict:
    """
    Scrapes a Menusaz URL by clicking a chosen menu (by its index).
    """
    print(f"  -> Scraping Menusaz URL: {url} with choice ID: {choice_id}")
    api_path_keyword = "/Script/get_categories_items.php"
    button_selector = ".t9_category"
    record = {"url": url, "hostname": urlparse(url).netloc, "api_data": None}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            buttons = await page.locator(button_selector).all()
            if not buttons or choice_id >= len(buttons):
                raise ValueError(f"Invalid choice_id '{choice_id}'. Only {len(buttons)} options found.")

            chosen_button = buttons[choice_id]
            button_text = await chosen_button.text_content()
            print(f"     Found and clicking chosen option: '{button_text.strip()}'")

            async with page.expect_response(lambda res: api_path_keyword in res.url) as response_info:
                await chosen_button.click()
            
            response = await response_info.value
            if not response.ok:
                raise ValueError(f"API responded with status {response.status}")
            
            record["api_data"] = await response.json()
        finally:
            await browser.close()
    return record
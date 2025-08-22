# scrapers/menudigital_scraper.py
import json
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def scrape(url: str) -> dict:
    """
    Scrapes a MenuDigital.ir URL by interactively navigating its intro page
    and then parsing the final server-rendered HTML.
    """
    print(f"  -> Scraping MenuDigital URL: {url}")
    
    hostname = urlparse(url).hostname
    record = {"url": url, "hostname": hostname, "api_data": None}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("     Navigating to page...")
        page.goto(url, wait_until="domcontentloaded")
        
        intro_links_selector = ".resenbg a"
        
        try:
            page.wait_for_selector(intro_links_selector, timeout=5000)
            intro_links = page.locator(intro_links_selector).all()

            if intro_links:
                print("\n     Intro page detected. Please choose a menu:")
                choices = [{"text": link.text_content().strip().replace('\n', ' '), "element": link} for link in intro_links if link.is_visible()]

                for i, choice in enumerate(choices, start=1):
                    print(f"       [{i}] {choice['text']}")
                
                while True:
                    try:
                        user_choice_idx = int(input("\n     Enter the number of your choice: ")) - 1
                        if 0 <= user_choice_idx < len(choices):
                            chosen_button = choices[user_choice_idx]['element']
                            break
                        else:
                            print("     Invalid number.")
                    except ValueError:
                        print("     Invalid input.")
                
                print(f"     You chose: '{choices[user_choice_idx]['text']}'. Navigating...")
                
                with page.expect_navigation(wait_until="networkidle", timeout=30000):
                    chosen_button.click()
        except Exception:
            print("     No intro page detected, or it failed. Proceeding with current page.")

        print("     On final menu page. Capturing HTML...")
        html_content = page.content()
        final_url = page.url
        browser.close()

    # --- Parse Captured HTML with Beautiful Soup ---
    soup = BeautifulSoup(html_content, 'lxml')
    
    # --- THIS IS THE FIX ---
    # Find the correct elements on the final menu page, not the intro page.
    menu_name_tag = soup.select_one("a.navbar-brand h4.logo-text span")
    menu_name = menu_name_tag.text.strip() if menu_name_tag else "Menu"
    menu_data = {"name": menu_name, "categories": []}

    category_tags = soup.find_all('div', class_='hrtext')

    for cat_tag in category_tags:
        p_tag = cat_tag.find('p')
        if not p_tag: continue
        category_name = p_tag.text.strip()
        if not category_name: continue
        
        items_container = cat_tag.find_next_sibling('div', class_='row')
        if not items_container: continue # This will skip non-menu sections like "درباره"

        print(f"     Processing category: {category_name}")
        new_category = {"name": category_name, "items": []}

        for item_card in items_container.find_all('div', class_='card'):
            name_tag = item_card.find('p', {'id': lambda x: x and x.startswith('pname_')})
            if not name_tag: continue
            
            name = name_tag.text.strip()
            desc_tag = item_card.find('p', {'id': lambda x: x and x.startswith('dname_')})
            desc = desc_tag.text.strip() if desc_tag else ""
            price_tag = item_card.find('f')
            price = price_tag.text.strip() if price_tag else "0"
            image_tag = item_card.find('img')
            image_src = image_tag['src'] if image_tag and image_tag.has_attr('src') else None
            
            new_item = {
                "name": name, "description": desc, "price": price,
                "image": urljoin(final_url, image_src) if image_src else None,
                "status": "available",
            }
            new_category["items"].append(new_item)
            
        if new_category["items"]:
            menu_data["categories"].append(new_category)

    record["api_data"] = menu_data
    return record
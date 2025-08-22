import json
import re
import requests
import time
from urllib.parse import urlparse
# ❗️THIS LINE MUST BE CHANGED❗️
from scrapers.scraper_helpers import get_browser_page # Was: from .shared...


def scrape(url: str) -> dict:
    """
    Scrapes a MenuDigital.ir URL by using a shared helper to handle the
    interactive intro page, then parsing the final server-rendered HTML.
    """
    print(f"  -> Scraping MenuDigital URL: {url}")
    
    hostname = urlparse(url).hostname
    record = {"url": url, "hostname": hostname, "api_data": None}
    
    with get_browser_page() as page:
        print("     Navigating to page...")
        page.goto(url, wait_until="domcontentloaded")
        
        # This helper function handles the entire branch selection process
        prompt_user_for_choice(
            page, 
            selector=".resenbg a", 
            prompt_message="Intro page detected. Please choose a menu:"
        )

        print("     On final menu page. Capturing HTML...")
        html_content = page.content()
        final_url = page.url

    # --- Parse Captured HTML with Beautiful Soup ---
    soup = BeautifulSoup(html_content, 'lxml')
    
    menu_name_tag = soup.select_one("a.navbar-brand h4.logo-text span")
    menu_name = menu_name_tag.text.strip() if menu_name_tag else "Menu"
    menu_data = {"name": menu_name, "categories": []}

    for cat_tag in soup.find_all('div', class_='hrtext'):
        p_tag = cat_tag.find('p')
        if not p_tag or not p_tag.text.strip(): continue
        
        category_name = p_tag.text.strip()
        items_container = cat_tag.find_next_sibling('div', class_='row')
        if not items_container: continue

        print(f"     Processing category: {category_name}")
        new_category = {"name": category_name, "items": []}

        for item_card in items_container.find_all('div', class_='card'):
            name_tag = item_card.find('p', {'id': lambda x: x and x.startswith('pname_')})
            if not name_tag: continue
            
            new_item = {
                "name": name_tag.text.strip(),
                "description": item_card.find('p', {'id': lambda x: x and x.startswith('dname_')}).text.strip() if item_card.find('p', {'id': lambda x: x and x.startswith('dname_')}) else "",
                "price": item_card.find('f').text.strip() if item_card.find('f') else "0",
                "image": urljoin(final_url, item_card.find('img')['src']) if item_card.find('img') and item_card.find('img').has_attr('src') else None,
                "status": "available",
            }
            new_category["items"].append(new_item)
            
        if new_category["items"]:
            menu_data["categories"].append(new_category)

    record["api_data"] = menu_data
    return record
# scrapers/hidigimenu_scraper.py
import requests
import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def scrape(url: str) -> dict:
    """
    Scrapes a HidigiMenu URL. Uses Playwright for navigation and then
    BeautifulSoup to parse the final server-rendered HTML.
    """
    print(f"  -> Scraping HidigiMenu (HTML) URL: {url}")
    
    hostname = urlparse(url).netloc
    record = {"url": url, "hostname": hostname, "api_data": None}
    
    # --- STAGE 1: Use Playwright for Navigation ---
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("     Navigating to handle intro pages...")
        page.goto(url, wait_until="domcontentloaded")

        # In the future, add interactive clicks here if needed for this platform
        
        print("     On final menu page. Capturing HTML...")
        html_content = page.content()
        final_url = page.url
        browser.close()

    # --- STAGE 2: Parse the captured HTML with Beautiful Soup ---
    soup = BeautifulSoup(html_content, 'lxml')
    menu_data = {"name": soup.find('h5').text.strip() if soup.find('h5') else "Menu", "categories": []}

    all_categories_html = soup.find_all('h3', class_='subtitle')
    for category_html in all_categories_html:
        category_name = category_html.text.strip()
        print(f"     Processing category: {category_name}")
        new_category = {"name": category_name, "items": []}
        
        items_container = category_html.find_next_sibling('div', class_='row')
        if not items_container: continue
            
        all_items_html = items_container.find_all('div', class_='menu-item')
        for item_html in all_items_html:
            name = item_html.find('p', class_='font-weight-bold').text.strip()
            desc = item_html.find('small', class_='text-mute').text.strip()
            price = item_html.find('span', class_='price').text.strip()
            image_tag = item_html.find('img')
            
            image_src = image_tag['src'] if image_tag and image_tag.has_attr('src') else None
            image_full_url = urljoin(final_url, image_src) if image_src else None
            
            new_item = {
                "name": name, "description": desc, "price": price,
                "image": image_full_url, "status": "available",
            }
            new_category["items"].append(new_item)

        if new_category["items"]:
            menu_data["categories"].append(new_category)

    record["api_data"] = menu_data
    return record
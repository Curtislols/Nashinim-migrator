# scrapers/hidigimenu_scraper.py
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup  # <-- ADD THIS LINE
from .scraper_helpers import get_browser_page

def scrape(url: str) -> dict:
    """
    Scrapes a HidigiMenu URL using Playwright for navigation and then
    BeautifulSoup to parse the final server-rendered HTML.
    """
    print(f"  -> Scraping HidigiMenu (HTML) URL: {url}")

    hostname = urlparse(url).netloc
    record = {"url": url, "hostname": hostname, "api_data": None}

    with get_browser_page() as page:
        print("     Navigating to handle intro pages...")
        page.goto(url, wait_until="domcontentloaded")
        print("     On final menu page. Capturing HTML...")
        html_content = page.content()
        final_url = page.url

    soup = BeautifulSoup(html_content, 'lxml')
    menu_data = {"name": soup.find('h5').text.strip() if soup.find('h5') else "Menu", "categories": []}

    for category_html in soup.find_all('h3', class_='subtitle'):
        category_name = category_html.text.strip()
        print(f"     Processing category: {category_name}")
        new_category = {"name": category_name, "items": []}

        items_container = category_html.find_next_sibling('div', class_='row')
        if not items_container:
            continue

        for item_html in items_container.find_all('div', class_='menu-item'):
            new_item = {
                "name": item_html.find('p', class_='font-weight-bold').text.strip(),
                "description": item_html.find('small', class_='text-mute').text.strip(),
                "price": item_html.find('span', class_='price').text.strip(),
                "image": urljoin(final_url, item_html.find('img')['src']) if item_html.find('img') and item_html.find('img').has_attr('src') else None,
                "status": "available",
            }
            new_category["items"].append(new_item)

        if new_category["items"]:
            menu_data["categories"].append(new_category)

    record["api_data"] = menu_data
    return record
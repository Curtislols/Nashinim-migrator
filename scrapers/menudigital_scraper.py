from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from scrapers.scraper_helpers import get_browser_page


def scrape(url: str, choice_id: int = 0) -> dict:
    print(f"  -> Scraping MenuDigital URL: {url}")

    hostname = urlparse(url).hostname
    record = {"url": url, "hostname": hostname, "api_data": None}

    with get_browser_page() as page:
        page.goto(url, wait_until="domcontentloaded")

        # Handle optional branch/location selection intro page
        try:
            page.wait_for_selector(".resenbg a", timeout=4000)
            links = page.locator(".resenbg a").all()
            if links and choice_id < len(links):
                print(f"     Branch selection found. Clicking choice {choice_id}...")
                links[choice_id].click()
                page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass  # No selection needed — proceed directly

        html_content = page.content()
        final_url = page.url

    soup = BeautifulSoup(html_content, "lxml")

    name_tag = soup.select_one("a.navbar-brand h4.logo-text span")
    menu_name = name_tag.text.strip() if name_tag else "Menu"
    menu_data = {"name": menu_name, "categories": []}

    for cat_tag in soup.find_all("div", class_="hrtext"):
        p_tag = cat_tag.find("p")
        if not p_tag or not p_tag.text.strip():
            continue

        items_container = cat_tag.find_next_sibling("div", class_="row")
        if not items_container:
            continue

        category_name = p_tag.text.strip()
        new_category = {"name": category_name, "items": []}

        for card in items_container.find_all("div", class_="card"):
            name_el = card.find("p", {"id": lambda x: x and x.startswith("pname_")})
            if not name_el:
                continue

            desc_el = card.find("p", {"id": lambda x: x and x.startswith("dname_")})
            price_el = card.find("f")
            img_el = card.find("img")

            new_category["items"].append({
                "name": name_el.text.strip(),
                "description": desc_el.text.strip() if desc_el else "",
                "price": price_el.text.strip() if price_el else "0",
                "image": urljoin(final_url, img_el["src"]) if img_el and img_el.get("src") else None,
                "status": "available",
            })

        if new_category["items"]:
            menu_data["categories"].append(new_category)

    record["api_data"] = menu_data
    return record

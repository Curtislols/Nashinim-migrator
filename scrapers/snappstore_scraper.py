import re
import json
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"


def scrape(url: str) -> dict:
    hostname = urlparse(url).hostname          # ofset.snapp-store.com
    slug = hostname.split(".snapp-store.com")[0]  # ofset
    print(f"  -> Scraping Snapp-Store URL: {url}, slug: {slug}")

    record = {"url": url, "slug": slug, "api_data": None}
    vendor_info = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=MOBILE_UA, viewport={"width": 390, "height": 844})
        page = ctx.new_page()

        def handle_response(response):
            try:
                if "vendors" in response.url and response.status == 200:
                    vendor_info.update(response.json().get("data", {}))
            except Exception:
                pass

        page.on("response", handle_response)
        page.goto(url, wait_until="networkidle", timeout=40000)
        page.wait_for_timeout(3000)

        # Scroll to trigger lazy-loaded items; guard against mid-scroll navigations
        prev_height = 0
        for _ in range(20):
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)
                height = page.evaluate("document.body.scrollHeight")
            except Exception:
                break  # page navigated away during scroll — use what we have
            if height == prev_height:
                break
            prev_height = height

        html = page.content()
        browser.close()

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        raise ValueError("Could not find __NEXT_DATA__ on snapp-store page")

    next_data = json.loads(m.group(1))
    vendor = next_data.get("props", {}).get("pageProps", {}).get("vendor")
    if not vendor:
        raise ValueError("No vendor data found in __NEXT_DATA__")

    # Find CDN base URL from any img src on the page (e.g. https://cdn.snapp-store.com/foods/)
    cdn_base = ""
    cdn_match = re.search(r'(https://[^"\']+?/)\d{10,}\.(jpg|jpeg|png|webp)', html)
    if cdn_match:
        cdn_base = cdn_match.group(1)

    record["api_data"] = {
        "vendor": vendor,
        "vendor_info": vendor_info,
        "cdn_base": cdn_base,
    }
    return record

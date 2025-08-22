# recon_tool.py
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

def analyze_url(url: str):
    """
    Visits a URL and generates a reconnaissance report, saving the
    rendered HTML, a network log, and a screenshot.
    """
    print(f"🚀 Starting reconnaissance for: {url}")
    hostname = urlparse(url).hostname
    output_dir = Path(f"recon_report_{hostname}")
    output_dir.mkdir(exist_ok=True)
    
    network_log = []

    def handle_request(request):
        # We are interested in API calls, scripts, and stylesheets
        if request.resource_type in ["xhr", "fetch", "script", "stylesheet"]:
            network_log.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type
            })

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.on("request", handle_request)
        
        print(" -> Navigating to page...")
        # --- THIS IS THE FIX ---
        # Changed 'networkidle' to the more reliable 'domcontentloaded'
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        print(" -> Capturing data...")
        html_content = page.content()
        screenshot_path = output_dir / "recon_screenshot.png"
        page.screenshot(path=screenshot_path, full_page=True)
        
        page.remove_listener("request", handle_request)
        browser.close()

    html_path = output_dir / "recon_page_content.html"
    html_path.write_text(html_content, encoding='utf-8')
    
    network_path = output_dir / "recon_network_log.json"
    with network_path.open('w', encoding='utf-8') as f:
        json.dump(network_log, f, indent=2, ensure_ascii=False)
        
    print("\n✅ Reconnaissance Complete!")
    print(f" -> Report saved in folder: '{output_dir}/'")
    print(f"    - Screenshot: {screenshot_path}")
    print(f"    - Full HTML: {html_path}")
    print(f"    - Network Log: {network_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python recon_tool.py <url_to_analyze>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    analyze_url(target_url)
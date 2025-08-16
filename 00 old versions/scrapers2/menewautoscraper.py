from playwright.sync_api import sync_playwright
import json, requests, re
from pathlib import Path
from urllib.parse import urlparse

urls = [
    "https://khanehfamouri.menew.ir/catalogue",
    # add more...
]

api_endpoint = "https://citadel.menew.ir/api"
headers = {"Content-Type": "application/json"}
results = []

out_dir = Path("out")
out_dir.mkdir(exist_ok=True)

def slugify(s: str) -> str:
    # keep letters/numbers/_- (works fine with latin; keeps it simple for filenames)
    return re.sub(r"[^A-Za-z0-9_-]+", "", s)[:40] or "site"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for idx, url in enumerate(urls, start=1):
        print(f"Processing: {url}")
        found = {"id": None, "payload": None}

        def handle_request(request):
            if "citadel.menew.ir/api" in request.url:
                post_data = request.post_data
                if post_data and '"operationName":"getEntityItems"' in post_data:
                    try:
                        payload = json.loads(post_data)
                        found["id"] = payload.get("variables", {}).get("id")
                        found["payload"] = payload
                    except Exception:
                        pass

        page.on("request", handle_request)
        page.goto(url, wait_until="networkidle")

        record = {"url": url, "id": found["id"], "api_data": None}

        if found["id"]:
            print(f"  Found ID: {found['id']}")
            payload = {
                "query": """
                query getEntityItems($id: UUID!, $language: String, $flavour: QueryFlavour = VILLAGE) {
                  entity(id: $id, language: $language, flavour: $flavour) {
                    menus {
                      id
                      label
                      slug
                      description
                      isActive
                      categories {
                        id
                        label
                        thumbnail
                        status
                        items {
                          labels { name id url type description }
                          id
                          name
                          thumbnail
                          thumbnailBlurHash
                          description
                          itemMedias { mediaType url }
                          threed { armoUid }
                          shopItem {
                            id
                            isSoldOut
                            shopItemPrice { originalPrice price discountType discountValue }
                            productOptions {
                              id label minimumSelectableChoices maximumSelectableChoices
                              productOptionChoices {
                                id
                                choice {
                                  id isSoldOut
                                  shopItemPrice { price }
                                  item { id name }
                                }
                              }
                              isActive
                            }
                          }
                          itemCategories { category { id status } isBold isHidden }
                        }
                      }
                    }
                  }
                }""",
                "variables": {"id": found["id"], "flavour": "VILLAGE"},
                "operationName": "getEntityItems",
            }
            try:
                r = requests.post(api_endpoint, headers=headers, json=payload, timeout=30)
                record["api_data"] = r.json()
            except Exception as e:
                record["api_data"] = {"error": str(e)}

        results.append(record)

        # --- write per-URL file with iterative, even (zero-padded) name ---
        host = urlparse(url).netloc.split(":")[0]
        base = slugify(host)
        short = (found["id"] or "noid")[:8]
        per_file = out_dir / f"{idx:03d}_{base}_{short}.json"
        per_file.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved: {per_file}")

    browser.close()

# combined file
combined = out_dir / "menus_results_all.json"
combined.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"✅ All data saved to {combined}")

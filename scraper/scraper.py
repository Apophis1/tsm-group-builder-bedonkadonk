import os
import re
import json
from flask import Blueprint, request, jsonify
from playwright.sync_api import sync_playwright

scraper_bp = Blueprint("scraper", __name__)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    try:
        print("Received a request")
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "Missing URL"}), 400

        # Determine game mode from the URL
        if "/classic/" in url:
            mode = "anniversary"
        elif "/cata/" in url:
            mode = "cata"
        elif "/season-of-discovery/" in url:
            mode = "sod"
        elif "/ptr/" in url or "/beta/" in url:
            mode = "retail"
        elif "wowhead.com/items" in url or "/retail/" in url:
            mode = "retail"
        else:
            mode = "classic"

        print("Detected mode:", mode)
        print("Navigating to:", url)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Route blocking *before* navigation
            page.route("**/*", lambda route, req: route.abort() if any(x in req.url for x in ["ads", "doubleclick", "googletagmanager", "gstatic"]) else route.continue_())

            page.goto(url, timeout=90000, wait_until='load')


            if mode == "retail":
                # Evaluate script content directly in browser
                js_data = page.evaluate("""
                () => {
                    for (const script of document.scripts) {
                        if (script.textContent.includes("listviewitems = [")) {
                            return script.textContent;
                        }
                    }
                    return null;
                }
                """)
                if not js_data:
                    return jsonify({"error": "Retail script block not found"}), 404

                match = re.search(r'listviewitems\s*=\s*(\[[^\]]+\])', js_data, re.DOTALL)
                if not match:
                    return jsonify({"error": "Retail item block not matched"}), 404

                items = json.loads(match.group(1))

            else:
                # Classic-based scraping via addData JS block
                content = page.content()
                match = re.search(r'WH\.Gatherer\.addData\([^,]+,\s*[^,]+,\s*({.*?})\);', content, re.DOTALL)
                if not match:
                    return jsonify({"error": "Could not find item data in source"}), 404

                import demjson3
                items_dict = demjson3.decode(match.group(1))
                items = list(items_dict.values())

            # Extract valid item IDs
            item_ids = [
                item.get("id") for item in items
                if isinstance(item.get("id"), int) and 0 < item["id"] < 200000
            ]

            print(f"Mode: {mode}, Item count: {len(item_ids)}")
            return jsonify({"items": {"item_ids": item_ids}})

    except Exception as e:
        print("Scraper error:", str(e))
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
   


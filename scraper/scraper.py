import re
import os
import json5 as json  # json5 allows JavaScript-style parsing
from flask import Blueprint, request, jsonify
from playwright.sync_api import sync_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

scraper_bp = Blueprint("scraper", __name__)

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])
            page = browser.new_page()
            page.route("**/*", lambda route, request: route.abort() if "ads" in request.url else route.continue_())
            print(f"Navigating to: {url}")
            page.goto(url, timeout=45000, wait_until='domcontentloaded')
            content = page.content()
            browser.close()

        # Extract the listviewitems block which shows visible items
        match = re.search(r'listviewitems\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not match:
            print("No match for listviewitems, trying JS evaluation fallback")

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

        if js_data:
            match = re.search(r'listviewitems\s*=\s*(\[.*?\]);', js_data, re.DOTALL)

        if not match:
            print("Still no match for listviewitems after JS evaluation.")
            return jsonify({"error": "Could not find visible items on the page."}), 404


        items = json5.loads(match.group(1))

        item_ids = [
            item.get("id") for item in items
            if isinstance(item, dict) and isinstance(item.get("id"), int) and 0 < item["id"] < 200000
        ]

        print("Visible item count:", len(item_ids))
        return jsonify({"items": {"item_ids": item_ids}})
    
    except Exception as e:
        print("Scraper error:", str(e))
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

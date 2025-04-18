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
            return jsonify({"error": "Could not find listviewitems block in page."}), 500

        listview_block = match.group(1)
        items = json.loads(listview_block)

        # Extract item IDs from visible list
        item_ids = [
            item.get("id") for item in items
            if isinstance(item, dict) and isinstance(item.get("id"), int) and 0 < item["id"]
        ]

        print("Visible item count:", len(item_ids))
        return jsonify({"items": {"item_ids": item_ids}})
    except Exception as e:
        print("Scraper error:", str(e))
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

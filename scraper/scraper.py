from flask import jsonify
import os
import re
import json
from flask import Blueprint, request, jsonify

scraper_bp = Blueprint("scraper", __name__)

from playwright.sync_api import sync_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    try:
        print("Received a request", flush=True)
        url = request.json.get("url")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                print("Navigating to:", url,flush=True)
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as nav_err:
                print("Navigation timeout or error:", nav_err, flush=True)
                return jsonify({"error": "Page load failed or timed out."}), 504


            content = page.content()

        match = re.search(r'listviewitems\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not match:
            print("No match for listviewitems",flush=True)
            return jsonify({"error": "Could not find visible items on the page."}), 404

        items = json.loads(match.group(1))

        item_ids = [
            item.get("id") for item in items
            if isinstance(item.get("id"), int) and 0 < item["id"] < 200000
        ]

        print(f"Item IDs ({len(item_ids)}):", item_ids,flush=True)

        return jsonify({"items": {"item_ids": item_ids}})
    
    except Exception as e:
        print("Scraper error:", str(e),flush=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


import re
import json
from flask import Blueprint, request, jsonify
from playwright.sync_api import sync_playwright

scraper_bp = Blueprint("scraper", __name__)

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            print(f"Navigating to: {url}")
            page.goto(url, timeout=45000, wait_until='load')
            content = page.content()
            browser.close()

        # Extract the WH.Gatherer.addData block
        match = re.search(r'WH\.Gatherer\.addData\([^,]+,\s*[^,]+,\s*({.*?})\);', content, re.DOTALL)
        if not match:
            return jsonify({"error": "Could not find item data in page."}), 500

        item_data_block = match.group(1)

        # Match item IDs which are top-level keys in the object
        item_ids = re.findall(r'"(\d+)":\s*{', item_data_block)

        # Convert and filter valid item IDs
        item_ids = [
            int(item_id) for item_id in item_ids
            if item_id.isdigit() and item_id != "0"
        ]
        size = len(item_ids)
        print("Number of item IDs:", size)

        return jsonify({"items": {"item_ids": item_ids}})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

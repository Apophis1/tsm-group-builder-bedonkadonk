import re
import json5 as json  
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
        print("Received a request")
        with sync_playwright() as p:
            with p.chromium.launch(headless=True) as browser:
                print("Opening Browser")
                page = browser.new_page()
                print("Navigating to: ", url)
                page.goto(url, timeout=45000, wait_until='load')
                content = page.content()

        # Extract the listviewitems block which shows visible items
        match = re.search(r'listviewitems\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not match:
            return jsonify({"error": "Could not find listviewitems block in page."}), 500

        items = json.loads(match.group(1))

        # Extract item IDs from visible list
        item_ids = [
            item.get("id") for item in items
            # Instead of filtering IDs arbitrarily:
	        if isinstance(item.get("id"), int) and 0 < item["id"] < 200000
        ]


        print("Visible item count:", len(item_ids))
        
        return jsonify({
            "items": {
                "item_ids": item_ids
            }
        })
    
    except Exception as e:
        print("Scraper error:", str(e))
    return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

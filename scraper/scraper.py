from flask import jsonify
import os
import re
import json5 as json
from flask import Blueprint, request, jsonify

scraper_bp = Blueprint("scraper", __name__)

from playwright.sync_api import sync_playwright

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    try:
        print("Received a request", flush=True)
        url = request.json.get("url")
        if "classic" in url:
            mode = "anniversary"
        elif "cata" in url:
            mode = "cata"
        else:
            mode = "retail"


        print("Detected mode:", mode, flush=True)


        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                print("Navigating to:", url,flush=True)
                page.goto(url, timeout=timeout_ms, wait_until='load')
            except Exception as nav_err:
                print("Navigation timeout or error:", nav_err, flush=True)
                return jsonify({"error": "Page load failed or timed out."}), 504

            content = page.content()

        match = re.search(r'listviewitems\s*=\s*(\[.*?\]);', content, re.DOTALL)
        if not match:
            print("No match for listviewitems",flush=True)
            return jsonify({"error": "Could not find visible items on the page."}), 404

        try:
            items = json.loads(match.group(1))
        except Exception as decode_err:
            print("JSON decode failed:", str(decode_err), flush=True)
            return jsonify({"error": "Item data could not be decoded. This may be a malformed or massive page."}), 500


        def is_valid_item(item, mode):
            item_id = item.get("id")

            if not isinstance(item_id, int):
                return False

            if mode in ["classic", "sod", "anniversary"]:
                return 0 < item_id

            if mode == "retail":
                return item.get("hidden") is not True and item.get("flags2") != 0x800000

            return False

        item_ids = [item["id"] for item in items if is_valid_item(item, mode)]

        print(f"Mode: {mode}, Item count: {len(item_ids)}", flush=True)

        return jsonify({"items": {"item_ids": item_ids}})
    
    except Exception as e:
        print("Scraper error:", str(e),flush=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


import os
import re
import json
import json5
from flask import Blueprint, request, jsonify
from playwright.sync_api import sync_playwright

scraper_bp = Blueprint("scraper", __name__)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    try:
        print("Received a request", flush=True)
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "Missing URL"}), 400

        # Detect realm mode
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

        print("Detected mode:", mode, flush=True)
        print("Navigating to:", url, flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Block ads & tracking
            page.route("**/*", lambda route, req: route.abort() if any(x in req.url for x in ["ads", "googletag", "gstatic", "doubleclick"]) else route.continue_())

            page.goto(url, timeout=90000, wait_until="load")

            if mode == "retail":
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
                    print("Retail script block not found", flush=True)
                    return jsonify({"error": "Retail script block not found"}), 404

                match = re.search(r'listviewitems\s*=\s*(\[[\s\S]*?\])\s*;', js_data)
                if not match:
                    print("Retail item array not matched", flush=True)
                    return jsonify({"error": "Retail item array not matched"}), 404

                items = json.loads(match.group(1))

            else:
                content = page.content()
                match = re.search(r'listviewitems\s*=\s*(\[[\s\S]*?\])\s*;', content)
                if not match:
                    print("Classic listviewitems block not found", flush=True)
                    return jsonify({"error": "Could not find listviewitems in HTML"}), 404

            items = json5.loads(match.group(1))


            # Filter item IDs
            item_ids = [
                item.get("id") for item in items
                if isinstance(item.get("id"), int) and 0 < item["id"] < 200000
                and not item.get("hidden", False)
                and item.get("available", 1) == 1
            ]


            print(f"Mode: {mode}, Item count: {len(item_ids)}", flush=True)
            return jsonify({"items": {"item_ids": item_ids}})

    except Exception as e:
        print("Scraper error:", str(e), flush=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

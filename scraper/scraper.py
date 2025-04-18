import os
import re
import json5 as json
import asyncio
from flask import Blueprint, request, jsonify
from playwright.async_api import async_playwright

scraper_bp = Blueprint("scraper", __name__)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/ms-playwright"

@scraper_bp.route("/api/scrape", methods=["POST"])
def scrape():
    return asyncio.run(scrape_async())
async def scrape_async():
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

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # 🔐 Define and apply async route blocker
            async def block_ads(route, request):
                try:
                    if any(x in request.url for x in ["ads", "googletag", "gstatic", "doubleclick"]):
                            await route.abort()
                    else:
                        await route.continue_()
                except Exception as e:
                    print(f"Routing error: {type(e).__name__} - {e}", flush=True)

            await page.route("**/*", block_ads)

            await page.goto(url, wait_until='domcontentloaded')
            await page.wait_for_selector(".listview-row", timeout=10000)

            if mode == "retail":
                js_data = await page.evaluate("""
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

                match = re.search(r'listviewitems\s*=\s*(\[[\s\S]*?\])\s*(?:;|\n)', js_data)
                if not match:
                    print("Retail item array not matched", flush=True)
                    return jsonify({"error": "Retail item array not matched"}), 404

                print("Matched JS data (first 500 chars):", match.group(1)[:500], flush=True)

                items = await page.evaluate("""
                    () => typeof listviewitems !== 'undefined' ? listviewitems : []
                """)
            else:
                content = await page.content()
                match = re.search(r'listviewitems\s*=\s*(\[[\s\S]*?\])\s*;', content)
                if not match:
                    print("Classic listviewitems block not found", flush=True)
                    return jsonify({"error": "Could not find listviewitems in HTML"}), 404

                items = json.loads(match.group(1))

            visible_ids = await page.eval_on_selector_all(
                ".listview-row",
                "nodes => nodes.map(n => parseInt(n.dataset.id)).filter(id => !isNaN(id))"
            )

            if mode == "retail":
                item_ids = list({
                    item.get("id") for item in items
                    if isinstance(item.get("id"), int)
                    and not item.get("hidden", False)
                    and item.get("available", 1) == 1
                    and item.get("id") in visible_ids
                })
            else:
                item_ids = list({
                    item.get("id") for item in items
                    if isinstance(item.get("id"), int)
                    and 0 < item["id"] < 200000
                    and not item.get("hidden", False)
                    and item.get("available", 1) == 1
                    and item.get("id") in visible_ids
                })

            item_ids = sorted(item_ids)
            print(f"Mode: {mode}, Item count: {len(item_ids)}", flush=True)
            return jsonify({"items": {"item_ids": item_ids}})

    except Exception as e:
        print("Scraper error:", str(e), flush=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
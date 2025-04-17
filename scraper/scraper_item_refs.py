def scrape_item_ids_from_wowhead(url):
    session = requests.Session()
    response = session.get(url, timeout=10)

    if response.status_code != 200:
        raise Exception(f"Request failed with status code {response.status_code}")

    match = re.search(r'var listviewitems = (\[.*?\]);\n?new Listview', response.text, re.DOTALL)
    if not match:
        raise Exception("Could not find listviewitems in page.")

    js_array_str = match.group(1)
    js_array_str = js_array_str.replace("false", "False").replace("true", "True").replace("null", "None")

    try:
        item_data = ast.literal_eval(js_array_str)
        item_refs = []

        for item in item_data:
            item_id = item.get("id")
            if item_id:
                item_refs.append(f"{item_id}")

        return item_refs

    except Exception as e:
        raise Exception(f"Failed to parse item data: {e}")

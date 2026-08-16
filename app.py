from flask import Flask, jsonify, request
import requests
import json
from pathlib import Path
from urllib.parse import unquote

app = Flask(__name__)
inventory_file_path = Path("data/inventory.py")

product_url = "https://world.openfoodfacts.org/api/v2/product"
search_url = "https://world.openfoodfacts.org/api/v2/search"

headers = {
        "User-Agent": "InventoryManagementSystem/1.0 (contact@example.com)"}

def load_inventory():
    if inventory_file_path.exists():
        content = inventory_file_path.read_text(encoding="utf-8")
        namespace = {}
        try:
            exec(content, namespace)
            inventory = namespace.get("inventory", [])
            return inventory if isinstance(inventory, list) else []
        except Exception as error:
            return []
    return []

def save_inventory(inventory):
    inventory_file_path.parent.mkdir(parents=True, exist_ok=True)
    json_formatted = json.dumps(inventory, indent=4, ensure_ascii=False)
    python_syntax_ready = (
        json_formatted.replace("true", "True")
                    .replace("false", "False")
                    .replace("null", "None")
    )
    
    clean_output = f"inventory = {python_syntax_ready}\n"
    inventory_file_path.write_text(clean_output, encoding="utf-8")

def format_product_data(product_data):
    if not product_data:
        return None
    return {
        "status": 1,
        "product": {
            "product_name": product_data.get("product_name", "Unknown Product"),
            "brands": product_data.get("brands", "Unknown Brand"),
            "ingredients_text": product_data.get("ingredients_text", "No ingredients information available"),
            "quantity": product_data.get("quantity", "Unknown Quantity"),
            "categories": product_data.get("categories", "No categories information available"),
        }
    }

#=========================
#API Route designs
#=========================

1. #GET /inventory - Fetch all items in the inventory
@app.route('/inventory', methods=['GET'])
def fetch_all_items():
    inventory = load_inventory()
    return jsonify({
        "status": "success",
        "data": inventory
    }), 200

2. #GET /inventory/<id> → Fetch a single item using barcode id
@app.route('/inventory/<id>', methods=['GET'])
def fetch_item_by_barcode_id(id):
    inventory = load_inventory()
    #check local inventory first
    local_item = next((item for item in inventory if str(item["barcode"]) == str(id)), None)
    if local_item:
        return jsonify({
            "status": "success",
            "data": local_item
        }), 200
    #fallback to OpenFoodFacts live API if not found in local inventory
    url = f"{product_url}/{id}.json"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            return jsonify({"error": "Product not found"}), 404
        raw_data = response.json()
        formatted_data = format_product_data(raw_data.get("product"))

        if not formatted_data:
            return jsonify({"error": "Barcode not found in OpenFoodFacts"}), 404

        # Return the formatted product data
        return jsonify({
            "status": "success",
            "data": {
                "id": None,
                "barcode": id,
                "product_info": formatted_data
            }
        }), 200
    except requests.RequestException as error:
        return jsonify({"error": f"Connection failed: {error}"}), 500

3. #GET /inventory/<name> → Fetch a single item using product name
@app.route('/inventory/<product_name>', methods=['GET'])
def fetch_item_by_product_name(product_name):

    clean_name_query = unquote(product_name).strip().lower()
    #check local inventory first
    inventory = load_inventory()

    for item in inventory:
        name_a = item.get("product_info", {}).get("product", {}).get("product_name", "")
        name_b = item.get("product", {}).get("product_name", "")
        name_c = item.get("product_name", "")

        combined_search_string = f"{name_a} {name_b} {name_c}".lower()
        if clean_name_query in combined_search_string:
            print(f"Local database match found for '{clean_name_query}' inside inventory.py")
    
        return jsonify({
            "status": "success",
            "data": item
        }), 200
    #Fallback to OpenFoodFacts live API if not found in local inventory
    params = {
        "search_terms": product_name,
        "json": 1,
        "page_size": 1  # Limit to 1 result to enforce fetching a single item
    }
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            fetched_product = response.json().get("products", [])

            if not fetched_product:
                return jsonify({"error": "No product found matching the given name"}), 404

            #target the first product found in the search results
            first_match = fetched_product[0]
            formatted_data = format_product_data(first_match)

            if not formatted_data:
                formatted_data = {
                    "status": 1,
                    "product": {
                        "product_name": first_match.get("product_name", "Unknown Product"),
                        "brands": first_match.get("brands", "Unknown Brand"),
                        "ingredients_text": first_match.get("ingredients_text", "No details available"),
                        "quantity": first_match.get("quantity", "N/A"),
                        "categories": first_match.get("categories", "N/A")
                    }
                }

        # Return the first product found
        return jsonify({
            "status": "success",
            "data": {
                "id": None,
                "barcode": first_match.get("code"),
                "price": 0.0,  # Default price, can be updated later
                "stock_quantity": 0,  # Default stock quantity, can be updated later
                "product_info": formatted_data
            }
        }), 200
    except requests.RequestException as error:
        return jsonify({"error": f"Connection failed: {error}"}), 500
  
4. #POST /inventory - Add a new item to the inventory
@app.route('/inventory', methods=['POST'])
def add_a_new_item():
    body = request.get_json() or {}
    barcode = body.get("barcode")
    product_info = body.get("product_info")

    if not barcode or not product_info:
        return jsonify({"error": "Missing required fields: 'barcode' and 'product_info'"}), 400
    inventory = load_inventory()
    #check if the product already exists in the inventory
    if any(str(item["barcode"]) == str(barcode) for item in inventory):
        return jsonify({"error": f"Product with barcode {barcode} already exists in inventory."}), 400

    next_id = max((item["id"] for item in inventory), default=0) + 1

    inner_product_info = product_info.get("product", {})
    price = inner_product_info.pop("price", 0.0)
    stock_quantity = inner_product_info.pop("stock_quantity", 0)

    new_product = {
        "id": next_id,
        "barcode": barcode,
        "price": float(price),
        "stock_quantity": int(stock_quantity),
        "product_info": product_info
    }

    inventory.append(new_product)
    save_inventory(inventory)
    return jsonify({
        "status": "success",
        "message": "New item added successfully",
        "data": new_product
    }), 201

5. #PATCH /inventory/<id> - Update an existing item in the inventory
@app.route('/inventory/<id>', methods=['PATCH'])
def update_existing_item(id):
    body = request.get_json() or {}
    inventory = load_inventory()
    item_to_update = next((item for item in inventory if str(item["barcode"]) == str(id)), None)
    if not item_to_update:
        return jsonify({"error": f"Item not found"}), 404

    if "price" in body:
        item_to_update["price"] = float(body["price"])
    if "stock_quantity" in body:
        item_to_update["stock_quantity"] = int(body["stock_quantity"])

    save_inventory(inventory)

    return jsonify({
        "status": "success",
        "message": "Item updated successfully",
        "data": item_to_update
    }), 200

6. #DELETE /inventory/<id> - Remove an item from the inventory
@app.route('/inventory/<id>', methods=['DELETE'])
def delete_item(id):
    inventory = load_inventory()

    if not any(str(item["barcode"]) == str(id) for item in inventory):
        return jsonify({"error": "Product not found"}), 404

    updated_inventory = [item for item in inventory if str(item["barcode"]) != str(id)]
    save_inventory(updated_inventory)

    return jsonify({
        "status": "success",
        "message": "Barcode deleted successfully"
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

product_url = "https://world.openfoodfacts.org/api/v2/product"
search_url = "https://world.openfoodfacts.org/api/v2/search"

headers = {
        "User-Agent": "InventoryManagementSystem/1.0 (contact@example.com)"}

def format_product_data(data):
    if not data or data.get("status") != 1:
        return None

    product_data = data.get("product", {})
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
    search_query = request.args.get('q', '').strip()
    if not search_query:
        return jsonify({"error": "Cannot fetch all 4.5M+ items. Please pass a search term via ?q=keyword"}), 400

    params = {
        "search_terms": search_query,
        "json": 1,
        "page_size": 10  #This limits the size of the response to 10 items for demonstration purposes.
    }

    try:
        response = requests.get(search_url, params=params, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Failed to query Open Food Facts Search API"}), response.status_code

        fetched_data = response.json()
        products = [format_product_data(item) for item in fetched_data.get("products", []) if format_product_data(item)]
        return jsonify({"products": products}), 200

    except requests.RequestException as e:
        return jsonify({"error": f"Connection failed: {e}"}), 500

2. #GET /inventory/<id> → Fetch a single item using barcode id
@app.route('/inventory/<id>', methods=['GET'])
def fetch_item_by_barcode_id(id):
    url = f"{product_url}/{id}.json"

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            return jsonify({"error": "Product not found"}), 404
        raw_data = response.json()
        formatted_data = format_product_data(raw_data)

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
    except requests.RequestException as e:
        return jsonify({"error": f"Connection failed: {e}"}), 500

3. #GET /inventory/<name> → Fetch a single item using product name
@app.route('/inventory/<product_name>', methods=['GET'])
def fetch_item_by_product_name(product_name):
    params = {
        "search_terms": product_name,
        "search_tag": "product_name",
        "json": 1,
        "page_size": 1  # Limit to 1 result to enforce fetching a single item
    }
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        fetched_data = response.json().get("products", [])

        if not fetched_data:
            return jsonify({"error": "No product found matching the given name"}), 404

        #target the first product found in the search results
        target_product = fetched_data[0]
        formatted_data = format_product_data(target_product)

        # Return the first product found
        return jsonify({
            "status": "success",
            "data": {
                "id": None,
                "barcode": target_product.get("code"),
                "product_info": formatted_data
            }
        }), 200
    except requests.RequestException as e:
        return jsonify({"error": f"Connection failed: {e}"}), 500
  
4. #POST /inventory - Add a new item to the inventory
@app.route('/inventory', methods=['POST'])
def add_a_new_item():
    body = request.get_json() or {}
    return jsonify({
        "status": "success",
        "message": "New item added successfully",
        "received_data": body
    }), 201

#PATCH /inventory/<id> - Update an existing item in the inventory
@app.route('/inventory/<id>', methods=['PATCH'])
def update_existing_item(id):
    body = request.get_json() or {}
    return jsonify({
        "status": "success",
        "message": f"Item with ID {id} updated successfully",
        "updated_data": body
    }), 200

#DELETE /inventory/<id> - Remove an item from the inventory
@app.route('/inventory/<id>', methods=['DELETE'])
def delete_item(id):
    return jsonify({
        "status": "success",
        "message": f"Item with ID {id} deleted successfully"
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
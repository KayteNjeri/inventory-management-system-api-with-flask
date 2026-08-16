import requests
import json
from pathlib import Path
import pprint
from pprint import pformat

BASE_URL = "https://world.openfoodfacts.org/"

def fetch_products_by_barcode(barcode):
    url = f"{BASE_URL}api/v2/product/{barcode}.json"

    headers = {
        "User-Agent": "InventoryManagementSystem/1.0 (contact@example.com)"}

    try:
        # send the HHTP GET request to the OpenFoodFacts API
        response = requests.get(url, headers=headers)

        #check if the request was successful
        if response.status_code == 200:    
            data = response.json()

            #OPenFoodFacts API returns a status of 1 if the product is found
            if data.get("status") == 1:
                product_data = data["product"]

            #Extract the useful data elements
                product_info = {
                    "status": 1,
                    "product": {
                        "product_name": product_data.get("product_name", "Unknown Product"),
                        "brands": product_data.get("brands", "Unknown Brand"),
                        "ingredients_text": product_data.get("ingredients_text", "No ingredients information available"),
                        "quantity": product_data.get("quantity", "Unknown Quantity"),
                        "categories": product_data.get("categories", "No categories information available"),
                    }
                }
                return product_info
            return None
        else:
            print(f"API Error : {response.status_code}")
            return None
    
    except requests.RequestException as error:
        print(f"Connection failed: {error}")
        return None

def save_product_info_to_inventory(product, barcode):
    inventory_file = Path("data/inventory.py")

    inventory_file.parent.mkdir(parents=True, exist_ok=True)
    
    #Read existing inventory data
    if inventory_file.exists():
        content = inventory_file.read_text(encoding="utf-8")

        #get the existing inventory list
        namespace = {}
        try:
            exec(content, namespace)
            inventory = namespace.get("inventory", [])
            if not isinstance(inventory, list):
                inventory = []
        except Exception:
            inventory = []
    else:
        inventory = []

    
    #Generate the next id
    if inventory:
        next_id = max(item["id"] for item in inventory) + 1
    else:
        next_id = 1

    #Create a new product entry
    new_product = {
        "id": next_id,
        "barcode": barcode,
        "product_info": product
    }
    inventory.append(new_product)

    json_formatted = json.dumps(inventory, indent=4, ensure_ascii=False)
    python_syntax_ready = (
        json_formatted.replace("true", "True")
                      .replace("false", "False")
                      .replace("null", "None")
    )

    clean_output = f"inventory = {python_syntax_ready}\n"
    #Write updated inventory back to inventory.py
    inventory_file.write_text(clean_output, encoding="utf-8")
    print(f"Product saved successfully with ID {next_id}")


if __name__ == "__main__":
    test_barcode = "7622210449283"
    product = fetch_products_by_barcode(test_barcode)
    if product:
        save_product_info_to_inventory(product, test_barcode)
    else:
        print("Product was not saved.")
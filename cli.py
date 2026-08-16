import sys
import requests
import json

API_BASE_URL = "http://127.0.0.1:5000"

def display_banner():
    banner = """
    ==========================================
    Inventory Management System - CLI Tool
    ==========================================
    """
    print(banner)

def display_menu():
    menu = """
    Please choose an option:
    1. View all items in the inventory
    2. Fetch for a single product by barcode
    3. Fetch for a single product by name
    4. Add a new item to the inventory
    5. Update an existing item in the inventory
    6. Delete an item from the inventory
    7. Exit the program
    """
    print(menu)

def get_user_choice():
    while True:
        try:
            choice = int(input("Enter your choice (1-7): "))
            if 1 <= choice <= 7:
                return choice
            else:
                print("Invalid choice. Please enter a number between 1 and 7.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

#View all items in the inventory
def view_all_items():
    try:
        response = requests.get(f"{API_BASE_URL}/inventory")
        if response.status_code == 200:
            items = response.json().get("data", [])
            if not items:
                print("Inventory is empty.")
            else:
                for item in items:
                    prod_data = item.get("product_info", {}).get("product", {})
                    name = prod_data.get("product_name", "Unknown Product")

                    print(f"ID: {item['id']} | Barcode: {item['barcode']} | Product Name: {name}")

        else:
            print(f"Error fetching inventory: {response.status_code}")
    except requests.RequestException as error:
        print(f"Connection failed: Is your app.py server running? {e}")

#view a single item by barcode
def view_item_by_barcode():
    barcode = input("Enter the barcode of the product: ").strip()
    try:
        response = requests.get(f"{API_BASE_URL}/inventory/{barcode}")
        if response.status_code == 200:
            item = response.json().get("data", {})
            prod = item.get("product_info", {}).get("product", {})
            print(f"\nBarcode: {item['barcode']} | Price: ${item.get('price', 0.0):.2f} | Stock: {item.get('stock_quantity', 0)}")
            print(f"Product Name: {prod.get('product_name')}\nBrands: {prod.get('brands')}")
        else:
            print(f"Error fetching product: {response.status_code}")
    except requests.RequestException as error:
        print(f"Connection failed: {error}")

#view a single item by product name
def view_item_by_name():
    product_name = input("Enter the name of the product: ").strip()
    try:
        response = requests.get(f"{API_BASE_URL}/inventory/{product_name}")
        if response.status_code == 200:
            item = response.json().get("data", {})
            prod = item.get("product_info", {}).get("product", {})
            print(f"\n[Match Found] Barcode: {item['barcode']}")
            print(f"Product Name: {prod.get('product_name')}\nBrands: {prod.get('brands')}")
        else:
            print(f"Error fetching product: {response.status_code}")
    except requests.RequestException as error:
        print(f"Connection failed: {error}")

#add a new item to the inventory
def add_new_item():
    barcode = input("Enter the barcode of the new product: ").strip()
    try:
        response = requests.get(f"{API_BASE_URL}/inventory/{barcode}")
        if response.status_code == 200:
            print("Product already exists in the inventory.")
            return
        elif response.status_code == 404:
            # Product not found, proceed to add
            product_name = input("Enter the product name: ")
            brands = input("Enter the brands (comma-separated): ")
            ingredients_text = input("Enter the ingredients text: ")
            quantity = input("Enter the quantity: ")
            categories = input("Enter the categories (comma-separated): ")
            price = input("Enter the price: ").strip() or "0.0"
            stock_quantity = input("Enter the stock quantity: ").strip() or "0"

            payload = {
                "barcode": barcode,
                "product_info": {
                    "status": 1,
                    "product":{
                        "product_name": product_name,
                        "brands": brands,
                        "ingredients_text": ingredients_text,
                        "quantity": quantity,
                        "categories": categories,
                        "price": float(price),
                        "stock_quantity": int(stock_quantity)
                    }  
                }
            }

            post_response = requests.post(f"{API_BASE_URL}/inventory", json=payload)
            if post_response.status_code == 201:
                print("Product added successfully.")
            else:
                print(f"Error adding product: {post_response.status_code}")
        else:
            print(f"Error checking product existence: {response.status_code}")
    except requests.RequestException as error:
        print(f"Connection failed: {error}")

#update the price or stock level of an existing item in the inventory
def update_item():
    barcode = input("Enter the barcode of the product to update: ").strip()
    price = input("Enter new price (leave blank to skip): ").strip()
    stock = input("Enter new stock level (leave blank to skip): ").strip()

    payload = {}
    if price: payload["price"] = float(price)
    if stock: payload["stock_quantity"] = int(stock)

    try:
        response = requests.get(f"{API_BASE_URL}/inventory/{barcode}", json=payload)
        if response.status_code == 200:
            print("Product updated successfully")

        else:
            print("Product not found.")
               
    except requests.RequestException as error:
        print(f"Connection failed: {error}")

#delete an item from the inventory
def delete_item_from_inventory():
    barcode = input("Enter the barcode of the product to delete: ").strip()
    try:
        response = requests.delete(f"{API_BASE_URL}/inventory/{barcode}")
        if response.status_code == 200:
            print("Product deleted successfully.")
        else:
            print("Product not found.")
    except requests.RequestException as error:
        print(f"Connection failed: {error}")

def main():
    display_banner()
    while True:
        display_menu()
        choice = get_user_choice()

        if choice == 1:
            view_all_items()
        elif choice == 2:
            view_item_by_barcode()
        elif choice == 3:
            view_item_by_name()
        elif choice == 4:
            add_new_item()
        elif choice == 5:
            update_item()
        elif choice == 6:
            delete_item_from_inventory()
        elif choice == 7:
            print("Exiting the program. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Choose a digit between 1 and 7.")

if __name__ == "__main__":
    main()
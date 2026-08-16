import pytest
from unittest.mock import patch
import app


@pytest.fixture
def client():
    app.app.config["TESTING"] = True

    with app.app.test_client() as client:
        yield client

# GET /inventory
@patch("app.load_inventory")
def test_get_all_inventory(mock_load_inventory, client):
    mock_load_inventory.return_value = [
        {
            "id": 2,
            "barcode": "737628064502",
            "price": 0.0,
            "stock_quantity": 0,
            "product_info": {
                "status": 1,
                "product": {
                    "product_name": "Thai peanut noodle kit",
                    "brands": "Simply Asia, Thai Kitchen"
                }
            }
        }
    ]

    response = client.get("/inventory")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["barcode"] == "737628064502"

    mock_load_inventory.assert_called_once()

# GET /inventory/<id>
@patch("app.load_inventory")
def test_get_item_by_barcode_from_local_inventory(
    mock_load_inventory,
    client
):
    mock_load_inventory.return_value = [
        {
            "id": 2,
            "barcode": "737628064502",
            "price": 10.0,
            "stock_quantity": 5,
            "product_info": {
                "status": 1,
                "product": {
                    "product_name": "Thai peanut noodle kit",
                    "brands": "Simply Asia, Thai Kitchen"
                }
            }
        }
    ]

    response = client.get("/inventory/737628064502")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["barcode"] == "737628064502"
    assert data["data"]["price"] == 10.0
    assert data["data"]["stock_quantity"] == 5

    mock_load_inventory.assert_called_once()

#GET /inventory/<id> - External API
@patch("app.requests.get")
@patch("app.load_inventory")
def test_get_item_by_barcode_from_openfoodfacts(
    mock_load_inventory,
    mock_requests_get,
    client
):
    # Product does not exist locally
    mock_load_inventory.return_value = []

    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Thai peanut noodle kit",
            "brands": "Simply Asia, Thai Kitchen",
            "ingredients_text": "Rice noodles, peanut, sugar, salt",
            "quantity": "155 g",
            "categories": "Noodles, Rice Noodles"
        }
    }

    response = client.get("/inventory/737628064502")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["barcode"] == "737628064502"

    product = data["data"]["product_info"]["product"]
    assert product["product_name"] == "Thai peanut noodle kit"
    assert product["brands"] == "Simply Asia, Thai Kitchen"

    mock_requests_get.assert_called_once()

# POST /inventory
@patch("app.save_inventory")
@patch("app.load_inventory")
def test_add_new_inventory_item(
    mock_load_inventory,
    mock_save_inventory,
    client
):
    mock_load_inventory.return_value = []

    payload = {
        "barcode": "123456789012",
        "product_info": {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "brands": "Test Brand",
                "ingredients_text": "Water, sugar",
                "quantity": "500 g",
                "categories": "Food",
                "price": 25.50,
                "stock_quantity": 10
            }
        }
    }

    response = client.post(
        "/inventory",
        json=payload
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["status"] == "success"
    assert data["message"] == "New item added successfully"

    new_product = data["data"]

    assert new_product["id"] == 1
    assert new_product["barcode"] == "123456789012"
    assert new_product["price"] == 25.50
    assert new_product["stock_quantity"] == 10

    mock_save_inventory.assert_called_once()

#POST /inventory - Missing fields
@patch("app.load_inventory")
def test_add_inventory_missing_fields(
    mock_load_inventory,
    client
):
    mock_load_inventory.return_value = []

    payload = {
        "barcode": "123456789012"
    }

    response = client.post(
        "/inventory",
        json=payload
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "Missing required fields" in data["error"]

# PATCH /inventory/<id>
@patch("app.save_inventory")
@patch("app.load_inventory")
def test_update_inventory_item(
    mock_load_inventory,
    mock_save_inventory,
    client
):
    inventory = [
        {
            "id": 2,
            "barcode": "737628064502",
            "price": 10.0,
            "stock_quantity": 5,
            "product_info": {
                "status": 1,
                "product": {
                    "product_name": "Thai peanut noodle kit"
                }
            }
        }
    ]

    mock_load_inventory.return_value = inventory

    payload = {
        "price": 15.50,
        "stock_quantity": 20
    }

    response = client.patch(
        "/inventory/737628064502",
        json=payload
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["price"] == 15.50
    assert data["data"]["stock_quantity"] == 20

    mock_save_inventory.assert_called_once()

# DELETE /inventory/<id>
@patch("app.save_inventory")
@patch("app.load_inventory")
def test_delete_inventory_item(
    mock_load_inventory,
    mock_save_inventory,
    client
):
    inventory = [
        {
            "id": 2,
            "barcode": "737628064502",
            "price": 10.0,
            "stock_quantity": 5,
            "product_info": {}
        },
        {
            "id": 3,
            "barcode": "123456789012",
            "price": 20.0,
            "stock_quantity": 10,
            "product_info": {}
        }
    ]

    mock_load_inventory.return_value = inventory

    response = client.delete(
        "/inventory/737628064502"
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "success"
    assert data["message"] == "Barcode deleted successfully"

    mock_save_inventory.assert_called_once()

    saved_inventory = mock_save_inventory.call_args[0][0]

    assert len(saved_inventory) == 1
    assert saved_inventory[0]["barcode"] == "123456789012"
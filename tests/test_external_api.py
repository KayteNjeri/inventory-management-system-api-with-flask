from unittest.mock import patch, Mock
import app
import requests

@patch("app.requests.get")
@patch("app.load_inventory")
def test_openfoodfacts_product_request(
    mock_load_inventory,
    mock_get
):

    # Make sure the product is not found locally
    mock_load_inventory.return_value = []

    mock_response = Mock()
    mock_response.status_code = 200

    mock_response.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Milk",
            "brands": "Test Brand",
            "ingredients_text": "Milk",
            "quantity": "1 L",
            "categories": "Dairy products"
        }
    }

    mock_get.return_value = mock_response

    client = app.app.test_client()

    response = client.get(
        "/inventory/3274080005003"
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["barcode"] == "3274080005003"

    product = data["data"]["product_info"]["product"]

    assert product["product_name"] == "Milk"
    assert product["brands"] == "Test Brand"

    mock_load_inventory.assert_called_once()
    mock_get.assert_called_once()



def test_openfoodfacts_product_not_found():

    fake_response = Mock()
    fake_response.status_code = 404

    with patch(
        "app.requests.get",
        return_value=fake_response
    ) as mock_get:

        response = app.app.test_client().get(
            "/inventory/999999999999"
        )

        assert response.status_code == 404

        data = response.get_json()

        assert data["error"] == "Product not found"

        mock_get.assert_called_once()


@patch("app.requests.get")
@patch("app.load_inventory")
def test_openfoodfacts_connection_error(
    mock_load_inventory,
    mock_get
):

    # Force the application to go to OpenFoodFacts
    mock_load_inventory.return_value = []

    # Simulate an external API connection failure
    mock_get.side_effect = requests.RequestException(
        "Connection failed"
    )

    client = app.app.test_client()

    response = client.get(
        "/inventory/3274080005003"
    )

    assert response.status_code == 500

    data = response.get_json()

    assert "Connection failed" in data["error"]

    mock_load_inventory.assert_called_once()
    mock_get.assert_called_once()
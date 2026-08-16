from unittest.mock import patch, Mock
import cli

# View all inventory
@patch("cli.requests.get")
def test_view_all_items(mock_get):

    mock_response = Mock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "status": "success",
        "data": [
            {
                "id": 2,
                "barcode": "737628064502",
                "price": 0.0,
                "stock_quantity": 0,
                "product_info": {
                    "product": {
                        "product_name": "Thai peanut noodle kit",
                        "brands": "Simply Asia"
                    }
                }
            }
        ]
    }

    mock_get.return_value = mock_response

    with patch("builtins.print") as mock_print:
        cli.view_all_items()

    mock_get.assert_called_once_with(
        "http://127.0.0.1:5000/inventory"
    )

    mock_print.assert_any_call(
        "ID: 2 | Barcode: 737628064502 | Product Name: Thai peanut noodle kit"
    )

# View item by barcode
@patch("cli.requests.get")
@patch("builtins.input", return_value="737628064502")
def test_view_item_by_barcode(mock_input, mock_get):

    mock_response = Mock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "id": 2,
            "barcode": "737628064502",
            "price": 10.0,
            "stock_quantity": 5,
            "product_info": {
                "product": {
                    "product_name": "Thai peanut noodle kit",
                    "brands": "Simply Asia"
                }
            }
        }
    }

    mock_get.return_value = mock_response

    with patch("builtins.print") as mock_print:

        cli.view_item_by_barcode()

    mock_get.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/737628064502"
    )

    mock_print.assert_any_call(
        "\nBarcode: 737628064502 | Price: $10.00 | Stock: 5"
    )

# View item by name
@patch("cli.requests.get")
@patch(
    "builtins.input",
    return_value="Thai peanut noodle kit"
)
def test_view_item_by_name(mock_input, mock_get):

    mock_response = Mock()

    mock_response.status_code = 200

    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "barcode": "737628064502",
            "product_info": {
                "product": {
                    "product_name": "Thai peanut noodle kit",
                    "brands": "Simply Asia"
                }
            }
        }
    }

    mock_get.return_value = mock_response

    with patch("builtins.print") as mock_print:

        cli.view_item_by_name()

    mock_get.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/name/Thai peanut noodle kit"
    )

    mock_print.assert_any_call(
        "\n[Match Found] Barcode: 737628064502"
    )

# Add new item
@patch("cli.requests.post")
@patch("cli.requests.get")
@patch(
    "builtins.input",
    side_effect=[
        "123456789012",
        "Test Product",
        "Test Brand",
        "Water, sugar",
        "500 g",
        "Food",
        "25.50",
        "10"
    ]
)
def test_add_new_item(
    mock_input,
    mock_get,
    mock_post
):

    # First GET checks whether barcode already exists
    get_response = Mock()
    get_response.status_code = 404

    mock_get.return_value = get_response

    # POST creates the product
    post_response = Mock()
    post_response.status_code = 201

    mock_post.return_value = post_response

    with patch("builtins.print") as mock_print:

        cli.add_new_item()
    mock_get.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/123456789012"
    )

    mock_post.assert_called_once()

    request_payload = mock_post.call_args.kwargs["json"]

    assert request_payload["barcode"] == "123456789012"

    product = request_payload["product_info"]["product"]

    assert product["product_name"] == "Test Product"
    assert product["brands"] == "Test Brand"
    assert product["price"] == 25.50
    assert product["stock_quantity"] == 10

    mock_print.assert_any_call(
        "Product added successfully."
    )

# Update item
def test_update_item():
    mock_response = Mock()
    mock_response.status_code = 200

    with patch("cli.requests.patch", return_value=mock_response) as mock_patch:
        with patch(
            "builtins.input",
            side_effect=[
                "737628064502",
                "15.50",
                "20"
            ]
        ):
            with patch("builtins.print") as mock_print:

                cli.update_item()

    mock_patch.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/737628064502",
        json={
            "price": 15.50,
            "stock_quantity": 20
        }
    )

    mock_print.assert_called_with(
        "Product updated successfully."
    )
    
# Delete item
@patch("cli.requests.delete")
@patch(
    "builtins.input",
    return_value="737628064502"
)
def test_delete_item(
    mock_input,
    mock_delete
):

    mock_response = Mock()
    mock_response.status_code = 200

    mock_delete.return_value = mock_response

    with patch("builtins.print") as mock_print:

        cli.delete_item_from_inventory()

    mock_delete.assert_called_once_with(
        "http://127.0.0.1:5000/inventory/737628064502"
    )

    mock_print.assert_any_call(
        "Product deleted successfully."
    )
import requests
import pytest

service_a = 'http://localhost:5000'
service_b = 'http://localhost:5001'
service_c = 'http://localhost:5002'

@pytest.fixture(scope="function")
def setup_order():
    # Setup a sample order
    url = f'{service_a}/order'
    order_data = {
        "pizza_type": "Thin Crust",
        "toppings": ["Extra Cheese", "Tuna", "Olives"],
        "quantity": 2,
        "price": 50
    }
    response = requests.post(url, json=order_data)
    assert response.status_code == 202
    order_id = response.json()["order_id"]

    # Accept the order so it gets processed into MongoDB
    accept_url = f'{service_a}/accept_order/{order_id}'
    response = requests.post(accept_url)
    assert response.status_code == 200
    assert response.json()["message"] == "Order processed"

    yield order_id

    # Teardown: Delete the order after test completion
    delete_url = f'{service_b}/order/{order_id}'
    response = requests.delete(delete_url)
    assert response.status_code == 200 or response.status_code == 404

def test_prepare_order():
    url = f'{service_a}/order'
    order_data = {
        "pizza_type": "Thin Crust",
        "toppings": ["Extra Cheese", "Tuna", "Olives"],
        "quantity": 2,
        "price": 50
    }
    response = requests.post(url, json=order_data)
    assert response.status_code == 202
    assert "order_id" in response.json()

def test_accept_order(setup_order):
    order_id = setup_order
    url = f'{service_b}/order/{order_id}'
    response = requests.get(url)
    assert response.status_code == 200
    assert response.json()["order_id"] == order_id

def test_accept_all_orders(setup_order):
    url = f'{service_a}/accept_all'
    response = requests.post(url)
    assert response.status_code == 200
    assert "orders processed" in response.json()["message"] or "No orders to process" in response.json()["message"]

def test_get_order(setup_order):
    order_id = setup_order
    url = f'{service_b}/order/{order_id}'
    response = requests.get(url)
    assert response.status_code == 200
    assert response.json()["order_id"] == order_id

def test_update_order(setup_order):
    order_id = setup_order
    url = f'{service_b}/order/{order_id}'
    updated_data = {
        "pizza_type": "Thin Crust",
        "toppings": ["Extra Cheese", "Tuna", "Olives", "Mushrooms"],
        "quantity": 3,
        "price": 55
    }
    response = requests.put(url, json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Order updated"
    assert response.json()["details"]["order_id"] == order_id
    assert response.json()["details"]["toppings"] == updated_data["toppings"]
    assert response.json()["details"]["quantity"] == updated_data["quantity"]

def test_get_all_orders(setup_order):
    url = f'{service_b}/orders'
    response = requests.get(url)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_delete_order(setup_order):
    order_id = setup_order
    url = f'{service_b}/order/{order_id}'
    response = requests.delete(url)
    assert response.status_code == 200
    assert response.json()["message"] == "Order deleted"
    assert response.json()["order_id"] == order_id

def test_show_pizza_menu():
    url = f'{service_c}/pizzamenu'
    response = requests.get(url)
    assert response.status_code == 200
    menu = response.json()
    assert isinstance(menu, dict), f"Expected a dict, got {type(menu)}"

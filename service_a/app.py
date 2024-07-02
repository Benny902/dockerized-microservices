from flask import Flask, request, jsonify
import requests
import pika
import json
import time

app = Flask(__name__)

# URLs of the current additional services
SERVICE_URLS = {
    'B': 'http://service_b:5001',
    'C': 'http://service_c:5002'
}

RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_QUEUE = 'order_queue'

# initialize order_id_counter in global scope
order_id_counter = 0

# function to generate unique order_id
def generate_order_id():
    global order_id_counter
    order_id_counter += 1
    return order_id_counter

# function to forward requests to a service
def forward_to_service(service, endpoint, method='GET', json_data=None):
    url = SERVICE_URLS.get(service) + endpoint
    try:
        response = requests.request(method=method, url=url, json=json_data)
        response.raise_for_status()
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# endpoint to place an order (forwarded to RabbitMQ)
@app.route('/order', methods=['POST'])
def place_order():
    order_data = request.json
    order_id = generate_order_id() 
    order_data['order_id'] = order_id
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        channel.basic_publish(exchange='',
                              routing_key=RABBITMQ_QUEUE,
                              body=json.dumps(order_data))
        connection.close()
        return jsonify({"message": "Order placed in queue", "order_id": order_id}), 202
    except pika.exceptions.AMQPConnectionError as e:
        return jsonify({"error": "RabbitMQ connection failed"}), 500

# endpoint to accept all orders from RabbitMQ and save them to MongoDB (forwarded to service B)
@app.route('/accept_all', methods=['POST'])
def accept_all_orders():
    return forward_to_service('B', '/accept_all', method='POST')

# endpoint to accept a specific order from RabbitMQ and save it to MongoDB (forwarded to service B)
@app.route('/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    return forward_to_service('B', f'/accept_order/{order_id}', method='POST')

# endpoint to get an order by order_id (forwarded to service B)
@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    return forward_to_service('B', f'/order/{order_id}', method='GET')

# endpoint to update an order by order_id (forwarded to service B)
@app.route('/order/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order_data = request.json
    return forward_to_service('B', f'/order/{order_id}', method='PUT', json_data=order_data)

# endpoint to delete an order by order_id (forwarded to service B)
@app.route('/order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    return forward_to_service('B', f'/order/{order_id}', method='DELETE')

# endpoint to get all orders (forwarded to service B)
@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        response, status_code = forward_to_service('B', '/orders', method='GET')
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# endpoint to get pizza menu (forwarded to service C)
@app.route('/pizzamenu', methods=['GET'])
def get_menu():
    return forward_to_service('C', '/pizzamenu', method='GET')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, jsonify, request
from pymongo import MongoClient
import pika
import json
import threading

app = Flask(__name__)

client = MongoClient('db:27017')
db = client.get_database('pizza')
orders = db.orders

RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_QUEUE = 'order_queue'

# convert ObjectId to string for JSON serialization
def serialize_order(order):
    if '_id' in order:
        order['_id'] = str(order['_id'])
    return order

# consumes all orders from RabbitMQ and saves them to MongoDB
@app.route('/accept_all', methods=['POST'])
def accept_all():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)

        processed_orders = []
        method, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        
        while method:
            try:
                order_data = json.loads(body)
                result = orders.insert_one(order_data)
                order_data['_id'] = str(result.inserted_id)  # Convert ObjectId to string
                processed_orders.append(order_data)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Failed to process message: {e}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            method, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        
        if processed_orders:
            return jsonify({
                "message": f"{len(processed_orders)} orders processed",
                "orders": processed_orders
            })
        else:
            return jsonify({"message": "No orders to process"}), 200

    except Exception as e:
        print(f"Error during accept_all processing: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# consumes a specific order from RabbitMQ and saves it to MongoDB
@app.route('/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        
        # limit the number of unacknowledged messages fetched at once
        channel.basic_qos(prefetch_count=1)
        
        method, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        found_order = False
        
        while method:
            order_data = json.loads(body)
            
            if order_data.get('order_id') == order_id:
                result = orders.insert_one(order_data)
                order_data['_id'] = str(result.inserted_id)  # Convert ObjectId to string
                channel.basic_ack(delivery_tag=method.delivery_tag)
                found_order = True
                break  # exit loop once order is processed
                
            # continue fetching next message
            method, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        
        if found_order:
            return jsonify({
                "message": "Order processed",
                "order_id": order_data['order_id'],
                "details": order_data
            })
        else:
            return jsonify({"error": f"Order with order_id {order_id} not found in queue"}), 404

    except Exception as e:
        print(f"Error during accept_order processing: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500



# other endpoints with ObjectId serialization
@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.find_one({"order_id": order_id})
    if order:
        return jsonify(serialize_order(order))
    else:
        return jsonify({"error": "Order not found"}), 404

@app.route('/orders', methods=['GET'])
def get_all_orders():
    all_orders = list(orders.find())
    return jsonify([serialize_order(order) for order in all_orders])

@app.route('/order/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order_data = request.json
    existing_order = orders.find_one({"order_id": order_id})
    if existing_order:
        orders.update_one({"order_id": order_id}, {"$set": order_data})
        updated_order = orders.find_one({"order_id": order_id})
        return jsonify({
            "message": "Order updated",
            "order_id": order_id,
            "details": serialize_order(updated_order)
        })
    else:
        return jsonify({"error": "Order not found"}), 404

@app.route('/order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    existing_order = orders.find_one({"order_id": order_id})
    if existing_order:
        orders.delete_one({"order_id": order_id})
        return jsonify({
            "message": "Order deleted",
            "order_id": order_id,
            "details": serialize_order(existing_order)
        })
    else:
        return jsonify({"error": "Order not found"}), 404

def rabbitmq_consumer():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    def callback(ch, method, properties, body):
        try:
            order_data = json.loads(body)
            result = orders.insert_one(order_data)
            print(f"Order processed and added to database: {order_data['order_id']}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Failed to process message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback)
    print('Waiting for orders...')
    channel.start_consuming()

if __name__ == '__main__':
    threading.Thread(target=rabbitmq_consumer, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, debug=True)

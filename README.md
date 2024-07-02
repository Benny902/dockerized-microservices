# dockerized-microservices

## the goal of this project was to learn and show how three services communicate between each other regardless of their programming language, also including MongoDB as database and intergrating RabbitMQ for managing queues, and finally dockerize the project using docker-compose.

i have created three backend services, a main service (service A) that the user can interact with services B and C.  
service B with python: place_order, get_order, get_all_orders, update_order, delete_order.  
service C with node.js: get_pizza_menu (this service is used for the frontend pizza ordering for dynamic menu populating).  
integrating RabbitMQ for handling POST requests before accepting them into the MongoDB database.  
the orders can be viewed in the rabbitMQ management address: http://localhost:15672/  
implemented two new functions: accept_all and accept_order, that will accept order/s from RabbitMQ queue into the database and will respond with a callback that processing is done.  


## to run the project just type on terminal:  
docker-compose up --build  

thats it!! and it will run all five services: a, b, c, mongodb, and RabbitMQ.  

and to run the integration test: (cd integration_test)  
pytest -v test.py  

i've also included "postman_collection.json" that you can use to test each route individually with the different order numbers as you wish.  

## example usage in postman / swagger / etc:  
the main service (a) http://localhost:5000/ with the following endpoints:  

>POST /order: creates an order and places it in RabbitMQ queue (with a unique order_id created by order_counter)  
POST /accept_order/<int: order_id>: accepts an order by its order_id  
POST /accept_all: accepts all orders from the queue.  
GET /order/<int: order_id>: shows the order with the given order_id (if its accepted).  
PUT /order/<int: order_id>: updates the order with the given order_id (if its accepted).  
DELETE /order/<int: order_id>: deletes the order with the given order_id.  
GET /orders/<int: order_id>: shows all the (accepted) orders.  
GET /pizzamenu: shows the pizza menu.  

for "POST /order" or "PUT /order" you need to include json input, for example:  
{  
  "pizza_type": "Thin Crust",  
  "toppings": "Extra Cheese, Tuna, Olives",  
  "quantity": 2,  
  "price": 100  
}  

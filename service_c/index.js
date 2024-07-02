const express = require('express');
const app = express();
const PORT = process.env.PORT || 5002;


const pizzaMenu = { // pizza menu
    pizzas: [
        { name: 'Classic', price: 50 },
        { name: 'Thin crust', price: 50 },
        { name: 'Mozzarella filling on the edges', price: 60 },
        { name: 'Gluten free', price: 50 }
    ],
    toppings: [
        { name: 'Extra Cheese', price: 5 },
        { name: 'Tomato', price: 5 },
        { name: 'Mozzarella', price: 5 },
        { name: 'Tuna', price: 5 },
        { name: 'Olives', price: 5 },
        { name: 'Onions', price: 5 },
        { name: 'Pineapple', price: 5 }
    ],
    drinks: [
        { name: 'Cola', price: 10 },
        { name: 'Cola Zero', price: 10 },
        { name: 'Fanta', price: 10 },
        { name: 'Sprite', price: 10 },
        { name: 'Water', price: 5 }
    ]
};

// endpoint to get the pizza menu
app.get('/pizzamenu', (req, res) => {
    res.json(pizzaMenu);
});


app.listen(PORT, () => {
    console.log(`Service C is running on port ${PORT}`);
});

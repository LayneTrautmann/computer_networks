# JSON Schema for Client-Ordering HTTP Communication

This document defines the JSON format used for communication between the Streamlit Client and the Flask Ordering Service.

## Grocery Order Request

**Endpoint:** `POST /order/grocery`

```json
{
  "customer_id": "string",
  "order_type": "GROCERY_ORDER",
  "items": {
    "bread": [
      {"name": "white_bread", "quantity": 2},
      {"name": "bagels", "quantity": 6}
    ],
    "dairy": [
      {"name": "milk", "quantity": 1},
      {"name": "cheese", "quantity": 2}
    ],
    "meat": [
      {"name": "chicken", "quantity": 3},
      {"name": "beef", "quantity": 2}
    ],
    "produce": [
      {"name": "tomatoes", "quantity": 5},
      {"name": "apples", "quantity": 8}
    ],
    "party": [
      {"name": "soda", "quantity": 4},
      {"name": "paper_plates", "quantity": 1}
    ]
  }
}
```

**Notes:**
- `customer_id`: Unique identifier for the customer/refrigerator
- `order_type`: Always "GROCERY_ORDER" for grocery orders
- `items`: Categories can be empty arrays `[]` but at least one category must have items
- `quantity`: Integer representing units (or weight units for produce)

---

## Restock Order Request

**Endpoint:** `POST /order/restock`

```json
{
  "supplier_id": "string",
  "order_type": "RESTOCK_ORDER",
  "items": {
    "bread": [
      {"name": "white_bread", "quantity": 50},
      {"name": "bagels", "quantity": 100}
    ],
    "dairy": [
      {"name": "milk", "quantity": 30},
      {"name": "cheese", "quantity": 40}
    ],
    "meat": [
      {"name": "chicken", "quantity": 25},
      {"name": "beef", "quantity": 20}
    ],
    "produce": [
      {"name": "tomatoes", "quantity": 100},
      {"name": "apples", "quantity": 150}
    ],
    "party": [
      {"name": "soda", "quantity": 60},
      {"name": "paper_plates", "quantity": 30}
    ]
  }
}
```

**Notes:**
- `supplier_id`: Unique identifier for the truck/supplier
- `order_type`: Always "RESTOCK_ORDER" for restocking
- Same structure as grocery order but typically larger quantities

---

## Response Format

**Success Response:**

```json
{
  "status": "OK",
  "message": "Order processed successfully",
  "order_id": "string",
  "items_fulfilled": {
    "bread": [
      {"name": "white_bread", "quantity_fulfilled": 2}
    ],
    "dairy": [],
    "meat": [],
    "produce": [],
    "party": []
  },
  "total_price": 25.99
}
```

**Error Response:**

```json
{
  "status": "BAD_REQUEST",
  "message": "Error description here",
  "order_id": null,
  "items_fulfilled": null,
  "total_price": null
}
```

---

## Available Items Per Category

### Bread
- white_bread, wheat_bread, bagels, waffles, croissants, baguette

### Dairy
- milk, cheese, yogurt, butter, cream, eggs

### Meat
- chicken, beef, pork, turkey, fish, lamb

### Produce
- tomatoes, onions, apples, oranges, bananas, lettuce, carrots, potatoes

### Party Supplies
- soda, paper_plates, napkins, cups, balloons, streamers

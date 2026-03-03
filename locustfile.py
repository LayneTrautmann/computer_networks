import random
import string

from locust import HttpUser, between, task

ITEMS = {
    "bread": ["white_bread", "wheat_bread", "bagels", "waffles", "croissants", "baguette"],
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream", "eggs"],
    "meat": ["chicken", "beef", "pork", "turkey", "fish", "lamb"],
    "produce": ["tomatoes", "onions", "apples", "oranges", "bananas", "lettuce", "carrots", "potatoes"],
    "party": ["soda", "paper_plates", "napkins", "cups", "balloons", "streamers"],
}


def random_id(prefix, length=6):
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=length))}"


def random_items(max_quantity):
    """Build a randomized items dict across a random subset of categories."""
    items = {}
    categories = random.sample(list(ITEMS.keys()), k=random.randint(1, len(ITEMS)))
    for category in categories:
        chosen = random.sample(ITEMS[category], k=random.randint(1, len(ITEMS[category])))
        items[category] = [{"name": name, "quantity": random.randint(1, max_quantity)} for name in chosen]
    return items


class RefrigeratorUser(HttpUser):
    """Simulates grocery orders from refrigerators (higher proportion of traffic)."""
    weight = 8
    wait_time = between(1, 3)

    @task
    def place_grocery_order(self):
        payload = {
            "customer_id": random_id("cust"),
            "order_type": "GROCERY_ORDER",
            "items": random_items(max_quantity=5),
        }
        self.client.post("/order/grocery", json=payload)


class TruckUser(HttpUser):
    """Simulates restock orders from delivery trucks."""
    weight = 2
    wait_time = between(1, 3)

    @task
    def place_restock_order(self):
        payload = {
            "supplier_id": random_id("supp"),
            "order_type": "RESTOCK_ORDER",
            "items": random_items(max_quantity=50),
        }
        self.client.post("/order/restock", json=payload)

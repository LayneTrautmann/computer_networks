"""
Locust workload generator for the Grocery Ordering Service.

Traffic mix: ~80% refrigerator (grocery) orders, ~20% truck (restock) orders.

Usage:
  # Web UI mode
  locust -f locustfile.py --host=http://172.16.2.136:30500

  # Headless with CSV export (for tail-latency analysis)
  locust -f locustfile.py --host=http://172.16.2.136:30500 \
      --headless -u 50 -r 5 -t 60s --csv=results

  # Different workload shapes (set LOCUST_SHAPE env var):
  LOCUST_SHAPE=burst locust -f locustfile.py --host=http://...
"""

import os
import random
import string
import math

from locust import HttpUser, between, task, events, LoadTestShape

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


# ── Custom load shapes for different experiments ─────────────────────────────

class SteadyShape(LoadTestShape):
    """Constant load: ramp to target users, hold for duration, then stop.
    Env vars: STEADY_USERS (default 30), STEADY_DURATION (default 120s)."""

    def __init__(self):
        super().__init__()
        self.target_users = int(os.environ.get("STEADY_USERS", "30"))
        self.duration = int(os.environ.get("STEADY_DURATION", "120"))
        self.ramp_rate = max(1, self.target_users // 10)

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.duration:
            return None
        return (self.target_users, self.ramp_rate)


class BurstShape(LoadTestShape):
    """Periodic bursts: low baseline with spikes every interval.
    Env vars: BURST_BASELINE (10), BURST_PEAK (100), BURST_INTERVAL (30s),
              BURST_WIDTH (10s), BURST_DURATION (180s)."""

    def __init__(self):
        super().__init__()
        self.baseline = int(os.environ.get("BURST_BASELINE", "10"))
        self.peak = int(os.environ.get("BURST_PEAK", "100"))
        self.interval = int(os.environ.get("BURST_INTERVAL", "30"))
        self.width = int(os.environ.get("BURST_WIDTH", "10"))
        self.duration = int(os.environ.get("BURST_DURATION", "180"))

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.duration:
            return None
        phase = run_time % self.interval
        users = self.peak if phase < self.width else self.baseline
        return (users, max(5, abs(users - self.baseline) // 2 + 1))


class RampShape(LoadTestShape):
    """Linearly ramping load: 0 -> peak over the duration.
    Env vars: RAMP_PEAK (80), RAMP_DURATION (120s)."""

    def __init__(self):
        super().__init__()
        self.peak = int(os.environ.get("RAMP_PEAK", "80"))
        self.duration = int(os.environ.get("RAMP_DURATION", "120"))

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.duration:
            return None
        users = max(1, int(self.peak * run_time / self.duration))
        return (users, max(1, self.peak // 20))


class SineShape(LoadTestShape):
    """Sinusoidal load oscillation.
    Env vars: SINE_MIN (5), SINE_MAX (60), SINE_PERIOD (60s), SINE_DURATION (180s)."""

    def __init__(self):
        super().__init__()
        self.min_users = int(os.environ.get("SINE_MIN", "5"))
        self.max_users = int(os.environ.get("SINE_MAX", "60"))
        self.period = int(os.environ.get("SINE_PERIOD", "60"))
        self.duration = int(os.environ.get("SINE_DURATION", "180"))

    def tick(self):
        run_time = self.get_run_time()
        if run_time > self.duration:
            return None
        amp = (self.max_users - self.min_users) / 2
        mid = self.min_users + amp
        users = max(1, int(mid + amp * math.sin(2 * math.pi * run_time / self.period)))
        return (users, max(1, int(amp / 5)))


# Select shape based on LOCUST_SHAPE env var.  When unset or "default",
# no custom shape is used and Locust falls back to normal CLI -u/-r behavior.
_SHAPE_MAP = {
    "steady": SteadyShape,
    "burst": BurstShape,
    "ramp": RampShape,
    "sine": SineShape,
}

_selected = os.environ.get("LOCUST_SHAPE", "").lower()
if _selected in _SHAPE_MAP:
    # Dynamically register the chosen shape so Locust picks it up
    globals()["SelectedShape"] = _SHAPE_MAP[_selected]

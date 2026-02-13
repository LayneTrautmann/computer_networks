"""
Analytics Service
Subscribes to ZMQ analytics events published by the Ordering Service.
Tracks total requests, fulfillment outcomes, and per-request latency.
Stores data to CSV for later plotting.
"""

import os
import csv
import json
import signal
import sys
from datetime import datetime

import zmq

# Configuration
ZMQ_ANALYTICS_ADDRESS = os.environ.get("ZMQ_ANALYTICS_ADDRESS", "tcp://*:5557")
ZMQ_ANALYTICS_TOPIC = os.environ.get("ZMQ_ANALYTICS_TOPIC", "analytics")
CSV_OUTPUT_PATH = os.environ.get(
    "ANALYTICS_CSV_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics_data.csv"),
)

# In-memory counters
stats = {
    "total_requests": 0,
    "grocery_orders": 0,
    "restock_orders": 0,
    "ok_count": 0,
    "bad_request_count": 0,
    "total_latency": 0.0,
}


def _init_csv(path):
    """Create CSV with header if it doesn't exist."""
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["timestamp", "order_id", "order_type", "status", "latency_seconds"]
            )


def _append_csv(path, row):
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def _print_summary():
    avg = (
        stats["total_latency"] / stats["total_requests"]
        if stats["total_requests"] > 0
        else 0
    )
    print("\n--- Analytics Summary ---")
    print(f"  Total requests:   {stats['total_requests']}")
    print(f"  Grocery orders:   {stats['grocery_orders']}")
    print(f"  Restock orders:   {stats['restock_orders']}")
    print(f"  OK responses:     {stats['ok_count']}")
    print(f"  BAD_REQUEST:      {stats['bad_request_count']}")
    print(f"  Avg latency:      {avg:.4f}s")
    print("-------------------------\n")


def serve():
    _init_csv(CSV_OUTPUT_PATH)

    context = zmq.Context.instance()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.bind(ZMQ_ANALYTICS_ADDRESS)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, ZMQ_ANALYTICS_TOPIC)

    # Graceful shutdown
    def _shutdown(signum, frame):
        print("\nShutting down Analytics Service...")
        _print_summary()
        sub_socket.close()
        context.term()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print(f"Analytics Service listening on {ZMQ_ANALYTICS_ADDRESS}")
    print(f"Subscribed to topic: {ZMQ_ANALYTICS_TOPIC}")
    print(f"Saving data to: {CSV_OUTPUT_PATH}")

    while True:
        try:
            parts = sub_socket.recv_multipart()
            if len(parts) < 2:
                continue

            payload = json.loads(parts[1].decode("utf-8"))
            order_id = payload.get("order_id", "")
            order_type = payload.get("order_type", "")
            status = payload.get("status", "")
            latency = payload.get("latency_seconds", 0.0)
            timestamp = datetime.now().isoformat()

            # Update counters
            stats["total_requests"] += 1
            stats["total_latency"] += latency
            if order_type == "GROCERY_ORDER":
                stats["grocery_orders"] += 1
            elif order_type == "RESTOCK_ORDER":
                stats["restock_orders"] += 1
            if status == "OK":
                stats["ok_count"] += 1
            else:
                stats["bad_request_count"] += 1

            # Persist to CSV
            _append_csv(CSV_OUTPUT_PATH, [timestamp, order_id, order_type, status, latency])

            # Print live update
            avg = stats["total_latency"] / stats["total_requests"]
            print(
                f"[{stats['total_requests']}] {order_type} | {status} | "
                f"latency={latency:.4f}s | avg={avg:.4f}s | order={order_id[:8]}..."
            )

        except zmq.ZMQError as e:
            if e.errno == zmq.ETERM:
                break
            raise


if __name__ == "__main__":
    serve()

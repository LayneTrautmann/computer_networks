"""
Flask Ordering Service
Receives HTTP/JSON requests from clients and forwards them to the Inventory Service via gRPC.
Starts a timer per request, measures end-to-end latency, and publishes Analytics events via ZMQ.
"""

import os
import sys
import time
import json

from flask import Flask, request, jsonify
import grpc
import zmq

# Allow imports from ../protos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "protos"))
sys.path.insert(0, PROTOS_DIR)

import grocery_pb2
import grocery_pb2_grpc

app = Flask(__name__)

# Configuration
INVENTORY_SERVICE_HOST = os.environ.get("INVENTORY_SERVICE_HOST", "localhost")
INVENTORY_SERVICE_PORT = os.environ.get("INVENTORY_SERVICE_PORT", "50051")
INVENTORY_SERVICE_ADDRESS = f"{INVENTORY_SERVICE_HOST}:{INVENTORY_SERVICE_PORT}"

# Analytics: Ordering publishes to this address (Analytics service subscribes)
ZMQ_ANALYTICS_ADDRESS = os.environ.get("ZMQ_ANALYTICS_ADDRESS", "tcp://localhost:5557")
ZMQ_ANALYTICS_TOPIC = os.environ.get("ZMQ_ANALYTICS_TOPIC", "analytics")

# Lazy-init ZMQ PUB socket for analytics
_analytics_socket = None
_analytics_ctx = None


def _get_analytics_socket():
    global _analytics_socket, _analytics_ctx
    if _analytics_socket is None:
        _analytics_ctx = zmq.Context.instance()
        _analytics_socket = _analytics_ctx.socket(zmq.PUB)
        _analytics_socket.connect(ZMQ_ANALYTICS_ADDRESS)
    return _analytics_socket


def _publish_analytics(order_id, order_type, status, latency_seconds):
    """Publish one analytics event (order_type: GROCERY_ORDER | RESTOCK_ORDER, status: OK | BAD_REQUEST)."""
    try:
        sock = _get_analytics_socket()
        payload = json.dumps({
            "order_id": order_id or "",
            "order_type": order_type,
            "status": status,
            "latency_seconds": round(latency_seconds, 6),
        }).encode("utf-8")
        sock.send_multipart([ZMQ_ANALYTICS_TOPIC.encode("utf-8"), payload])
    except Exception:
        pass  # Don't fail the request if analytics is down


def json_items_to_protobuf(json_items):
    """Convert JSON items structure to Protobuf OrderItems message."""
    order_items = grocery_pb2.OrderItems()

    # Helper to convert a category's item list
    def convert_category(category_name):
        category = grocery_pb2.Category()
        for item in json_items.get(category_name, []):
            category.items.append(
                grocery_pb2.Item(name=item["name"], quantity=item["quantity"])
            )
        return category

    order_items.bread.CopyFrom(convert_category("bread"))
    order_items.dairy.CopyFrom(convert_category("dairy"))
    order_items.meat.CopyFrom(convert_category("meat"))
    order_items.produce.CopyFrom(convert_category("produce"))
    order_items.party.CopyFrom(convert_category("party"))

    return order_items


def protobuf_fulfilled_to_json(fulfilled_items):
    """Convert Protobuf FulfilledItems message to JSON structure."""
    result = {"bread": [], "dairy": [], "meat": [], "produce": [], "party": []}

    def convert_category(category, category_name):
        for item in category.items:
            result[category_name].append(
                {
                    "name": item.name,
                    "quantity_requested": item.quantity_requested,
                    "quantity_fulfilled": item.quantity_fulfilled,
                }
            )

    convert_category(fulfilled_items.bread, "bread")
    convert_category(fulfilled_items.dairy, "dairy")
    convert_category(fulfilled_items.meat, "meat")
    convert_category(fulfilled_items.produce, "produce")
    convert_category(fulfilled_items.party, "party")

    return result


def protobuf_response_to_json(response):
    """Convert Protobuf OrderResponse to JSON."""
    status_map = {grocery_pb2.OK: "OK", grocery_pb2.BAD_REQUEST: "BAD_REQUEST"}

    return {
        "status": status_map.get(response.status, "UNKNOWN"),
        "message": response.message,
        "order_id": response.order_id if response.order_id else None,
        "items_fulfilled": protobuf_fulfilled_to_json(response.items_fulfilled),
        "total_price": response.total_price,
    }


def _has_any_item(json_items):
    """Return True if at least one item is present in the items dict."""
    if not json_items:
        return False
    for category in ("bread", "dairy", "meat", "produce", "party"):
        if json_items.get(category):
            return True
    return False


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/order/grocery", methods=["POST"])
def grocery_order():
    """Process a grocery order from a customer."""
    start_time = time.perf_counter()
    order_id = None
    status = "BAD_REQUEST"

    try:
        data = request.get_json()

        if not data:
            return jsonify(
                {
                    "status": "BAD_REQUEST",
                    "message": "No JSON data provided",
                    "order_id": None,
                    "items_fulfilled": None,
                    "total_price": None,
                }
            ), 400

        if not _has_any_item(data.get("items", {})):
            return jsonify(
                {
                    "status": "BAD_REQUEST",
                    "message": "At least one item must be ordered",
                    "order_id": None,
                    "items_fulfilled": None,
                    "total_price": None,
                }
            ), 400

        grpc_request = grocery_pb2.GroceryOrderRequest(
            customer_id=data.get("customer_id", ""),
            order_type=grocery_pb2.GROCERY_ORDER,
            items=json_items_to_protobuf(data.get("items", {})),
        )

        with grpc.insecure_channel(INVENTORY_SERVICE_ADDRESS) as channel:
            stub = grocery_pb2_grpc.InventoryServiceStub(channel)
            grpc_response = stub.ProcessGroceryOrder(grpc_request)

        order_id = grpc_response.order_id or ""
        status = "OK" if grpc_response.status == grocery_pb2.OK else "BAD_REQUEST"
        return jsonify(protobuf_response_to_json(grpc_response))

    except grpc.RpcError as e:
        latency = time.perf_counter() - start_time
        _publish_analytics(order_id or "", "GROCERY_ORDER", "BAD_REQUEST", latency)
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Inventory service error: {e.details()}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 503

    except Exception as e:
        latency = time.perf_counter() - start_time
        _publish_analytics(order_id or "", "GROCERY_ORDER", "BAD_REQUEST", latency)
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Error processing order: {str(e)}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 500

    finally:
        # Publish analytics on success (on failure we already published in except)
        if order_id and status == "OK":
            latency = time.perf_counter() - start_time
            _publish_analytics(order_id, "GROCERY_ORDER", status, latency)


@app.route("/order/restock", methods=["POST"])
def restock_order():
    """Process a restock order from a supplier."""
    start_time = time.perf_counter()
    order_id = None
    status = "BAD_REQUEST"

    try:
        data = request.get_json()

        if not data:
            return jsonify(
                {
                    "status": "BAD_REQUEST",
                    "message": "No JSON data provided",
                    "order_id": None,
                    "items_fulfilled": None,
                    "total_price": None,
                }
            ), 400

        if not _has_any_item(data.get("items", {})):
            return jsonify(
                {
                    "status": "BAD_REQUEST",
                    "message": "At least one item must be restocked",
                    "order_id": None,
                    "items_fulfilled": None,
                    "total_price": None,
                }
            ), 400

        grpc_request = grocery_pb2.RestockOrderRequest(
            supplier_id=data.get("supplier_id", ""),
            order_type=grocery_pb2.RESTOCK_ORDER,
            items=json_items_to_protobuf(data.get("items", {})),
        )

        with grpc.insecure_channel(INVENTORY_SERVICE_ADDRESS) as channel:
            stub = grocery_pb2_grpc.InventoryServiceStub(channel)
            grpc_response = stub.ProcessRestockOrder(grpc_request)

        order_id = grpc_response.order_id or ""
        status = "OK" if grpc_response.status == grocery_pb2.OK else "BAD_REQUEST"
        return jsonify(protobuf_response_to_json(grpc_response))

    except grpc.RpcError as e:
        latency = time.perf_counter() - start_time
        _publish_analytics(order_id or "", "RESTOCK_ORDER", "BAD_REQUEST", latency)
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Inventory service error: {e.details()}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 503

    except Exception as e:
        latency = time.perf_counter() - start_time
        _publish_analytics(order_id or "", "RESTOCK_ORDER", "BAD_REQUEST", latency)
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Error processing order: {str(e)}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 500

    finally:
        if order_id and status == "OK":
            latency = time.perf_counter() - start_time
            _publish_analytics(order_id, "RESTOCK_ORDER", status, latency)


if __name__ == "__main__":
    print(f"Starting Ordering Service on port 5000...")
    print(f"Connecting to Inventory Service at {INVENTORY_SERVICE_ADDRESS}")
    app.run(host="0.0.0.0", port=5000, debug=True)

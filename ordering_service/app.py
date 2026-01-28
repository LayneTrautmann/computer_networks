"""
Flask Ordering Service
Receives HTTP/JSON requests from clients and forwards them to the Inventory Service via gRPC.
"""

import os
import sys

from flask import Flask, request, jsonify
import grpc

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


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/order/grocery", methods=["POST"])
def grocery_order():
    """Process a grocery order from a customer."""
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

        # Build the Protobuf request
        grpc_request = grocery_pb2.GroceryOrderRequest(
            customer_id=data.get("customer_id", ""),
            order_type=grocery_pb2.GROCERY_ORDER,
            items=json_items_to_protobuf(data.get("items", {})),
        )

        # Call the Inventory Service via gRPC
        with grpc.insecure_channel(INVENTORY_SERVICE_ADDRESS) as channel:
            stub = grocery_pb2_grpc.InventoryServiceStub(channel)
            grpc_response = stub.ProcessGroceryOrder(grpc_request)

        # Convert response to JSON and return
        return jsonify(protobuf_response_to_json(grpc_response))

    except grpc.RpcError as e:
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
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Error processing order: {str(e)}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 500


@app.route("/order/restock", methods=["POST"])
def restock_order():
    """Process a restock order from a supplier."""
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

        # Build the Protobuf request
        grpc_request = grocery_pb2.RestockOrderRequest(
            supplier_id=data.get("supplier_id", ""),
            order_type=grocery_pb2.RESTOCK_ORDER,
            items=json_items_to_protobuf(data.get("items", {})),
        )

        # Call the Inventory Service via gRPC
        with grpc.insecure_channel(INVENTORY_SERVICE_ADDRESS) as channel:
            stub = grocery_pb2_grpc.InventoryServiceStub(channel)
            grpc_response = stub.ProcessRestockOrder(grpc_request)

        # Convert response to JSON and return
        return jsonify(protobuf_response_to_json(grpc_response))

    except grpc.RpcError as e:
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
        return jsonify(
            {
                "status": "BAD_REQUEST",
                "message": f"Error processing order: {str(e)}",
                "order_id": None,
                "items_fulfilled": None,
                "total_price": None,
            }
        ), 500


if __name__ == "__main__":
    print(f"Starting Ordering Service on port 5000...")
    print(f"Connecting to Inventory Service at {INVENTORY_SERVICE_ADDRESS}")
    app.run(host="0.0.0.0", port=5000, debug=True)

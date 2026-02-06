import os
import sys
import time
import argparse
import threading

import grpc
import zmq

# Allow imports from ../protos and ../flatbuf
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "protos"))
FLATBUF_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "flatbuf"))
sys.path.insert(0, PROTOS_DIR)
sys.path.insert(0, FLATBUF_DIR)

import grocery_pb2
import grocery_pb2_grpc

from GroceryRobot import RobotMessage
from GroceryRobot import ActionType

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VALID_AISLES = ["bread", "dairy", "meat", "produce", "party"]

SLEEP_PER_ITEM_SEC = 0.5   # simulated fetch/restock time per unique item
SLEEP_TO_CART_SEC = 1.0     # simulated delivery-to-cart time

ACTION_NAMES = {
    ActionType.ActionType.FETCH: "FETCH",
    ActionType.ActionType.RESTOCK: "RESTOCK",
}

# ---------------------------------------------------------------------------
# FlatBuffers deserialization
# ---------------------------------------------------------------------------

def extract_my_items(payload_bytes, my_aisle):
    """Deserialize FlatBuffers payload and return items for this robot's aisle.

    Returns (order_id, request_id, action_type, items_list) where each item
    in items_list is a (name: str, quantity: int) tuple.
    """
    buf = bytearray(payload_bytes)
    msg = RobotMessage.RobotMessage.GetRootAs(buf, 0)

    order_id = msg.OrderId().decode("utf-8")
    request_id = msg.RequestId().decode("utf-8")
    action_type = msg.ActionType()

    items = []
    for i in range(msg.AisleItemsLength()):
        aisle_entry = msg.AisleItems(i)
        aisle_name = aisle_entry.Aisle().decode("utf-8")
        if aisle_name == my_aisle:
            for j in range(aisle_entry.ItemsLength()):
                item = aisle_entry.Items(j)
                items.append((item.Name().decode("utf-8"), item.Quantity()))
            break

    return order_id, request_id, action_type, items

# ---------------------------------------------------------------------------
# gRPC response
# ---------------------------------------------------------------------------

def send_response(stub, order_id, request_id, robot_id, aisle,
                  status, message, items):
    """Build a RobotResponse and send it to the Inventory via gRPC."""
    fulfilled = [
        grocery_pb2.FulfilledItem(
            name=name,
            quantity_requested=qty,
            quantity_fulfilled=qty,
        )
        for name, qty in items
    ]

    response = grocery_pb2.RobotResponse(
        order_id=order_id,
        request_id=request_id,
        robot_id=robot_id,
        aisle=aisle,
        status=status,
        message=message,
        items_handled=fulfilled,
    )

    ack = stub.ReportResult(response)
    print(f"  [{robot_id}] Inventory ack: {ack.message}")

# ---------------------------------------------------------------------------
# Order processing
# ---------------------------------------------------------------------------

def process_order(stub, robot_id, aisle, order_id, request_id,
                  action_type, items):
    """Handle a single order: simulate work then report back via gRPC."""
    action_name = ACTION_NAMES.get(action_type, "UNKNOWN")

    if items:
        print(f"  [{robot_id}] {action_name} order {order_id}: "
              f"{len(items)} item(s) -> {items}")
        # Simulate fetching/restocking each unique item
        work_time = len(items) * SLEEP_PER_ITEM_SEC
        print(f"  [{robot_id}] Working for {work_time:.1f}s ...")
        time.sleep(work_time)
        # Simulate delivering to cart / shelving
        print(f"  [{robot_id}] Delivering to cart ({SLEEP_TO_CART_SEC}s) ...")
        time.sleep(SLEEP_TO_CART_SEC)

        send_response(
            stub, order_id, request_id, robot_id, aisle,
            status=grocery_pb2.OK,
            message=f"{action_name} complete for {aisle}",
            items=items,
        )
    else:
        print(f"  [{robot_id}] {action_name} order {order_id}: "
              f"no items for aisle '{aisle}' — NO-OP")
        send_response(
            stub, order_id, request_id, robot_id, aisle,
            status=grocery_pb2.OK,
            message=f"No items for {aisle} — NO-OP",
            items=[],
        )

# ---------------------------------------------------------------------------
# Main event loop
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Robot worker for a single grocery aisle")
    parser.add_argument(
        "aisle", choices=VALID_AISLES,
        help="Aisle this robot is responsible for")
    parser.add_argument(
        "--inventory-host", default=None,
        help="Inventory gRPC host (default: env INVENTORY_SERVICE_HOST or localhost)")
    parser.add_argument(
        "--inventory-port", default=None,
        help="Inventory gRPC port (default: env INVENTORY_SERVICE_PORT or 50051)")
    parser.add_argument(
        "--zmq-address", default=None,
        help="ZMQ PUB address to connect to (default: env ZMQ_SUB_ADDRESS or tcp://localhost:5556)")
    parser.add_argument(
        "--zmq-topic", default=None,
        help="ZMQ topic to subscribe to (default: env ZMQ_ROBOT_TOPIC or 'robot')")
    return parser.parse_args()


def main():
    args = parse_args()
    aisle = args.aisle
    robot_id = f"robot_{aisle}"

    # Resolve configuration with fallback: CLI arg -> env var -> default
    inv_host = (args.inventory_host
                or os.environ.get("INVENTORY_SERVICE_HOST", "localhost"))
    inv_port = (args.inventory_port
                or os.environ.get("INVENTORY_SERVICE_PORT", "50051"))
    zmq_address = (args.zmq_address
                   or os.environ.get("ZMQ_SUB_ADDRESS", "tcp://localhost:5556"))
    zmq_topic = (args.zmq_topic
                 or os.environ.get("ZMQ_ROBOT_TOPIC", "robot"))

    # Persistent gRPC channel to Inventory
    grpc_target = f"{inv_host}:{inv_port}"
    channel = grpc.insecure_channel(grpc_target)
    stub = grocery_pb2_grpc.RobotServiceStub(channel)
    print(f"[{robot_id}] gRPC channel -> {grpc_target}")

    # ZMQ SUB socket
    zmq_context = zmq.Context.instance()
    sub_socket = zmq_context.socket(zmq.SUB)
    sub_socket.connect(zmq_address)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, zmq_topic)
    print(f"[{robot_id}] ZMQ SUB connected -> {zmq_address} (topic='{zmq_topic}')")
    print(f"[{robot_id}] Waiting for orders ...\n")

    try:
        while True:
            # Block until a message arrives: [topic, payload]
            topic, payload = sub_socket.recv_multipart()

            order_id, request_id, action_type, items = extract_my_items(
                payload, aisle)

            # Process each order in a daemon thread for concurrency
            t = threading.Thread(
                target=process_order,
                args=(stub, robot_id, aisle, order_id, request_id,
                      action_type, items),
                daemon=True,
            )
            t.start()

    except KeyboardInterrupt:
        print(f"\n[{robot_id}] Shutting down.")
    finally:
        sub_socket.close()
        channel.close()


if __name__ == "__main__":
    main()

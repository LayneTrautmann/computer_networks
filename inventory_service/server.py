import os
import sys
import time
import uuid
import threading
from concurrent import futures

import grpc
import zmq
import flatbuffers

# Allow imports from ../protos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "protos"))
FLATBUF_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "flatbuf"))
sys.path.insert(0, PROTOS_DIR)
sys.path.insert(0, FLATBUF_DIR)

import grocery_pb2
import grocery_pb2_grpc

from GroceryRobot import ActionType
from GroceryRobot import AisleItems
from GroceryRobot import Item
from GroceryRobot import RobotMessage


ZMQ_PUB_ADDRESS = os.environ.get("ZMQ_PUB_ADDRESS", "tcp://*:5556")
ZMQ_ROBOT_TOPIC = os.environ.get("ZMQ_ROBOT_TOPIC", "robot")
ROBOT_RESPONSE_TIMEOUT_SEC = float(os.environ.get("ROBOT_RESPONSE_TIMEOUT_SEC", "10"))
EXPECTED_ROBOTS = int(os.environ.get("EXPECTED_ROBOTS", "5"))
PRICING_SERVICE_ADDRESS = os.environ.get("PRICING_SERVICE_HOST", "localhost") + ":50053"


class OrderTracker:
    # Tracks robot replies per order and lets Inventory wait for them.
    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._responses = {}

    def init_order(self, order_id):
        with self._cond:
            self._responses.setdefault(order_id, {})

    def add_response(self, response):
        with self._cond:
            responses = self._responses.setdefault(response.order_id, {})
            responses[response.robot_id] = response
            self._cond.notify_all()

    def wait_for_responses(self, order_id, expected, timeout_sec):
        end_time = time.monotonic() + timeout_sec
        with self._cond:
            responses = self._responses.setdefault(order_id, {})
            while len(responses) < expected:
                remaining = end_time - time.monotonic()
                if remaining <= 0:
                    break
                self._cond.wait(timeout=remaining)
            completed = len(responses) >= expected
            collected = list(responses.values())
            self._responses.pop(order_id, None)
            return collected, completed


def _extract_items_by_aisle(order_items):
    return {
        "bread": list(order_items.bread.items),
        "dairy": list(order_items.dairy.items),
        "meat": list(order_items.meat.items),
        "produce": list(order_items.produce.items),
        "party": list(order_items.party.items),
    }


def _build_robot_message(order_id, request_id, action_type, items_by_aisle):
    # Build Flatbuffers payload for ZeroMQ PUB.
    builder = flatbuffers.Builder(1024)
    aisle_offsets = []

    for aisle, items in items_by_aisle.items():
        if not items:
            continue
        item_offsets = []
        for item in items:
            name_offset = builder.CreateString(item.name)
            Item.ItemStart(builder)
            Item.ItemAddName(builder, name_offset)
            Item.ItemAddQuantity(builder, item.quantity)
            item_offsets.append(Item.ItemEnd(builder))

        AisleItems.AisleItemsStartItemsVector(builder, len(item_offsets))
        for offset in reversed(item_offsets):
            builder.PrependUOffsetTRelative(offset)
        items_vector = builder.EndVector()

        aisle_offset = builder.CreateString(aisle)
        AisleItems.AisleItemsStart(builder)
        AisleItems.AisleItemsAddAisle(builder, aisle_offset)
        AisleItems.AisleItemsAddItems(builder, items_vector)
        aisle_offsets.append(AisleItems.AisleItemsEnd(builder))

    RobotMessage.RobotMessageStartAisleItemsVector(builder, len(aisle_offsets))
    for offset in reversed(aisle_offsets):
        builder.PrependUOffsetTRelative(offset)
    aisle_items_vector = builder.EndVector()

    order_id_offset = builder.CreateString(order_id)
    request_id_offset = builder.CreateString(request_id)

    RobotMessage.RobotMessageStart(builder)
    RobotMessage.RobotMessageAddOrderId(builder, order_id_offset)
    RobotMessage.RobotMessageAddRequestId(builder, request_id_offset)
    RobotMessage.RobotMessageAddActionType(builder, action_type)
    RobotMessage.RobotMessageAddAisleItems(builder, aisle_items_vector)
    msg = RobotMessage.RobotMessageEnd(builder)
    builder.Finish(msg)
    return bytes(builder.Output())


class InventoryService(grocery_pb2_grpc.InventoryServiceServicer):
    def __init__(self, pub_socket, tracker):
        self._pub_socket = pub_socket
        self._tracker = tracker

    def _build_success_response(self, order_id):
        return grocery_pb2.OrderResponse(
            status=grocery_pb2.OK,
            message="Order processed successfully",
            order_id=order_id,
            # items_fulfilled left empty for now (basic success)
            total_price=0.0,
        )

    def ProcessGroceryOrder(self, request, context):
        order_id = str(uuid.uuid4())
        self._tracker.init_order(order_id)

        # Publish fetch request to robots.
        items_by_aisle = _extract_items_by_aisle(request.items)
        payload = _build_robot_message(
            order_id=order_id,
            request_id=request.customer_id,
            action_type=ActionType.ActionType.FETCH,
            items_by_aisle=items_by_aisle,
        )
        self._pub_socket.send_multipart([ZMQ_ROBOT_TOPIC.encode("utf-8"), payload])

        # Wait for all robot responses (or timeout).
        collected, completed = self._tracker.wait_for_responses(
            order_id, EXPECTED_ROBOTS, ROBOT_RESPONSE_TIMEOUT_SEC
        )
        if not completed:
            return grocery_pb2.OrderResponse(
                status=grocery_pb2.BAD_REQUEST,
                message="Timed out waiting for robots",
                order_id=order_id,
                total_price=0.0,
            )
        # Items from all robots
        all_items = []
        for res in collected:
            all_items.extend(res.items_handled)

        pricing_request = grocery_pb2.PricingRequest(
            order_id=order_id,
            items=all_items
        )
        # Call Pricing Service
        with grpc.insecure_channel(PRICING_SERVICE_ADDRESS) as channel:
            stub = grocery_pb2_grpc.PricingServiceStub(channel)
            grpc_response = stub.GetPrice(pricing_request)

        
        return grocery_pb2.OrderResponse(
            status=grocery_pb2.OK,
            message="Order is a success",
            order_id=order_id,
            total_price=grpc_response.total_price,
        )

    def ProcessRestockOrder(self, request, context):
        order_id = str(uuid.uuid4())
        self._tracker.init_order(order_id)

        # Publish restock request to robots.
        items_by_aisle = _extract_items_by_aisle(request.items)
        payload = _build_robot_message(
            order_id=order_id,
            request_id=request.supplier_id,
            action_type=ActionType.ActionType.RESTOCK,
            items_by_aisle=items_by_aisle,
        )
        self._pub_socket.send_multipart([ZMQ_ROBOT_TOPIC.encode("utf-8"), payload])

        # Wait for all robot responses (or timeout).
        _, completed = self._tracker.wait_for_responses(
            order_id, EXPECTED_ROBOTS, ROBOT_RESPONSE_TIMEOUT_SEC
        )
        if not completed:
            return grocery_pb2.OrderResponse(
                status=grocery_pb2.BAD_REQUEST,
                message="Timed out waiting for robots",
                order_id=order_id,
                total_price=0.0,
            )

        return self._build_success_response(order_id)


class RobotService(grocery_pb2_grpc.RobotServiceServicer):
    # gRPC endpoint that robots call after work is done.
    def __init__(self, tracker):
        self._tracker = tracker

    def ReportResult(self, request, context):
        self._tracker.add_response(request)
        return grocery_pb2.RobotAck(
            status=grocery_pb2.OK,
            message=f"Received result from {request.robot_id}",
        )


def serve():
    zmq_context = zmq.Context.instance()
    pub_socket = zmq_context.socket(zmq.PUB)
    pub_socket.bind(ZMQ_PUB_ADDRESS)

    # Inventory handles gRPC from Ordering and Robots.
    tracker = OrderTracker()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grocery_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryService(pub_socket, tracker), server
    )
    grocery_pb2_grpc.add_RobotServiceServicer_to_server(
        RobotService(tracker), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Inventory service running on port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()

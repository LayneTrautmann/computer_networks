import os
import sys
import uuid
from concurrent import futures

import grpc

# Allow imports from ../protos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "protos"))
sys.path.insert(0, PROTOS_DIR)

import grocery_pb2
import grocery_pb2_grpc


class InventoryService(grocery_pb2_grpc.InventoryServiceServicer):
    def _build_success_response(self):
        return grocery_pb2.OrderResponse(
            status=grocery_pb2.OK,
            message="Order processed successfully",
            order_id=str(uuid.uuid4()),
            # items_fulfilled left empty for now (basic success)
            total_price=0.0,
        )

    def ProcessGroceryOrder(self, request, context):
        return self._build_success_response()

    def ProcessRestockOrder(self, request, context):
        return self._build_success_response()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grocery_pb2_grpc.add_InventoryServiceServicer_to_server(
        InventoryService(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Inventory service running on port 50051...")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()

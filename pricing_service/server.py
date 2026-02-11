import os
import sys
from concurrent import futures

import grpc

# Allow imports from ../protos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROTOS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "protos"))
sys.path.insert(0, PROTOS_DIR)

import grocery_pb2
import grocery_pb2_grpc

class PricingService(grocery_pb2_grpc.PricingServiceServicer):
    def __init__(self):
        # price for each item
        self._prices = {
            "white_bread": 3.99,
            "wheat_bread": 5.99,
            "bagels": 4.99,
            "waffles": 4.99,
            "croissants": 3.00,
            "baguette": 3.00,
            "milk": 3.00,
            "cheese": 4.99,
            "yogurt": 3.99,
            "butter": 2.00,
            "cream": 2.99,
            "eggs": 3.99,
            "chicken": 10.00,
            "beef": 11.99,
            "pork": 6.99,
            "turkey": 8.00,
            "fish": 10.99,
            "lamb": 11.99,
            "tomatoes": 2.99,
            "onions": 1.49,
            "apples": 1.99,
            "oranges": 2.49,
            "bananas": 0.99,
            "lettuce": 1.99,
            "carrots": 1.49,
            "potatoes": 2.99,
            "soda": 1.99,
            "paper_plates": 3.99,
            "napkins": 2.49,
            "cups": 2.99,
            "balloons": 4.99,
            "streamers": 3.49,
        }

    # Computing total prices 
    def GetPrice(self, request, context):
        total = 0
        for item in request.items:
            total += (self._prices[item.name] * item.quantity_fulfilled)

        return grocery_pb2.PricingResponse(
                status=grocery_pb2.OK,
                total_price=total
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    grocery_pb2_grpc.add_PricingServiceServicer_to_server(PricingService(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("Pricing service running on port 50053...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
    

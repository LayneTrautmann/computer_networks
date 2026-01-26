"""Quick test to verify the protobuf schema works correctly."""

import grocery_pb2

# Create a grocery order request
order = grocery_pb2.GroceryOrderRequest()
order.customer_id = "customer_123"
order.order_type = grocery_pb2.GROCERY_ORDER

# Add bread items
bread_item = order.items.bread.items.add()
bread_item.name = "bagels"
bread_item.quantity = 6

# Add produce items
produce_item = order.items.produce.items.add()
produce_item.name = "tomatoes"
produce_item.quantity = 5

# Serialize to bytes (this is what gets sent over the network)
serialized = order.SerializeToString()
print(f"Serialized order ({len(serialized)} bytes): {serialized}")

# Deserialize back
received_order = grocery_pb2.GroceryOrderRequest()
received_order.ParseFromString(serialized)

print(f"\nDeserialized order:")
print(f"  Customer ID: {received_order.customer_id}")
print(f"  Order Type: {grocery_pb2.OrderType.Name(received_order.order_type)}")
print(f"  Bread items: {[(item.name, item.quantity) for item in received_order.items.bread.items]}")
print(f"  Produce items: {[(item.name, item.quantity) for item in received_order.items.produce.items]}")

# Create a response
response = grocery_pb2.OrderResponse()
response.status = grocery_pb2.OK
response.message = "Order processed successfully"
response.order_id = "order_456"
response.total_price = 15.99

print(f"\nResponse:")
print(f"  Status: {grocery_pb2.StatusCode.Name(response.status)}")
print(f"  Message: {response.message}")
print(f"  Total Price: ${response.total_price}")

print("\n✓ Protobuf schema is working correctly!")

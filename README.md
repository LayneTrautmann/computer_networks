# Computer Networks - PA1

## Automated Grocery Ordering and Delivery Service

### Project Status

**Milestone 1 - In Progress**

#### Completed:
- [x] Project structure created
- [x] Protobuf schema (`protos/grocery.proto`)
- [x] Generated Python gRPC code (`grocery_pb2.py`, `grocery_pb2_grpc.py`)
- [x] JSON schema documentation (`schemas/json_schema.md`)
- [x] Tested protobuf serialization/deserialization

#### TODO:
- [ ] Streamlit client (Grocery + Restock orders)
- [ ] Flask Ordering service
- [ ] Basic Inventory service (returns success)
- [ ] HTTP-JSON communication (Client ↔ Ordering)
- [ ] gRPC-Protobuf communication (Ordering ↔ Inventory)
- [ ] End-to-end testing

---

### Project Structure

```
computer_networks/
├── protos/
│   ├── grocery.proto           # Protobuf schema definition
│   ├── grocery_pb2.py          # Generated message classes
│   ├── grocery_pb2_grpc.py     # Generated gRPC service classes
│   └── test_proto.py           # Test file for protobuf
├── schemas/
│   └── json_schema.md          # JSON format documentation
├── client/                     # Streamlit client (TODO)
├── ordering_service/           # Flask ordering service (TODO)
├── inventory_service/          # gRPC inventory service (TODO)
├── requirements.txt            # Python dependencies
└── README.md
```

---

### Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Recompile Protobuf (if you modify grocery.proto)

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --grpc_python_out=./protos ./protos/grocery.proto
```


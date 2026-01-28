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
- [x] Streamlit client (Grocery + Restock orders)
- [x] Flask Ordering service
- [x] Basic Inventory service (returns success)
- [x] HTTP-JSON communication (Client ↔ Ordering)
- [x] gRPC-Protobuf communication (Ordering ↔ Inventory)

#### TODO:
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
├── client/
│   └── app.py                  # Streamlit client GUI
├── ordering_service/
│   └── app.py                  # Flask ordering service
├── inventory_service/
│   └── server.py               # gRPC inventory service
├── requirements.txt            # Python dependencies
└── README.md
```

---

### Setup (Works on Mac, Windows, and Linux)

#### 1. Clone the repository
```bash
git clone https://github.com/LayneTrautmann/computer_networks.git
cd computer_networks
```

#### 2. Create virtual environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

### Running the Streamlit Client

```bash
streamlit run client/app.py
```

This opens a browser at `http://localhost:8501` with:
- **Grocery Order tab**: Simulates a smart refrigerator placing an order
- **Restock Order tab**: Simulates a supplier truck restocking inventory

The client sends JSON requests to the Flask Ordering Service (once built).

---

### Running the Ordering Service (TODO - Partner Task)

```bash
python ordering_service/app.py
```

Runs on `http://localhost:5000`. Receives JSON from client, sends gRPC to Inventory.

---

### Running the Inventory Service (TODO - Partner Task)

```bash
python inventory_service/server.py
```

Runs gRPC server on port `50051`. Receives requests from Ordering service.

---

### Recompile Protobuf (if you modify grocery.proto)

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --grpc_python_out=./protos ./protos/grocery.proto
```

---

### Team Work Division (Milestone 1)

| Person | Task | Status |
|--------|------|--------|
| Layne | Schemas + Streamlit Client | Done |
| Kevin | Flask Ordering Service | Done |
| Partner 3 | Inventory Service | Done |

---

### Communication Flow (Milestone 1)

```
Streamlit Client  --(HTTP/JSON)-->  Flask Ordering  --(gRPC/Protobuf)-->  Inventory
(port 8501)                         (port 5000)                           (port 50051)
```

---

### Key Files for Each Task

**Flask Ordering Service (Partner 2):**
- Create: `ordering_service/app.py`
- Read: `schemas/json_schema.md` (JSON format from client)
- Read: `protos/grocery.proto` (Protobuf format to send to Inventory)

**Inventory Service (Partner 3):**
- Create: `inventory_service/server.py`
- Read: `protos/grocery.proto` (Protobuf format to receive)
- For now: Just return success response

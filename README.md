# Computer Networks - PA1

## Automated Grocery Ordering and Delivery Service

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

### Local Setup (Works on Mac, Windows, and Linux)

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

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run all services locally (3 terminals)

**Terminal 1 - Inventory Service:**
```bash
source venv/bin/activate
python inventory_service/server.py
```

**Terminal 2 - Ordering Service:**
```bash
source venv/bin/activate
python ordering_service/app.py
```

**Terminal 3 - Streamlit Client:**
```bash
source venv/bin/activate
streamlit run client/app.py
```

Then open `http://localhost:8501` in your browser.

---

### Running on Chamelon Cloud virtual machines
```bash
team7-vm1: ip: 172.16.5.232, running: Inventory, port: 50051
team7-vm2: ip: 172.16.5.8, running: Ordering, port: 5000
team7-vm3: ip: 172.16.5.159, running: Client, port: 8501 
```

Use 3 windows to ssh into each vm


**VM1 (Inventory):**
```bash
VM1 (172.16.5.232) Backend: Inventory, Pricing, 5 Robots, Analytics

Need to ssh into 8 VM1 windows.


# In each tab first:
cd ~/computer_networks
git pull
source venv/bin/activate
pip install grpcio grpcio-tools protobuf pyzmq flatbuffers

# Tab 1: Analytics
python analytics_service/server.py

# Tab 2: Pricing
python pricing_service/server.py

# Tab 3: Inventory
python inventory_service/server.py

# Tab 4-8: Robots
python robot_service/robot.py bread
python robot_service/robot.py dairy
python robot_service/robot.py meat
python robot_service/robot.py produce
python robot_service/robot.py party
```

**VM2 (Ordering):**
```bash
VM2 (172.16.5.8) - Ordering Service

cd ~/computer_networks
git pull
source venv/bin/activate
pip install flask grpcio grpcio-tools protobuf pyzmq
INVENTORY_SERVICE_HOST=172.16.5.232 ZMQ_ANALYTICS_ADDRESS=tcp://172.16.5.232:5557 python ordering_service/app.py

```

**VM3 (Client):**
```bash
VM3 (172.16.5.159) - Streamlit Client


cd ~/computer_networks
git pull
source venv/bin/activate
pip install streamlit requests
sed -i 's|http://localhost:5000|http://172.16.5.8:5000|' client/app.py
streamlit run client/app.py
```

#### Viewing on the browser

Then run this on your computer:
```bash
ssh -L 8501:localhost:8501 team7_vm3
```

Then open `http://localhost:8501` in your browser.

Generating the graphs: 
```bash
cd ~/computer_networks
source venv/bin/activate
pip install pandas matplotlib
python analytics_service/plot.py
```
Plots are saved to analytics_service/plots/

---

### Recompile Protobuf (if you modify grocery.proto)

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --grpc_python_out=./protos ./protos/grocery.proto
```

---


### Communication Flow

```
Streamlit Client  --(HTTP/JSON)-->  Flask Ordering  --(gRPC/Protobuf)-->  Inventory
(port 8501)                         (port 5000)                           (port 50051)
```


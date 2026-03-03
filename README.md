# Computer Networks - PA1 & PA2

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
├── locustfile.py               # Locust load testing workload
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

---

## PA2 - K8s Deployment
- **C1** (172.16.1.196): Client
- **C2** (172.16.2.136): Ordering, Inventory, Pricing, Analytics
- **C3** (172.16.3.137): 5 Robots

---

### Load Testing with Locust

Locust generates HTTP workloads against the Ordering Service to measure tail latencies.

**Run against K8s deployment (web UI):**
```bash
locust -f locustfile.py --host=http://172.16.2.136:30500
```
Then open `http://localhost:8089`, configure the number of users and spawn rate, and start the test.

**Run locally:**
```bash
locust -f locustfile.py --host=http://localhost:5000
```

**Headless mode with CSV export:**
```bash
locust -f locustfile.py --host=http://172.16.2.136:30500 --headless -u 50 -r 5 -t 60s --csv=results
```
This produces `results_stats.csv`, `results_stats_history.csv`, etc. for analysis.

Traffic mix: 80% refrigerator grocery orders (`/order/grocery`), 20% truck restock orders (`/order/restock`).

---

### Recompile Protobuf (if you modify grocery.proto)

```bash
python -m grpc_tools.protoc -I./protos --python_out=./protos --grpc_python_out=./protos ./protos/grocery.proto
```

---


---

## PA2 Milestone 3 – ContainerLab HIL & Tail Latency Experiments

### Architecture

```
C1 (172.16.1.196)        ContainerLab WAN          C2 (172.16.2.136)         ContainerLab WAN          C3 (172.16.3.137)
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐   ┌─────────────────────┐   ┌──────────────────┐
│  Client          │    │  wan-c1-c2-a         │    │  Ordering Service    │   │  wan-c2-c3-a         │   │  Robot (bread)    │
│  (Streamlit)     │◄──►│  (172.16.1.254)      │◄──►│  Inventory Service   │◄──►│  (172.16.2.253)      │◄──►│  Robot (dairy)    │
│  Locust          │    │  wan-c1-c2-b         │    │  Pricing Service     │   │  wan-c2-c3-b         │   │  Robot (meat)     │
│  (port 30501)    │    │  (172.16.2.254)      │    │  Analytics Service   │   │  (172.16.3.254)      │   │  Robot (produce)  │
└─────────────────┘    └─────────────────────┘    └─────────────────────┘   └─────────────────────┘   │  Robot (party)    │
                              tc netem                                             tc netem             └──────────────────┘
                         delay/jitter/loss                                    delay/jitter/loss
```

### Step 1: Deploy ContainerLab Topology

On the ContainerLab VM (must have ContainerLab installed):

```bash
cd containerlab/
sudo clab deploy -t topology.clab.yml
```

Verify the topology is running:
```bash
sudo clab inspect -t topology.clab.yml
```

### Step 2: Configure Routes Through ContainerLab

Run once to redirect inter-cluster traffic through the WAN emulation:

```bash
cd containerlab/
chmod +x setup-routes.sh
./setup-routes.sh
```

To remove the routes later (return to direct connectivity):
```bash
./teardown-routes.sh
```

### Step 3: Configure WAN Emulation Scenarios

Apply different WAN characteristics using tc-netem:

```bash
cd containerlab/
chmod +x configure-wan.sh

# Available scenarios:
./configure-wan.sh none      # Baseline – no emulation
./configure-wan.sh low       # 10ms delay, 1ms jitter, 0.1% loss
./configure-wan.sh medium    # 50ms delay, 5ms jitter, 0.5% loss
./configure-wan.sh high      # 100ms delay, 10ms jitter, 1% loss
./configure-wan.sh extreme   # 200ms delay, 25ms jitter, 2% loss

# Custom values:
DELAY=75 JITTER=8 LOSS=0.3 ./configure-wan.sh custom
```

### Step 4: Run Load Tests with Locust

```bash
# Web UI mode
locust -f locustfile.py --host=http://172.16.2.136:30500

# Headless with CSV export
locust -f locustfile.py --host=http://172.16.2.136:30500 \
    --headless -u 50 -r 5 -t 60s --csv=results

# Different workload shapes (via env var):
LOCUST_SHAPE=steady locust -f locustfile.py --host=http://172.16.2.136:30500
LOCUST_SHAPE=burst  locust -f locustfile.py --host=http://172.16.2.136:30500
LOCUST_SHAPE=ramp   locust -f locustfile.py --host=http://172.16.2.136:30500
LOCUST_SHAPE=sine   locust -f locustfile.py --host=http://172.16.2.136:30500
```

Traffic mix: 80% refrigerator grocery orders, 20% truck restock orders.

### Step 5: Run All Experiments Automatically

The experiment runner script iterates through all WAN scenarios:

```bash
chmod +x run_experiments.sh
./run_experiments.sh http://172.16.2.136:30500

# Configure experiment parameters:
LOCUST_USERS=50 LOCUST_SPAWN_RATE=5 LOCUST_DURATION=60s ./run_experiments.sh
```

This will:
1. Run Locust under each WAN scenario (none, low, medium, high, extreme)
2. Collect analytics CSVs into `analytics_service/scenarios/`
3. Generate all plots including CDF comparisons

### Step 6: Generate Plots

```bash
cd ~/computer_networks
source venv/bin/activate
pip install pandas matplotlib numpy

# Generate all plots (basic + CDF + comparisons)
python analytics_service/plot.py
```

Plots saved to `analytics_service/plots/`:
- `latency_histogram.png` – Latency distribution
- `latency_over_time.png` – Latency over time by order type
- `latency_by_type.png` – Box plot by order type
- `outcome_breakdown.png` – OK vs BAD_REQUEST counts
- `summary_table.png` – Statistics summary with P90/P95/P99
- `cdf_latency.png` – **CDF with P50/P90/P95/P99 markers**
- `cdf_latency_by_type.png` – **CDF per order type**
- `throughput_over_time.png` – Requests/sec over time
- `cdf_comparison.png` – **CDF overlay of all WAN scenarios**
- `percentile_bars.png` – **Grouped bar chart of tail latencies per scenario**
- `comparison_summary.png` – **Table of P50/P90/P95/P99 across scenarios**
- `locust_stats.png` – Locust response time & throughput (if CSV available)

### Scenario Comparison

To generate comparison plots manually, place experiment CSVs in `analytics_service/scenarios/`:

```
analytics_service/scenarios/
├── no_containerlab.csv
├── wan_10ms.csv
├── wan_50ms.csv
├── wan_100ms.csv
└── wan_200ms.csv
```

Each CSV should have columns: `timestamp,order_id,order_type,status,latency_seconds`

Then run:
```bash
SCENARIO_CSV_DIR=analytics_service/scenarios python analytics_service/plot.py
```

### Tear Down

```bash
# Remove routes
cd containerlab/
./teardown-routes.sh

# Destroy ContainerLab topology
sudo clab destroy -t topology.clab.yml
```

---

### Communication Flow

```
Streamlit Client  --(HTTP/JSON)-->  Flask Ordering  --(gRPC/Protobuf)-->  Inventory
(port 8501)                         (port 5000)                           (port 50051)

Locust            --(HTTP/JSON)-->  Flask Ordering  --(gRPC/Protobuf)-->  Inventory
(port 8089 UI)                      (port 30500 K8s)                      (port 50051)
```


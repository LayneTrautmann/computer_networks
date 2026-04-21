# Computer Networks - PA1, PA2 & PA3

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

## PA2 - K8s Deployment
- **C1** (172.16.1.196): Client
- **C2** (172.16.2.136): Ordering, Inventory, Pricing, Analytics
- **C3** (172.16.3.137): 5 Robots

---

### Load Testing with Locust

Locust generates HTTP workloads against the Ordering Service to measure tail latencies. Run from C1's master node (not from Mac — the Chameleon private network is not reachable externally).

**Headless mode with CSV export (on C1 master):**
```bash
cd ~/computer_networks
source venv/bin/activate

locust -f locustfile.py --host=http://10.81.62.48:5000 \
    --headless -u 10 -r 2 -t 60s \
    --csv=analytics_service/scenarios/baseline
```
This produces `baseline_stats.csv`, `baseline_stats_history.csv`, etc. for analysis.

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

Two ContainerLab HIL topologies are deployed — one on vm1 (C1→C2 path) and one on vm2 (C2→C3 path):

```
C1 cluster (172.16.1.196)
  └─ client pod
       └─ ordering-wan ClusterIP (K8s EndpointSlice)
            └─ vm1 (172.16.5.232) socat :30500
                 └─ wan-router container (tc-netem on eth1)
                      └─ proxy container (socat)
                           └─ C2 ordering NodePort (172.16.2.136:30500)
                                └─ gRPC → Inventory (C2)
                                     └─ ZMQ → vm2 (172.16.5.8) socat :30556
                                          └─ wan-router container (tc-netem on eth1)
                                               └─ proxy container (socat)
                                                    └─ C3 robots NodePort (172.16.3.137:30556)
```

Locust runs on C1's master node and targets the C1 NodePort (`http://10.81.62.48:5000`) so that all traffic traverses both WAN emulators.

### Step 1: Deploy ContainerLab Topology

SSH into vm1 (172.16.5.232):

```bash
ssh cc@172.16.5.232   # This should be set up in your .config using the bastion_s26 and the private key

cd ~/computer_networks/containerlab
sudo clab deploy -t topology.clab.yml
sudo clab inspect -t topology.clab.yml   # verify containers are running
```

### Step 2: Start socat Relay Chain

After the topology is deployed, start the socat relay chain:

```bash
cd ~/computer_networks/containerlab
chmod +x start-wan.sh
./start-wan.sh
```

This script:
1. Gets the management IPs of `wan-router` and `proxy` containers
2. Kills any existing socat processes
3. Starts socat in `proxy` → C2 (172.16.2.136:30500)
4. Starts socat in `wan-router` → proxy
5. Starts socat on vm1 → wan-router
6. Tests the chain with a health check

### Step 3: Apply K8s EndpointSlice on C1

On C1's master node, redirect the client pod's traffic through vm1:

```bash
kubectl apply -f k8s/c1-wan-endpoint.yaml -n team7
```

This creates a `ordering-wan` ClusterIP service and EndpointSlice pointing to `172.16.5.232:30500` (vm1). The client pod uses `ORDERING_SERVICE_URL=http://ordering-wan:5000`.

To remove (return to direct C1→C2):
```bash
kubectl delete -f k8s/c1-wan-endpoint.yaml -n team7
```

### Step 3b: Deploy ContainerLab Topology on vm2 (C2→C3 path)

SSH into vm2 (172.16.5.8):

```bash
ssh cc@172.16.5.8   # requires bastion_s26 ProxyJump configured in ~/.ssh/config

cd ~/computer_networks/containerlab
sudo clab deploy -t topology-c2c3.clab.yml
sudo clab inspect -t topology-c2c3.clab.yml
chmod +x start-wan-c2c3.sh && ./start-wan-c2c3.sh
```

This sets up a socat relay chain on vm2 for both gRPC (port 30051) and ZMQ (port 30556) traffic between C2 and C3 robots.

### Step 4: Configure WAN Emulation Scenarios

On vm1, apply different WAN impairment levels with tc-netem:

```bash
cd ~/computer_networks/containerlab
chmod +x configure-wan.sh

./configure-wan.sh none      # Baseline – no emulation (ContainerLab only)
./configure-wan.sh low       # 10ms delay, 1ms jitter, 0.1% loss
./configure-wan.sh medium    # 50ms delay, 5ms jitter, 0.5% loss
./configure-wan.sh high      # 100ms delay, 10ms jitter, 1% loss
./configure-wan.sh extreme   # 200ms delay, 25ms jitter, 2% loss
```

### Step 5: Run Load Tests with Locust

On C1's master node (must be run from the cluster, not from Mac):

```bash
cd ~/computer_networks
source venv/bin/activate   # or: python3 -m venv venv && source venv/bin/activate && pip install locust

# Headless with CSV export – saves to analytics_service/scenarios/
locust -f locustfile.py --host=http://10.81.62.48:5000 \
    --headless -u 10 -r 2 -t 60s \
    --csv=analytics_service/scenarios/none
```

Replace `none` with the scenario name (`low`, `medium`, `high`, `extreme`) to match the WAN setting applied in Step 4.

Traffic mix: 80% refrigerator grocery orders (`/order/grocery`), 20% truck restock orders (`/order/restock`).

### Step 6: Collect All Scenarios

Run Steps 4 and 5 for each scenario in sequence. Resulting CSVs:

```
analytics_service/scenarios/
├── none_stats.csv
├── low_stats.csv
├── medium_stats.csv
├── high_stats.csv
└── extreme_stats.csv
```

### Step 7: Generate Plots

On your local machine (Mac):

```bash
cd ~/computer_networks
source venv/bin/activate
pip install pandas matplotlib numpy

python analytics_service/plot_locust.py
```

Plots saved to `analytics_service/plots/`:
- `wan_percentile_bars.png` – Grouped bar chart of P50/P90/P95/P99 across scenarios
- `wan_summary_table.png` – Summary table with request counts, mean, and percentiles
- `wan_latency_trend.png` – Line chart showing latency trend across scenarios

### Tear Down

On vm1:
```bash
cd ~/computer_networks/containerlab
sudo clab destroy -t topology.clab.yml
sudo pkill socat 2>/dev/null || true
```

On vm2:
```bash
cd ~/computer_networks/containerlab
sudo clab destroy -t topology-c2c3.clab.yml
sudo pkill socat 2>/dev/null || true
```

On C1:
```bash
kubectl delete -f k8s/c1-wan-endpoint.yaml -n team7
```

---

## PA3 – ContainerLab 1: WAN with OSPF Routing

### Deploy (on team7-vm1)

```bash
cd ~/computer_networks/containerlab1
chmod +x *.sh
./run.sh
```

### Verify OSPF shortest path

```bash
sudo docker exec -it clab-pa3-wan-lan1-host traceroute 10.4.0.2
# should be path that gives cost 80
```

### Collect routing tables (run for router1 through router6)

```bash
sudo docker exec -it clab-pa3-wan-router1 vtysh -c "show ip route"
sudo docker exec -it clab-pa3-wan-router1 vtysh -c "show ip ospf neighbor"
sudo docker exec -it clab-pa3-wan-router1 vtysh -c "show ip ospf database"
```

### Tear down

```bash
./cleanup.sh
```

---

### Communication Flow

```
Locust (C1 master)  --(HTTP)-->  C1 client NodePort (10.81.62.48:5000)
  └─ ordering-wan ClusterIP  →  vm1:30500 (socat)
       └─ wan-router container (tc-netem delay/jitter/loss on eth1)
            └─ proxy container (socat)
                 └─ C2 ordering NodePort (172.16.2.136:30500)
                      └─ gRPC  →  Inventory (C2)
                           └─ ZMQ  →  Robots (C3)
```

---

## PA4 – Network Policy, WAN Impairments, and Traffic Steering

### Overview

- K8s Cluster 1: clients (primary traffic source)
- K8s Cluster 2: ordering, inventory, pricing (primary backend)
- K8s Cluster 3: ordering, inventory, pricing + robots (backup backend)
- ContainerLab 1 (`containerlab1/`): primary WAN, C1 → C2
- ContainerLab 3 (`containerlab3/`): backup WAN, C1 → C3

### Milestone 1 – Network Policy

Apply a policy so only team7 pods can talk to each other on C1:

```bash
kubectl apply -f k8s/team7-network-policy.yaml -n team7   # on C1
```

### Milestone 2 – WAN Impairments

Add delay and loss to ContainerLab 1 links on vm1:

```bash
sudo clab tools netem set -n clab-pa3-wan-router1 -i eth1 --delay 2000ms --jitter 200ms --loss 20
sudo clab tools netem set -n clab-pa3-wan-router2 -i eth1 --delay 2000ms --jitter 200ms --loss 20
```

Remove impairments:

```bash
sudo clab tools netem set -n clab-pa3-wan-router1 -i eth1 --delay 0ms --jitter 0ms --loss 0
sudo clab tools netem set -n clab-pa3-wan-router2 -i eth1 --delay 0ms --jitter 0ms --loss 0
```

### Milestone 3 – Backup WAN and Traffic Steering

Deploy backup WAN on vm1:

```bash
cd ~/computer_networks/containerlab3
chmod +x *.sh
./run.sh
./start-wan-backup.sh
```

Deploy backup services on C3:

```bash
kubectl apply -f k8s/c2-ordering.yaml -n team7   # on C3
kubectl apply -f k8s/c2-inventory.yaml -n team7
kubectl apply -f k8s/c2-pricing.yaml -n team7
```

Steer C1 traffic to backup (apply on C1):

```bash
kubectl apply -f k8s/c1-backup-endpoint.yaml -n team7
kubectl set env deployment/client ORDERING_SERVICE_URL=http://ordering-backup:5000 -n team7
```

Revert to primary:

```bash
kubectl delete -f k8s/c1-backup-endpoint.yaml -n team7
kubectl set env deployment/client ORDERING_SERVICE_URL=http://ordering-wan:5000 -n team7
```

### Run Locust (on C1 master)

```bash
cd ~/team7/computer_networks
source venv/bin/activate
locust -f locustfile.py --host=http://10.81.62.48:5000 --headless -u 10 -r 2 -t 60s --csv=analytics_service/scenarios/pa4_baseline
```

### Generate Plots (on Mac)

```bash
cd ~/Desktop/computer_networks
source venv/bin/activate
python analytics_service/plot_locust.py
```

Plots saved to `analytics_service/plots/`.


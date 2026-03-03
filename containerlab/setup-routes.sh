#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup-routes.sh – Configure static routes on K8s cluster nodes so that
# inter-cluster traffic flows through the ContainerLab WAN routers.
#
# Run this ONCE after deploying the ContainerLab topology.
#
# What it does:
#   - On C1 nodes: route 172.16.2.0/24 and 172.16.3.0/24 via wan-c1-c2-a (172.16.1.254)
#   - On C2 nodes: route 172.16.1.0/24 via wan-c1-c2-b (172.16.2.254)
#                   route 172.16.3.0/24 via wan-c2-c3-a (172.16.2.253)
#   - On C3 nodes: route 172.16.2.0/24 and 172.16.1.0/24 via wan-c2-c3-b (172.16.3.254)
#
# Prerequisites:
#   - SSH access to all cluster nodes using the S26_CLUSTER.pem key
#   - ContainerLab topology is deployed and routers are up
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SSH_KEY="${SSH_KEY:-~/.ssh/S26_CLUSTER.pem}"
SSH_USER="${SSH_USER:-cc}"
SSH_OPTS="-o StrictHostKeyChecking=no -i ${SSH_KEY}"

# Cluster master IPs
C1_MASTER="172.16.1.196"
C2_MASTER="172.16.2.136"
C3_MASTER="172.16.3.137"

# ContainerLab WAN router gateway IPs
GW_C1_TO_C2="172.16.1.254"   # wan-c1-c2-a sits on C1's subnet
GW_C2_FROM_C1="172.16.2.254" # wan-c1-c2-b sits on C2's subnet
GW_C2_TO_C3="172.16.2.253"   # wan-c2-c3-a sits on C2's subnet
GW_C3_FROM_C2="172.16.3.254" # wan-c2-c3-b sits on C3's subnet

run_ssh() {
    local host="$1"
    shift
    ssh ${SSH_OPTS} "${SSH_USER}@${host}" "$@"
}

echo "=== Fetching worker node IPs for each cluster ==="

get_node_ips() {
    local master="$1"
    run_ssh "$master" "kubectl get nodes -o wide --no-headers | awk '{print \$6}'"
}

echo ""
echo "--- C1 nodes (Clients) ---"
C1_NODES=$(get_node_ips "$C1_MASTER")
echo "$C1_NODES"

echo ""
echo "--- C2 nodes (Core Services) ---"
C2_NODES=$(get_node_ips "$C2_MASTER")
echo "$C2_NODES"

echo ""
echo "--- C3 nodes (Robots) ---"
C3_NODES=$(get_node_ips "$C3_MASTER")
echo "$C3_NODES"

echo ""
echo "=== Adding routes on C1 nodes (-> C2 via ${GW_C1_TO_C2}, -> C3 via ${GW_C1_TO_C2}) ==="
for node in $C1_NODES; do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route replace 172.16.2.0/24 via ${GW_C1_TO_C2}" || true
    run_ssh "$node" "sudo ip route replace 172.16.3.0/24 via ${GW_C1_TO_C2}" || true
done

echo ""
echo "=== Adding routes on C2 nodes (-> C1 via ${GW_C2_FROM_C1}, -> C3 via ${GW_C2_TO_C3}) ==="
for node in $C2_NODES; do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route replace 172.16.1.0/24 via ${GW_C2_FROM_C1}" || true
    run_ssh "$node" "sudo ip route replace 172.16.3.0/24 via ${GW_C2_TO_C3}" || true
done

echo ""
echo "=== Adding routes on C3 nodes (-> C2 via ${GW_C3_FROM_C2}, -> C1 via ${GW_C3_FROM_C2}) ==="
for node in $C3_NODES; do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route replace 172.16.2.0/24 via ${GW_C3_FROM_C2}" || true
    run_ssh "$node" "sudo ip route replace 172.16.1.0/24 via ${GW_C3_FROM_C2}" || true
done

echo ""
echo "=== Route setup complete ==="
echo "Verify with: ssh ${SSH_USER}@<node-ip> ip route"

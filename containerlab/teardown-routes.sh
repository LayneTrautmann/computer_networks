#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# teardown-routes.sh – Remove the static routes added by setup-routes.sh
# so traffic returns to its default direct path (no ContainerLab detour).
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SSH_KEY="${SSH_KEY:-~/.ssh/S26_CLUSTER.pem}"
SSH_USER="${SSH_USER:-cc}"
SSH_OPTS="-o StrictHostKeyChecking=no -i ${SSH_KEY}"

C1_MASTER="172.16.1.196"
C2_MASTER="172.16.2.136"
C3_MASTER="172.16.3.137"

run_ssh() {
    local host="$1"; shift
    ssh ${SSH_OPTS} "${SSH_USER}@${host}" "$@"
}

get_node_ips() {
    local master="$1"
    run_ssh "$master" "kubectl get nodes -o wide --no-headers | awk '{print \$6}'"
}

echo "=== Removing ContainerLab routes ==="

echo ""
echo "--- C1 nodes ---"
for node in $(get_node_ips "$C1_MASTER"); do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route del 172.16.2.0/24 2>/dev/null" || true
    run_ssh "$node" "sudo ip route del 172.16.3.0/24 2>/dev/null" || true
done

echo ""
echo "--- C2 nodes ---"
for node in $(get_node_ips "$C2_MASTER"); do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route del 172.16.1.0/24 2>/dev/null" || true
    run_ssh "$node" "sudo ip route del 172.16.3.0/24 2>/dev/null" || true
done

echo ""
echo "--- C3 nodes ---"
for node in $(get_node_ips "$C3_MASTER"); do
    echo "  -> $node"
    run_ssh "$node" "sudo ip route del 172.16.2.0/24 2>/dev/null" || true
    run_ssh "$node" "sudo ip route del 172.16.1.0/24 2>/dev/null" || true
done

echo ""
echo "=== Routes removed – traffic now takes default direct paths ==="

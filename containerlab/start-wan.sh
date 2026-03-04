#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start-wan.sh – Start socat relay chain after ContainerLab topology is deployed
#
# Run this ONCE after: sudo clab deploy -t topology.clab.yml
#
# Traffic flow:
#   C1 K8s (via EndpointSlice) -> vm1:30500 (socat)
#   -> wan-router container (socat + tc-netem delay on eth1)
#   -> proxy container (socat)
#   -> C2 ordering service (172.16.2.136:30500)
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

C2_ORDERING="172.16.2.136:30500"
LISTEN_PORT=30500

# Get container management IPs
WAN_ROUTER_IP=$(docker inspect clab-grocery-wan-wan-router \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    | tr ',' '\n' | grep '172.20' | head -1)
PROXY_IP=$(docker inspect clab-grocery-wan-proxy \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    | tr ',' '\n' | grep '172.20' | head -1)

echo "wan-router IP: $WAN_ROUTER_IP"
echo "proxy IP:      $PROXY_IP"

# Kill any existing socat processes
echo "Stopping any existing socat processes..."
pkill -9 socat 2>/dev/null || true
docker exec clab-grocery-wan-wan-router pkill -9 socat 2>/dev/null || true
docker exec clab-grocery-wan-proxy pkill -9 socat 2>/dev/null || true
sleep 1

# Start socat in proxy container: listens on 30500, forwards to C2
echo "Starting socat in proxy container -> $C2_ORDERING ..."
docker exec -d clab-grocery-wan-proxy \
    socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:${C2_ORDERING}
sleep 1

# Start socat in wan-router container: listens on 30500, forwards to proxy
echo "Starting socat in wan-router container -> ${PROXY_IP}:${LISTEN_PORT} ..."
docker exec -d clab-grocery-wan-wan-router \
    socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:${PROXY_IP}:${LISTEN_PORT}
sleep 1

# Start socat on vm1: listens on 30500, forwards to wan-router
echo "Starting socat on vm1 -> ${WAN_ROUTER_IP}:${LISTEN_PORT} ..."
socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:${WAN_ROUTER_IP}:${LISTEN_PORT} &
sleep 2

# Test the chain
echo ""
echo "Testing chain: localhost:${LISTEN_PORT} -> wan-router -> proxy -> C2..."
RESPONSE=$(curl -s -X POST http://localhost:${LISTEN_PORT}/health --max-time 5 || echo "FAILED")
echo "Health check response: $RESPONSE"

echo ""
echo "=== WAN relay chain is up ==="
echo "Traffic path: vm1:${LISTEN_PORT} -> wan-router(${WAN_ROUTER_IP}) -> proxy(${PROXY_IP}) -> C2(${C2_ORDERING})"
echo "Apply WAN emulation: ./configure-wan.sh [none|low|medium|high|extreme]"

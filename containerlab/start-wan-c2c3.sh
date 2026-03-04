#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start-wan-c2c3.sh – Start socat relay chain for C2→C3 path on vm2
#
# Run this ONCE after: sudo clab deploy -t topology-c2c3.clab.yml
#
# Traffic flow (two ports):
#   C2 inventory (via EndpointSlice) -> vm2:30051 (socat)
#   -> wan-router container (socat + tc-netem delay on eth1)
#   -> proxy container (socat)
#   -> C3 robot NodePort (172.16.3.137:30051)
#
#   C2 inventory ZMQ PUB -> vm2:30556 (socat)
#   -> wan-router -> proxy -> C3:30556
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

C3_GRPC="172.16.3.137:30051"
C3_ZMQ="172.16.3.137:30556"
GRPC_PORT=30051
ZMQ_PORT=30556

# Get container management IPs
WAN_ROUTER_IP=$(docker inspect clab-grocery-wan-c2c3-wan-router \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    | tr ',' '\n' | grep '172.20' | head -1)
PROXY_IP=$(docker inspect clab-grocery-wan-c2c3-proxy \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    | tr ',' '\n' | grep '172.20' | head -1)

echo "wan-router IP: $WAN_ROUTER_IP"
echo "proxy IP:      $PROXY_IP"

# Kill any existing socat processes
echo "Stopping any existing socat processes..."
pkill -9 socat 2>/dev/null || true
docker exec clab-grocery-wan-c2c3-wan-router pkill -9 socat 2>/dev/null || true
docker exec clab-grocery-wan-c2c3-proxy pkill -9 socat 2>/dev/null || true
sleep 1

# --- gRPC port (30051) ---
echo "Starting socat in proxy container -> $C3_GRPC ..."
docker exec -d clab-grocery-wan-c2c3-proxy \
    socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${C3_GRPC}

echo "Starting socat in wan-router container -> ${PROXY_IP}:${GRPC_PORT} ..."
docker exec -d clab-grocery-wan-c2c3-wan-router \
    socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${PROXY_IP}:${GRPC_PORT}

echo "Starting socat on vm2 (gRPC) -> ${WAN_ROUTER_IP}:${GRPC_PORT} ..."
socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${WAN_ROUTER_IP}:${GRPC_PORT} &

sleep 1

# --- ZMQ port (30556) ---
echo "Starting socat in proxy container -> $C3_ZMQ ..."
docker exec -d clab-grocery-wan-c2c3-proxy \
    socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${C3_ZMQ}

echo "Starting socat in wan-router container -> ${PROXY_IP}:${ZMQ_PORT} ..."
docker exec -d clab-grocery-wan-c2c3-wan-router \
    socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${PROXY_IP}:${ZMQ_PORT}

echo "Starting socat on vm2 (ZMQ) -> ${WAN_ROUTER_IP}:${ZMQ_PORT} ..."
socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${WAN_ROUTER_IP}:${ZMQ_PORT} &

sleep 2

echo ""
echo "=== WAN relay chain (C2→C3) is up ==="
echo "gRPC path: vm2:${GRPC_PORT} -> wan-router(${WAN_ROUTER_IP}) -> proxy(${PROXY_IP}) -> C3(${C3_GRPC})"
echo "ZMQ  path: vm2:${ZMQ_PORT}  -> wan-router(${WAN_ROUTER_IP}) -> proxy(${PROXY_IP}) -> C3(${C3_ZMQ})"
echo "Apply WAN emulation: ./configure-wan-c2c3.sh [none|low|medium|high|extreme]"

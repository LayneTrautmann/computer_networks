#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# start-relay.sh – Start socat relay chain through the bridged LAN topology
#
# Run this AFTER: ./run.sh  (bridges must be configured and STP converged)
#
# Traffic flow (gRPC :30051 and ZMQ :30556):
#
#   C3 robot pods
#     → vm2:30051/30556  (socat on the host)
#     → robot-party container  (enters bridged LAN at BR5)
#          ↓  L2 traffic through bridges: BR5 → BR3 → BR1  (STP path)
#     → lan2-host container  (exits bridged LAN at BR1)
#     → C2 inventory  172.16.2.136:30051/30556
#
# This ensures all robot↔inventory traffic traverses the bridged topology.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
C2_INVENTORY="172.16.2.136"
GRPC_PORT=30051
ZMQ_PORT=30556

PREFIX="clab-pa3-bridged-lans"
ENTRY_HOST="robot-party"          # enters bridged LAN on BR5 (far side)
EXIT_HOST="lan2-host"             # exits bridged LAN on BR1 (near C2)
EXIT_BRIDGE_IP="192.168.100.1"    # lan2-host IP on the bridged network

# ── Get Docker management IPs ───────────────────────────────────────────────
ENTRY_MGMT_IP=$(docker inspect "$PREFIX-$ENTRY_HOST" \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
    | tr ',' '\n' | grep '172.20' | head -1)

echo "Entry host ($ENTRY_HOST) mgmt IP: $ENTRY_MGMT_IP"
echo "Exit  host ($EXIT_HOST)  bridge IP: $EXIT_BRIDGE_IP"
echo "Destination: $C2_INVENTORY:$GRPC_PORT / $C2_INVENTORY:$ZMQ_PORT"
echo ""

# ── Kill existing socat processes ────────────────────────────────────────────
echo "Stopping any existing socat processes..."
pkill -9 socat 2>/dev/null || true
docker exec "$PREFIX-$ENTRY_HOST" pkill -9 socat 2>/dev/null || true
docker exec "$PREFIX-$EXIT_HOST" pkill -9 socat 2>/dev/null || true
sleep 1

# ── Leg 3 (innermost): lan2-host listens, forwards to C2 inventory ──────────
# lan2-host receives traffic on the bridged network and sends it out to C2
# via the Docker management network (eth0).

echo "[$EXIT_HOST] socat :$GRPC_PORT → $C2_INVENTORY:$GRPC_PORT"
docker exec -d "$PREFIX-$EXIT_HOST" \
    socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${C2_INVENTORY}:${GRPC_PORT}

echo "[$EXIT_HOST] socat :$ZMQ_PORT → $C2_INVENTORY:$ZMQ_PORT"
docker exec -d "$PREFIX-$EXIT_HOST" \
    socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${C2_INVENTORY}:${ZMQ_PORT}
sleep 1

# ── Leg 2 (middle): robot-party listens, forwards to lan2-host ──────────────
# Traffic from robot-party (192.168.100.50) to lan2-host (192.168.100.1)
# traverses the bridged L2 network: BR5 → BR3 → BR1 (STP shortest path).

echo "[$ENTRY_HOST] socat :$GRPC_PORT → $EXIT_BRIDGE_IP:$GRPC_PORT  (through bridges)"
docker exec -d "$PREFIX-$ENTRY_HOST" \
    socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${EXIT_BRIDGE_IP}:${GRPC_PORT}

echo "[$ENTRY_HOST] socat :$ZMQ_PORT → $EXIT_BRIDGE_IP:$ZMQ_PORT  (through bridges)"
docker exec -d "$PREFIX-$ENTRY_HOST" \
    socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${EXIT_BRIDGE_IP}:${ZMQ_PORT}
sleep 1

# ── Leg 1 (outermost): VM host listens, forwards to robot-party container ───
# Robot pods on C3 connect here (via EndpointSlice or direct IP).

echo "[vm host] socat :$GRPC_PORT → $ENTRY_MGMT_IP:$GRPC_PORT"
socat TCP4-LISTEN:${GRPC_PORT},fork,reuseaddr TCP4:${ENTRY_MGMT_IP}:${GRPC_PORT} &

echo "[vm host] socat :$ZMQ_PORT → $ENTRY_MGMT_IP:$ZMQ_PORT"
socat TCP4-LISTEN:${ZMQ_PORT},fork,reuseaddr TCP4:${ENTRY_MGMT_IP}:${ZMQ_PORT} &
sleep 2

# ── Verify ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Bridged LAN relay chain is up ==="
echo ""
echo "gRPC path: vm:$GRPC_PORT → $ENTRY_HOST($ENTRY_MGMT_IP)"
echo "           → bridges (BR5→BR3→BR1) → $EXIT_HOST($EXIT_BRIDGE_IP)"
echo "           → C2 inventory ($C2_INVENTORY:$GRPC_PORT)"
echo ""
echo "ZMQ  path: vm:$ZMQ_PORT → $ENTRY_HOST($ENTRY_MGMT_IP)"
echo "           → bridges (BR5→BR3→BR1) → $EXIT_HOST($EXIT_BRIDGE_IP)"
echo "           → C2 inventory ($C2_INVENTORY:$ZMQ_PORT)"
echo ""
echo "Point robot pods at this VM's IP on ports $GRPC_PORT/$ZMQ_PORT."
echo "Use k8s/c3-robots-bridged.yaml or update the EndpointSlice."

#!/bin/bash
# Start socat relay chain for backup WAN (containerlab3)
# Traffic: vm1:30501 -> lan1-host -> OSPF routers -> lan2-host -> C3 ordering (172.16.3.137:30500)

set -euo pipefail

C3_ORDERING="172.16.3.137:30500"
LISTEN_PORT=30502

LAN1_HOST_IP=$(sudo docker inspect clab-pa4-backup-wan-lan1-host \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' \
    | tr ' ' '\n' | grep '172.20' | head -1)
LAN2_HOST_IP=$(sudo docker inspect clab-pa4-backup-wan-lan2-host \
    --format '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' \
    | tr ' ' '\n' | grep '172.20' | head -1)

echo "lan1-host IP: $LAN1_HOST_IP"
echo "lan2-host IP: $LAN2_HOST_IP"

# Kill any existing socat on port 30501
pkill -f "socat.*30502" 2>/dev/null || true
sudo docker exec clab-pa4-backup-wan-lan1-host pkill -9 socat 2>/dev/null || true
sudo docker exec clab-pa4-backup-wan-lan2-host pkill -9 socat 2>/dev/null || true
sleep 1

# socat in lan2-host: forward to C3 ordering
echo "Starting socat in lan2-host -> $C3_ORDERING ..."
sudo docker exec -d clab-pa4-backup-wan-lan2-host \
    socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:${C3_ORDERING}
sleep 1

# socat in lan1-host: forward to lan2-host via OSPF (use LAN2 IP, not management IP)
echo "Starting socat in lan1-host -> 10.8.0.2:${LISTEN_PORT} via OSPF ..."
sudo docker exec -d clab-pa4-backup-wan-lan1-host \
    socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:10.8.0.2:${LISTEN_PORT}
sleep 1

# socat on vm1: listen on 30501, forward to lan1-host
echo "Starting socat on vm1:${LISTEN_PORT} -> ${LAN1_HOST_IP}:${LISTEN_PORT} ..."
socat TCP4-LISTEN:${LISTEN_PORT},fork,reuseaddr TCP4:${LAN1_HOST_IP}:${LISTEN_PORT} &
sleep 2

echo ""
echo "=== Backup WAN relay chain is up ==="
echo "Traffic: vm1:${LISTEN_PORT} -> lan1-host(${LAN1_HOST_IP}) -> OSPF -> lan2-host(10.8.0.2) -> C3(${C3_ORDERING})"

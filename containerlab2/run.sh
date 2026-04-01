#!/bin/bash
# Deploy ContainerLab 2 (Bridged LANs) and configure everything.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Deploying ContainerLab 2 (Bridged LANs) ==="
sudo clab deploy -t bridgelab.clab.yml

echo ""
echo "=== Configuring bridges (STP + costs) ==="
./setup-bridges.sh

echo ""
echo "=== Configuring host IPs ==="
./setup-hosts.sh

echo ""
echo "=== Generating traffic to trigger MAC learning ==="
PREFIX="clab-pa3-bridged-lans"
echo "Pinging from lan2-host to all robots..."
for ip in 192.168.100.10 192.168.100.20 192.168.100.30 192.168.100.40 192.168.100.50; do
    sudo docker exec "$PREFIX-lan2-host" ping -c 2 -W 2 "$ip" >/dev/null 2>&1 && echo "  $ip reachable" || echo "  $ip unreachable"
done

echo ""
echo "=== Deployment complete ==="
echo "Run ./collect-tables.sh to see bridge/STP/ARP state."

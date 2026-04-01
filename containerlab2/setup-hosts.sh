#!/bin/bash
# Assign IP addresses to all host nodes after bridges are configured.
# All hosts share 192.168.100.0/24 (single L2 broadcast domain via bridges).
#
# Run after: ./setup-bridges.sh

set -euo pipefail
PREFIX="clab-pa3-bridged-lans"

configure_host() {
    local node=$1 ip=$2
    echo "[$node] Assigning $ip/24 on eth1..."
    sudo docker exec "$PREFIX-$node" ip link set eth1 up
    sudo docker exec "$PREFIX-$node" ip addr add "$ip/24" dev eth1
}

# Entry point from K8s Cluster 2
configure_host lan2-host     192.168.100.1

# Robot proxies
configure_host robot-bread   192.168.100.10
configure_host robot-dairy   192.168.100.20
configure_host robot-meat    192.168.100.30
configure_host robot-produce 192.168.100.40
configure_host robot-party   192.168.100.50

echo ""
echo "All hosts configured. Test connectivity with:"
echo "  sudo docker exec $PREFIX-lan2-host ping -c2 192.168.100.50"

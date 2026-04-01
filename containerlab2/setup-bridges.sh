#!/bin/bash
# Configure bridges after ContainerLab deploy.
# Creates br0 on each bridge node, enables STP, adds interfaces, sets costs.
#
# Run after: sudo clab deploy -t bridgelab.clab.yml

set -euo pipefail
PREFIX="clab-pa3-bridged-lans"

install_and_create_bridge() {
    local node=$1 priority=$2
    shift 2
    # remaining args are pairs: "ethN cost"

    echo "[$node] Installing bridge-utils and configuring br0 (priority $priority)..."
    sudo docker exec "$PREFIX-$node" sh -c "apk add --no-cache -q bridge-utils iproute2 2>/dev/null"
    sudo docker exec "$PREFIX-$node" brctl addbr br0
    sudo docker exec "$PREFIX-$node" brctl stp br0 on
    sudo docker exec "$PREFIX-$node" brctl setbridgeprio br0 "$priority"

    while [ $# -ge 2 ]; do
        local iface=$1 cost=$2
        shift 2
        sudo docker exec "$PREFIX-$node" ip link set "$iface" up
        sudo docker exec "$PREFIX-$node" brctl addif br0 "$iface"
        sudo docker exec "$PREFIX-$node" brctl setpathcost br0 "$iface" "$cost"
    done

    sudo docker exec "$PREFIX-$node" ip link set br0 up
}

# BR1 – root bridge (lowest priority)
#   eth1→BR2(10)  eth2→BR3(20)  eth3→lan2-host(4)  eth4→robot-bread(4)
install_and_create_bridge br1 4096 \
    eth1 10  eth2 20  eth3 4  eth4 4

# BR2
#   eth1→BR1(10)  eth2→BR4(15)  eth3→robot-dairy(4)
install_and_create_bridge br2 8192 \
    eth1 10  eth2 15  eth3 4

# BR3
#   eth1→BR1(20)  eth2→BR4(25)  eth3→BR5(10)  eth4→robot-meat(4)
install_and_create_bridge br3 12288 \
    eth1 20  eth2 25  eth3 10  eth4 4

# BR4
#   eth1→BR2(15)  eth2→BR3(25)  eth3→BR5(30)  eth4→robot-produce(4)
install_and_create_bridge br4 16384 \
    eth1 15  eth2 25  eth3 30  eth4 4

# BR5
#   eth1→BR3(10)  eth2→BR4(30)  eth3→robot-party(4)
install_and_create_bridge br5 20480 \
    eth1 10  eth2 30  eth3 4

echo ""
echo "All bridges configured. Waiting 30s for STP convergence..."
sleep 30
echo "STP should have converged. Run collect-tables.sh to inspect state."

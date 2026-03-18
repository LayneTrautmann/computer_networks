#!/bin/sh

# Configure the two Linux host containers after ContainerLab deploy
# Run this after: sudo clab deploy -t frrlab.clab.yml

# lan1-host: on LAN1, gateway is router4 (10.2.0.1)
sudo docker exec -d clab-pa3-wan-lan1-host ip link set eth1 up
sudo docker exec -d clab-pa3-wan-lan1-host ip addr add 10.2.0.2/24 dev eth1
# Route all WAN and LAN2 traffic through router4
sudo docker exec -d clab-pa3-wan-lan1-host ip route add 10.0.0.0/8 via 10.2.0.1 dev eth1

# lan2-host: on LAN2, gateway is router6 (10.4.0.1)
sudo docker exec -d clab-pa3-wan-lan2-host ip link set eth1 up
sudo docker exec -d clab-pa3-wan-lan2-host ip addr add 10.4.0.2/24 dev eth1
# Route all WAN and LAN1 traffic through router6
sudo docker exec -d clab-pa3-wan-lan2-host ip route add 10.0.0.0/8 via 10.4.0.1 dev eth1

#!/bin/sh

# Configure the two Linux host containers after ContainerLab deploy
# Run this after: sudo clab deploy -t frrlab-backup.clab.yml

# lan1-host: on LAN1 (10.6.0.0/24), gateway is router4 (10.6.0.1)
sudo docker exec -d clab-pa4-backup-wan-lan1-host ip link set eth1 up
sudo docker exec -d clab-pa4-backup-wan-lan1-host ip addr add 10.6.0.2/24 dev eth1
sudo docker exec -d clab-pa4-backup-wan-lan1-host ip route add 10.0.0.0/8 via 10.6.0.1 dev eth1

# lan2-host: on LAN2 (10.8.0.0/24), gateway is router6 (10.8.0.1)
sudo docker exec -d clab-pa4-backup-wan-lan2-host ip link set eth1 up
sudo docker exec -d clab-pa4-backup-wan-lan2-host ip addr add 10.8.0.2/24 dev eth1
sudo docker exec -d clab-pa4-backup-wan-lan2-host ip route add 10.0.0.0/8 via 10.8.0.1 dev eth1

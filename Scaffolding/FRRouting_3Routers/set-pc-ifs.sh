#!/bin/sh
# Taken from lab examples
# Here, we enable eth1 on all the PCs, assign them an IP
# address in their network, and update their routing table
#
# Note that "sudo" will not be needed if the clab user is
# already in the docker group.
#
# Following are on PC1
sudo docker exec -d clab-frrlab-pc1 ip link set eth1 up
sudo docker exec -d clab-frrlab-pc1 ip addr add 172.16.1.2/24 dev eth1
sudo docker exec -d clab-frrlab-pc1 ip route add 172.16.0.0/16 via 172.16.1.1 dev eth1
sudo docker exec -d clab-frrlab-pc1 ip route add 10.0.0.0/16 via 172.16.1.1 dev eth1
#
# Following are on PC2
sudo docker exec -d clab-frrlab-pc2 ip link set eth1 up
sudo docker exec -d clab-frrlab-pc2 ip addr add 172.16.2.2/24 dev eth1
sudo docker exec -d clab-frrlab-pc2 ip route add 172.16.0.0/16 via 172.16.2.1 dev eth1
sudo docker exec -d clab-frrlab-pc2 ip route add 10.0.0.0/16 via 172.16.2.1 dev eth1
#
# Following are on PC3
sudo docker exec -d clab-frrlab-pc3 ip link set eth1 up
sudo docker exec -d clab-frrlab-pc3 ip addr add 172.16.3.2/24 dev eth1
sudo docker exec -d clab-frrlab-pc3 ip route add 172.16.0.0/16 via 172.16.3.1 dev eth1
sudo docker exec -d clab-frrlab-pc3 ip route add 10.0.0.0/16 via 172.16.3.1 dev eth1


#!/bin/bash
set -e

cd "$(dirname "$0")"

sudo clab deploy -t frrlab-backup.clab.yml
sleep 10
./set-host-ifs.sh

echo "Backup WAN deployed. Verify OSPF with:"
echo "  sudo docker exec -it clab-pa4-backup-wan-router4 traceroute 10.8.0.2"
echo "  Expected path: R4->R1->R5->R2->R6 (cost 70)"

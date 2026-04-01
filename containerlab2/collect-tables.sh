#!/bin/bash
# Collect bridge forwarding tables, STP state, and ARP tables from all nodes.
# Use this to demonstrate bridge learning and satisfy Milestone 2 deliverables.

set -euo pipefail
PREFIX="clab-pa3-bridged-lans"

BRIDGES="br1 br2 br3 br4 br5"
HOSTS="lan2-host robot-bread robot-dairy robot-meat robot-produce robot-party"

echo "============================================"
echo " STP State (Spanning Tree)"
echo "============================================"
for br in $BRIDGES; do
    echo ""
    echo "--- $br: brctl showstp br0 ---"
    sudo docker exec "$PREFIX-$br" brctl showstp br0
done

echo ""
echo "============================================"
echo " Bridge Forwarding Tables (MAC learning)"
echo "============================================"
for br in $BRIDGES; do
    echo ""
    echo "--- $br: brctl showmacs br0 ---"
    sudo docker exec "$PREFIX-$br" brctl showmacs br0
done

echo ""
echo "============================================"
echo " ARP Tables"
echo "============================================"
for node in $BRIDGES $HOSTS; do
    echo ""
    echo "--- $node: ip neigh show ---"
    sudo docker exec "$PREFIX-$node" ip neigh show 2>/dev/null || true
done

echo ""
echo "============================================"
echo " Bridge Link Details"
echo "============================================"
for br in $BRIDGES; do
    echo ""
    echo "--- $br: bridge link show ---"
    sudo docker exec "$PREFIX-$br" bridge link show 2>/dev/null || true
done

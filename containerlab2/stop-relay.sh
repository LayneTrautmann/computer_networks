#!/bin/bash
# Stop all socat relay processes (on VM host and inside containers).

set -euo pipefail
PREFIX="clab-pa3-bridged-lans"

echo "Stopping socat on VM host..."
pkill -9 socat 2>/dev/null || true

echo "Stopping socat in containers..."
for node in lan2-host robot-party; do
    docker exec "$PREFIX-$node" pkill -9 socat 2>/dev/null || true
done

echo "All socat relays stopped."

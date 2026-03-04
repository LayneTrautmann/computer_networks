#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# configure-wan.sh – Apply tc-netem WAN emulation rules to ContainerLab nodes
#
# Usage:
#   ./configure-wan.sh <scenario>
#
# Scenarios:
#   none       – Remove all WAN emulation (baseline)
#   low        – 10 ms delay, 1 ms jitter, 0.1% loss
#   medium     – 50 ms delay, 5 ms jitter, 0.5% loss
#   high       – 100 ms delay, 10 ms jitter, 1% loss
#   extreme    – 200 ms delay, 25 ms jitter, 2% loss
#   custom     – Reads DELAY, JITTER, LOSS env vars
#
# The script applies symmetric netem rules on the internal eth2 interfaces
# of all four WAN router containers (traffic in both directions is shaped).
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCENARIO="${1:-none}"

CONTAINERS=(
    "clab-grocery-wan-wan-router"
)
IFACE="eth1"

apply_netem() {
    local delay="$1" jitter="$2" loss="$3"
    echo "Applying WAN emulation: delay=${delay}ms jitter=${jitter}ms loss=${loss}%"
    for ctr in "${CONTAINERS[@]}"; do
        echo "  -> ${ctr}:${IFACE}"
        # Clear existing qdisc (ignore error if none set)
        docker exec "$ctr" tc qdisc del dev "$IFACE" root 2>/dev/null || true
        docker exec "$ctr" tc qdisc add dev "$IFACE" root netem \
            delay "${delay}ms" "${jitter}ms" distribution normal \
            loss "${loss}%"
    done
    echo "Done."
}

clear_netem() {
    echo "Clearing all WAN emulation rules (baseline)."
    for ctr in "${CONTAINERS[@]}"; do
        echo "  -> ${ctr}:${IFACE}"
        docker exec "$ctr" tc qdisc del dev "$IFACE" root 2>/dev/null || true
    done
    echo "Done."
}

case "$SCENARIO" in
    none)
        clear_netem
        ;;
    low)
        apply_netem 10 1 0.1
        ;;
    medium)
        apply_netem 50 5 0.5
        ;;
    high)
        apply_netem 100 10 1
        ;;
    extreme)
        apply_netem 200 25 2
        ;;
    custom)
        DELAY="${DELAY:-50}"
        JITTER="${JITTER:-5}"
        LOSS="${LOSS:-0.5}"
        apply_netem "$DELAY" "$JITTER" "$LOSS"
        ;;
    *)
        echo "Unknown scenario: $SCENARIO"
        echo "Usage: $0 {none|low|medium|high|extreme|custom}"
        exit 1
        ;;
esac

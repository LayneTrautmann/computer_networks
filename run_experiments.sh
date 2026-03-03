#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# run_experiments.sh – Automated experiment runner for PA2 Milestone 3
#
# Runs Locust load tests under multiple WAN scenarios and collects the
# analytics CSVs into analytics_service/scenarios/ for comparison plotting.
#
# Usage:
#   ./run_experiments.sh [ordering-service-url]
#
# Default ordering service URL: http://172.16.2.136:30500
#
# What it does for each scenario:
#   1. Configure WAN emulation via containerlab/configure-wan.sh
#   2. Clear the analytics CSV
#   3. Run Locust headless for the configured duration
#   4. Copy the analytics CSV into scenarios/<scenario_name>.csv
#   5. Copy the Locust stats CSV into scenarios/<scenario_name>_locust.csv
#
# After all scenarios, it runs plot.py to generate comparison graphs.
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

HOST="${1:-http://172.16.2.136:30500}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ANALYTICS_CSV="${SCRIPT_DIR}/analytics_service/analytics_data.csv"
SCENARIO_DIR="${SCRIPT_DIR}/analytics_service/scenarios"
LOCUST_FILE="${SCRIPT_DIR}/locustfile.py"
WAN_SCRIPT="${SCRIPT_DIR}/containerlab/configure-wan.sh"

USERS="${LOCUST_USERS:-50}"
SPAWN_RATE="${LOCUST_SPAWN_RATE:-5}"
DURATION="${LOCUST_DURATION:-60s}"

# Scenarios: name -> WAN configure-wan.sh argument
declare -A SCENARIOS=(
    ["01_no_containerlab"]="none"
    ["02_wan_low_10ms"]="low"
    ["03_wan_medium_50ms"]="medium"
    ["04_wan_high_100ms"]="high"
    ["05_wan_extreme_200ms"]="extreme"
)

mkdir -p "$SCENARIO_DIR"

echo "============================================"
echo "  PA2 Milestone 3 – Experiment Runner"
echo "============================================"
echo "Target host:    $HOST"
echo "Users:          $USERS"
echo "Spawn rate:     $SPAWN_RATE"
echo "Duration:       $DURATION"
echo "Scenarios:      ${!SCENARIOS[*]}"
echo "Output dir:     $SCENARIO_DIR"
echo "============================================"
echo ""

for scenario in $(echo "${!SCENARIOS[@]}" | tr ' ' '\n' | sort); do
    wan_setting="${SCENARIOS[$scenario]}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Scenario: ${scenario}  (WAN: ${wan_setting})"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Step 1: Configure WAN
    echo "[1/4] Configuring WAN emulation..."
    if [ -x "$WAN_SCRIPT" ]; then
        bash "$WAN_SCRIPT" "$wan_setting"
    else
        echo "  (WAN script not executable or not found – skipping WAN config)"
    fi

    # Step 2: Clear analytics CSV
    echo "[2/4] Clearing analytics CSV..."
    rm -f "$ANALYTICS_CSV"

    # Allow WAN changes to stabilize
    sleep 3

    # Step 3: Run Locust
    echo "[3/4] Running Locust (users=${USERS}, duration=${DURATION})..."
    locust -f "$LOCUST_FILE" \
        --host="$HOST" \
        --headless \
        -u "$USERS" \
        -r "$SPAWN_RATE" \
        -t "$DURATION" \
        --csv="${SCENARIO_DIR}/${scenario}_locust" \
        2>&1 | tail -5

    # Step 4: Collect results
    echo "[4/4] Collecting results..."
    if [ -f "$ANALYTICS_CSV" ]; then
        cp "$ANALYTICS_CSV" "${SCENARIO_DIR}/${scenario}.csv"
        ROWS=$(wc -l < "${SCENARIO_DIR}/${scenario}.csv")
        echo "  Saved ${ROWS} rows to scenarios/${scenario}.csv"
    else
        echo "  WARNING: Analytics CSV not found – analytics service may not be running"
    fi

    echo "  Scenario ${scenario} complete."
done

echo ""
echo "============================================"
echo "  All experiments complete!"
echo "============================================"
echo ""

# Generate plots
echo "Generating comparison plots..."
export SCENARIO_CSV_DIR="$SCENARIO_DIR"
python "${SCRIPT_DIR}/analytics_service/plot.py"

echo ""
echo "Results saved in:"
echo "  - Scenario CSVs: ${SCENARIO_DIR}/"
echo "  - Plots:         ${SCRIPT_DIR}/analytics_service/plots/"
echo ""
echo "Done!"

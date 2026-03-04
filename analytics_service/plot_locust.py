"""
Plot tail latency comparisons from Locust stats CSVs.
Reads *_stats.csv files from the scenarios/ directory and generates:
  1. Grouped bar chart of P50/P90/P95/P99 across scenarios
  2. Summary table image
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCENARIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
PERCENTILES = [50, 90, 95, 99]
PERCENTILE_COLORS = {50: "#2196F3", 90: "#FF9800", 95: "#F44336", 99: "#9C27B0"}

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_scenarios():
    scenarios = {}
    for path in sorted(glob.glob(os.path.join(SCENARIO_DIR, "*_stats.csv"))):
        name = os.path.basename(path).replace("_stats.csv", "")
        df = pd.read_csv(path)
        # Get the Aggregated row
        agg = df[df["Name"] == "Aggregated"]
        if agg.empty:
            agg = df[df["Type"] == ""]
        if not agg.empty:
            row = agg.iloc[0]
            scenarios[name] = {
                50: float(row["50%"]) / 1000,   # ms -> seconds
                90: float(row["90%"]) / 1000,
                95: float(row["95%"]) / 1000,
                99: float(row["99%"]) / 1000,
                "count": int(row["Request Count"]),
                "mean": float(row["Average Response Time"]) / 1000,
            }
    return scenarios

scenarios = load_scenarios()
if not scenarios:
    print("No scenario CSVs found in", SCENARIO_DIR)
    exit(1)

print(f"Found {len(scenarios)} scenarios: {list(scenarios.keys())}")

# ── Grouped bar chart ────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
n = len(scenarios)
n_p = len(PERCENTILES)
bar_width = 0.8 / n_p
x = np.arange(n)

for i, p in enumerate(PERCENTILES):
    vals = [scenarios[s][p] for s in scenarios]
    offset = (i - n_p / 2 + 0.5) * bar_width
    bars = ax.bar(x + offset, vals, bar_width, label=f"P{p}",
                  color=PERCENTILE_COLORS[p], edgecolor="black", alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{v:.1f}s", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels([s.replace("_", "\n") for s in scenarios], fontsize=9)
ax.set_ylabel("Latency (seconds)")
ax.set_title("Tail Latency Percentiles by WAN Scenario")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
out = os.path.join(OUTPUT_DIR, "wan_percentile_bars.png")
fig.savefig(out, dpi=150)
plt.close(fig)
print(f"  -> {out}")

# ── Summary table ────────────────────────────────────────────────────────────
col_labels = ["Scenario", "Requests", "Mean (s)", "P50 (s)", "P90 (s)", "P95 (s)", "P99 (s)"]
rows = []
for name, s in scenarios.items():
    rows.append([
        name, str(s["count"]),
        f"{s['mean']:.2f}",
        f"{s[50]:.2f}",
        f"{s[90]:.2f}",
        f"{s[95]:.2f}",
        f"{s[99]:.2f}",
    ])

fig, ax = plt.subplots(figsize=(13, 1 + 0.5 * len(rows)))
ax.axis("off")
table = ax.table(cellText=rows, colLabels=col_labels, loc="center", cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.6)
for j in range(len(col_labels)):
    table[0, j].set_facecolor("#4472C4")
    table[0, j].set_text_props(color="white", fontweight="bold")
ax.set_title("WAN Scenario Tail Latency Summary", fontsize=13, fontweight="bold", pad=20)
fig.tight_layout()
out = os.path.join(OUTPUT_DIR, "wan_summary_table.png")
fig.savefig(out, dpi=150)
plt.close(fig)
print(f"  -> {out}")

# ── Line chart: P50/P99 trend across scenarios ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
names = list(scenarios.keys())
for p, color in PERCENTILE_COLORS.items():
    vals = [scenarios[s][p] for s in names]
    ax.plot(names, vals, marker="o", label=f"P{p}", color=color, linewidth=2)

ax.set_xlabel("Scenario")
ax.set_ylabel("Latency (seconds)")
ax.set_title("Latency Percentiles Across WAN Scenarios")
ax.legend()
ax.grid(True, alpha=0.3)
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
out = os.path.join(OUTPUT_DIR, "wan_latency_trend.png")
fig.savefig(out, dpi=150)
plt.close(fig)
print(f"  -> {out}")

print(f"\nAll plots saved to {OUTPUT_DIR}/")

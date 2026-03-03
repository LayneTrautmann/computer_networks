"""
Analytics Plotting Script
Reads CSV data collected by the Analytics Service and generates:
  1. Latency distribution (histogram)
  2. Latency over time (line chart)
  3. Latency by order type (box plot)
  4. Request outcome breakdown (bar chart)
  5. Summary statistics table
  6. CDF of tail latencies with P50/P90/P95/P99 markers
  7. CDF by order type
  8. Multi-scenario CDF comparison (with vs without ContainerLab HIL)
  9. Throughput over time
"""

import os
import sys
import glob

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV_PATH = os.environ.get(
    "ANALYTICS_CSV_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics_data.csv"),
)

OUTPUT_DIR = os.environ.get(
    "ANALYTICS_PLOT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots"),
)

PERCENTILES = [50, 90, 95, 99]
PERCENTILE_COLORS = {50: "#2196F3", 90: "#FF9800", 95: "#F44336", 99: "#9C27B0"}


def load_data(path):
    if not os.path.exists(path):
        print(f"Error: CSV file not found at {path}")
        print("Run the analytics service and send some orders first.")
        sys.exit(1)

    df = pd.read_csv(path)
    if df.empty:
        print("Error: CSV file is empty. Send some orders first.")
        sys.exit(1)

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["latency_seconds"] = df["latency_seconds"].astype(float)
    return df


# ── Original PA1 plots ───────────────────────────────────────────────────────

def plot_latency_histogram(df, output_dir):
    """Distribution of end-to-end latencies."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df["latency_seconds"], bins=30, edgecolor="black", alpha=0.7, color="steelblue")
    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Number of Requests")
    ax.set_title("End-to-End Latency Distribution")
    ax.axvline(df["latency_seconds"].mean(), color="red", linestyle="--",
               label=f'Mean: {df["latency_seconds"].mean():.4f}s')
    ax.axvline(df["latency_seconds"].median(), color="green", linestyle="--",
               label=f'Median: {df["latency_seconds"].median():.4f}s')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "latency_histogram.png"), dpi=150)
    plt.close(fig)
    print("  -> latency_histogram.png")


def plot_latency_over_time(df, output_dir):
    """Latency over time for each request."""
    fig, ax = plt.subplots(figsize=(10, 5))

    grocery = df[df["order_type"] == "GROCERY_ORDER"]
    restock = df[df["order_type"] == "RESTOCK_ORDER"]

    if not grocery.empty:
        ax.plot(grocery["timestamp"], grocery["latency_seconds"],
                "o-", label="Grocery Order", markersize=4, alpha=0.8)
    if not restock.empty:
        ax.plot(restock["timestamp"], restock["latency_seconds"],
                "s-", label="Restock Order", markersize=4, alpha=0.8)

    ax.set_xlabel("Time")
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("End-to-End Latency Over Time")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "latency_over_time.png"), dpi=150)
    plt.close(fig)
    print("  -> latency_over_time.png")


def plot_latency_by_type(df, output_dir):
    """Box plot comparing latency by order type."""
    fig, ax = plt.subplots(figsize=(7, 5))

    types = df["order_type"].unique()
    data = [df[df["order_type"] == t]["latency_seconds"].values for t in types]
    labels = [t.replace("_", " ").title() for t in types]

    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    colors = ["steelblue", "coral"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Latency by Order Type")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "latency_by_type.png"), dpi=150)
    plt.close(fig)
    print("  -> latency_by_type.png")


def plot_outcome_breakdown(df, output_dir):
    """Bar chart of request outcomes by order type."""
    fig, ax = plt.subplots(figsize=(7, 5))

    grouped = df.groupby(["order_type", "status"]).size().unstack(fill_value=0)
    grouped.index = [idx.replace("_", " ").title() for idx in grouped.index]

    grouped.plot(kind="bar", ax=ax, edgecolor="black", alpha=0.8)
    ax.set_xlabel("Order Type")
    ax.set_ylabel("Count")
    ax.set_title("Request Outcomes by Order Type")
    ax.legend(title="Status")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "outcome_breakdown.png"), dpi=150)
    plt.close(fig)
    print("  -> outcome_breakdown.png")


def plot_summary_table(df, output_dir):
    """Summary statistics table as an image."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")

    latency = df["latency_seconds"]
    summary = {
        "Metric": [
            "Total Requests",
            "Grocery Orders",
            "Restock Orders",
            "OK Responses",
            "BAD_REQUEST Responses",
            "Mean Latency (s)",
            "Median Latency (s)",
            "P90 Latency (s)",
            "P95 Latency (s)",
            "P99 Latency (s)",
            "Min Latency (s)",
            "Max Latency (s)",
            "Std Dev Latency (s)",
        ],
        "Value": [
            len(df),
            len(df[df["order_type"] == "GROCERY_ORDER"]),
            len(df[df["order_type"] == "RESTOCK_ORDER"]),
            len(df[df["status"] == "OK"]),
            len(df[df["status"] == "BAD_REQUEST"]),
            f"{latency.mean():.4f}",
            f"{latency.median():.4f}",
            f"{np.percentile(latency, 90):.4f}",
            f"{np.percentile(latency, 95):.4f}",
            f"{np.percentile(latency, 99):.4f}",
            f"{latency.min():.4f}",
            f"{latency.max():.4f}",
            f"{latency.std():.4f}",
        ],
    }

    table = ax.table(
        cellText=list(zip(summary["Metric"], summary["Value"])),
        colLabels=["Metric", "Value"],
        loc="center",
        cellLoc="left",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)

    ax.set_title("Analytics Summary", fontsize=13, fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_table.png"), dpi=150)
    plt.close(fig)
    print("  -> summary_table.png")


# ── PA2 Milestone 3: CDF / Tail Latency plots ───────────────────────────────

def plot_cdf(df, output_dir):
    """CDF of all latencies with P50, P90, P95, P99 vertical markers."""
    latency = np.sort(df["latency_seconds"].values)
    cdf = np.arange(1, len(latency) + 1) / len(latency)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(latency, cdf, linewidth=2, color="#333333", label="CDF")

    for p in PERCENTILES:
        val = np.percentile(latency, p)
        ax.axvline(val, linestyle="--", color=PERCENTILE_COLORS[p], linewidth=1.5,
                   label=f"P{p}: {val:.4f}s")
        ax.axhline(p / 100, linestyle=":", color=PERCENTILE_COLORS[p], alpha=0.3)

    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title("CDF of End-to-End Latency (Tail Latencies)")
    ax.legend(loc="lower right")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "cdf_latency.png"), dpi=150)
    plt.close(fig)
    print("  -> cdf_latency.png")


def plot_cdf_by_type(df, output_dir):
    """Separate CDF curves for each order type with tail-latency markers."""
    fig, ax = plt.subplots(figsize=(9, 6))
    type_colors = {"GROCERY_ORDER": "steelblue", "RESTOCK_ORDER": "coral"}

    for otype in df["order_type"].unique():
        sub = df[df["order_type"] == otype]
        latency = np.sort(sub["latency_seconds"].values)
        cdf = np.arange(1, len(latency) + 1) / len(latency)
        color = type_colors.get(otype, "gray")
        label = otype.replace("_", " ").title()
        ax.plot(latency, cdf, linewidth=2, color=color, label=label)

        for p in [90, 99]:
            val = np.percentile(latency, p)
            ax.axvline(val, linestyle="--", color=color, alpha=0.5, linewidth=1)
            ax.annotate(f"P{p}: {val:.3f}s", xy=(val, p / 100),
                        fontsize=8, color=color,
                        xytext=(5, -10), textcoords="offset points")

    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title("CDF of Latency by Order Type")
    ax.legend(loc="lower right")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "cdf_latency_by_type.png"), dpi=150)
    plt.close(fig)
    print("  -> cdf_latency_by_type.png")


def plot_throughput_over_time(df, output_dir):
    """Requests per second over time."""
    fig, ax = plt.subplots(figsize=(10, 5))

    df_sorted = df.sort_values("timestamp")
    df_sorted = df_sorted.set_index("timestamp")
    throughput = df_sorted.resample("1s").size()

    ax.plot(throughput.index, throughput.values, color="steelblue", linewidth=1.5)
    ax.fill_between(throughput.index, throughput.values, alpha=0.2, color="steelblue")
    ax.set_xlabel("Time")
    ax.set_ylabel("Requests / second")
    ax.set_title("Throughput Over Time")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "throughput_over_time.png"), dpi=150)
    plt.close(fig)
    print("  -> throughput_over_time.png")


# ── Multi-scenario comparison (with vs without ContainerLab) ─────────────────

def _load_scenario_csvs(scenario_dir):
    """Load all CSV files from a directory as {scenario_name: DataFrame}."""
    scenarios = {}
    csv_files = sorted(glob.glob(os.path.join(scenario_dir, "*.csv")))
    for path in csv_files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            df = pd.read_csv(path)
            if not df.empty and "latency_seconds" in df.columns:
                df["latency_seconds"] = df["latency_seconds"].astype(float)
                scenarios[name] = df
        except Exception as e:
            print(f"  Warning: could not load {path}: {e}")
    return scenarios


def plot_cdf_comparison(scenarios, output_dir):
    """Overlay CDF curves from multiple experiment scenarios on one plot."""
    if not scenarios:
        print("  (skipped cdf_comparison – no scenario CSVs found)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = plt.cm.get_cmap("tab10", max(len(scenarios), 1))

    for idx, (name, df) in enumerate(scenarios.items()):
        latency = np.sort(df["latency_seconds"].values)
        cdf = np.arange(1, len(latency) + 1) / len(latency)
        ax.plot(latency, cdf, linewidth=2, color=cmap(idx), label=name)

    for p in [50, 90, 95, 99]:
        ax.axhline(p / 100, linestyle=":", color="gray", alpha=0.4)
        ax.text(ax.get_xlim()[0], p / 100 + 0.01, f"P{p}", fontsize=8, color="gray")

    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title("CDF Comparison Across Scenarios\n(With vs Without ContainerLab HIL)")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "cdf_comparison.png"), dpi=150)
    plt.close(fig)
    print("  -> cdf_comparison.png")


def plot_percentile_bars(scenarios, output_dir):
    """Grouped bar chart of P50/P90/P95/P99 across scenarios."""
    if not scenarios:
        print("  (skipped percentile_bars – no scenario CSVs found)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    n_scenarios = len(scenarios)
    n_percentiles = len(PERCENTILES)
    bar_width = 0.8 / n_percentiles
    x = np.arange(n_scenarios)

    for i, p in enumerate(PERCENTILES):
        vals = [np.percentile(df["latency_seconds"], p) for df in scenarios.values()]
        offset = (i - n_percentiles / 2 + 0.5) * bar_width
        bars = ax.bar(x + offset, vals, bar_width, label=f"P{p}",
                      color=PERCENTILE_COLORS[p], edgecolor="black", alpha=0.85)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.001,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(list(scenarios.keys()), rotation=25, ha="right")
    ax.set_ylabel("Latency (seconds)")
    ax.set_title("Tail Latency Percentiles by Scenario")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "percentile_bars.png"), dpi=150)
    plt.close(fig)
    print("  -> percentile_bars.png")


def plot_comparison_summary_table(scenarios, output_dir):
    """Table image showing P50/P90/P95/P99 for every scenario side by side."""
    if not scenarios:
        print("  (skipped comparison_summary – no scenario CSVs found)")
        return

    col_labels = ["Scenario", "Count", "Mean", "P50", "P90", "P95", "P99"]
    rows = []
    for name, df in scenarios.items():
        lat = df["latency_seconds"]
        rows.append([
            name, str(len(df)), f"{lat.mean():.4f}",
            f"{np.percentile(lat, 50):.4f}",
            f"{np.percentile(lat, 90):.4f}",
            f"{np.percentile(lat, 95):.4f}",
            f"{np.percentile(lat, 99):.4f}",
        ])

    fig, ax = plt.subplots(figsize=(11, 1 + 0.5 * len(rows)))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=col_labels, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)
    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#4472C4")
        table[0, j].set_text_props(color="white", fontweight="bold")

    ax.set_title("Scenario Comparison – Tail Latencies", fontsize=13,
                 fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "comparison_summary.png"), dpi=150)
    plt.close(fig)
    print("  -> comparison_summary.png")


# ── Locust CSV support ───────────────────────────────────────────────────────

def plot_locust_stats(output_dir):
    """If Locust CSV exports exist in the project root, generate CDF from them."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stats_file = None
    for candidate in ["results_stats_history.csv", "locust_stats_history.csv"]:
        p = os.path.join(root, candidate)
        if os.path.exists(p):
            stats_file = p
            break

    if stats_file is None:
        print("  (skipped locust_stats – no Locust CSV history found)")
        return

    df = pd.read_csv(stats_file)
    if "Total Average Response Time" not in df.columns:
        print("  (skipped locust_stats – unexpected CSV columns)")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ts = pd.to_datetime(df["Timestamp"], unit="s")
    axes[0].plot(ts, df["Total Average Response Time"], label="Avg", color="steelblue")
    if "Total Max Response Time" in df.columns:
        axes[0].plot(ts, df["Total Max Response Time"], label="Max",
                     color="coral", alpha=0.7)
    axes[0].set_xlabel("Time")
    axes[0].set_ylabel("Response Time (ms)")
    axes[0].set_title("Locust Response Time Over Time")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    if "Total Requests/s" in df.columns:
        axes[1].plot(ts, df["Total Requests/s"], color="green")
        axes[1].set_xlabel("Time")
        axes[1].set_ylabel("Requests/s")
        axes[1].set_title("Locust Throughput Over Time")
        axes[1].grid(True, alpha=0.3)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "locust_stats.png"), dpi=150)
    plt.close(fig)
    print("  -> locust_stats.png")


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    print(f"Loading data from: {CSV_PATH}")
    df = load_data(CSV_PATH)
    print(f"Loaded {len(df)} records.\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Saving plots to: {OUTPUT_DIR}\n")

    print("=== Basic Plots ===")
    plot_latency_histogram(df, OUTPUT_DIR)
    plot_latency_over_time(df, OUTPUT_DIR)
    plot_latency_by_type(df, OUTPUT_DIR)
    plot_outcome_breakdown(df, OUTPUT_DIR)
    plot_summary_table(df, OUTPUT_DIR)

    print("\n=== Tail Latency / CDF Plots ===")
    plot_cdf(df, OUTPUT_DIR)
    plot_cdf_by_type(df, OUTPUT_DIR)
    plot_throughput_over_time(df, OUTPUT_DIR)

    print("\n=== Locust Stats ===")
    plot_locust_stats(OUTPUT_DIR)

    print("\n=== Scenario Comparison (ContainerLab with vs without) ===")
    scenario_dir = os.environ.get(
        "SCENARIO_CSV_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios"),
    )
    if os.path.isdir(scenario_dir):
        scenarios = _load_scenario_csvs(scenario_dir)
        if scenarios:
            print(f"Found {len(scenarios)} scenario(s) in {scenario_dir}")
            plot_cdf_comparison(scenarios, OUTPUT_DIR)
            plot_percentile_bars(scenarios, OUTPUT_DIR)
            plot_comparison_summary_table(scenarios, OUTPUT_DIR)
        else:
            print(f"  No valid CSV files found in {scenario_dir}")
    else:
        print(f"  Scenario directory not found: {scenario_dir}")
        print("  To generate comparison plots, create scenario CSVs in that directory.")
        print("  e.g.: no_containerlab.csv, wan_10ms.csv, wan_50ms.csv, wan_100ms.csv")

    print(f"\nAll plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

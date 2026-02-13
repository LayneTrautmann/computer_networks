"""
Analytics Plotting Script
Reads the CSV data collected by the Analytics Service and generates graphs:
  1. Latency distribution (histogram)
  2. Latency over time (line chart)
  3. Latency by order type (box plot)
  4. Request outcome breakdown (bar chart)
"""

import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = os.environ.get(
    "ANALYTICS_CSV_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics_data.csv"),
)

OUTPUT_DIR = os.environ.get(
    "ANALYTICS_PLOT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots"),
)


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


def plot_latency_histogram(df, output_dir):
    """Plot 1: Distribution of end-to-end latencies."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df["latency_seconds"], bins=20, edgecolor="black", alpha=0.7, color="steelblue")
    ax.set_xlabel("Latency (seconds)")
    ax.set_ylabel("Number of Requests")
    ax.set_title("End-to-End Latency Distribution")
    ax.axvline(df["latency_seconds"].mean(), color="red", linestyle="--", label=f'Mean: {df["latency_seconds"].mean():.4f}s')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "latency_histogram.png"), dpi=150)
    plt.close(fig)
    print("  -> latency_histogram.png")


def plot_latency_over_time(df, output_dir):
    """Plot 2: Latency over time for each request."""
    fig, ax = plt.subplots(figsize=(10, 5))

    grocery = df[df["order_type"] == "GROCERY_ORDER"]
    restock = df[df["order_type"] == "RESTOCK_ORDER"]

    if not grocery.empty:
        ax.plot(grocery["timestamp"], grocery["latency_seconds"], "o-", label="Grocery Order", markersize=4, alpha=0.8)
    if not restock.empty:
        ax.plot(restock["timestamp"], restock["latency_seconds"], "s-", label="Restock Order", markersize=4, alpha=0.8)

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
    """Plot 3: Box plot comparing latency by order type."""
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
    """Plot 4: Bar chart of request outcomes (OK vs BAD_REQUEST) by order type."""
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
    """Plot 5: Summary statistics table as an image."""
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")

    summary = {
        "Metric": [
            "Total Requests",
            "Grocery Orders",
            "Restock Orders",
            "OK Responses",
            "BAD_REQUEST Responses",
            "Mean Latency (s)",
            "Median Latency (s)",
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
            f'{df["latency_seconds"].mean():.4f}',
            f'{df["latency_seconds"].median():.4f}',
            f'{df["latency_seconds"].min():.4f}',
            f'{df["latency_seconds"].max():.4f}',
            f'{df["latency_seconds"].std():.4f}',
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


def main():
    print(f"Loading data from: {CSV_PATH}")
    df = load_data(CSV_PATH)
    print(f"Loaded {len(df)} records.\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Saving plots to: {OUTPUT_DIR}\n")

    plot_latency_histogram(df, OUTPUT_DIR)
    plot_latency_over_time(df, OUTPUT_DIR)
    plot_latency_by_type(df, OUTPUT_DIR)
    plot_outcome_breakdown(df, OUTPUT_DIR)
    plot_summary_table(df, OUTPUT_DIR)

    print(f"\nAll plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

"""
Exploratory Data Analysis for MORROW.

Generates charts and summary statistics from the cleaned dataset.

Usage:
    python -m ml.eda.analyze_dataset
"""
import matplotlib
matplotlib.use("Agg")

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from ml.config import (
    CLEANED_DATA_PATH,
    FIGURES_DIR,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
    MODEL_FEATURES,
)


def load_data(path: str = CLEANED_DATA_PATH) -> pd.DataFrame:
    """Load cleaned dataset."""
    df = pd.read_csv(path, parse_dates=["booking_created_at", "appointment_datetime"])
    print(f"Loaded {len(df)} records for EDA")
    return df


def plot_target_distribution(df: pd.DataFrame, save_dir: str) -> None:
    """Bar chart of target variable distribution."""
    fig, ax = plt.subplots(figsize=(8, 5))
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    labels = ["Attended (0)", "No-Show (1)"]
    colors = ["#2ecc71", "#e74c3c"]
    bars = ax.bar(labels, counts.values, color=colors, edgecolor="black", alpha=0.85)
    for bar, count in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
                f"{count}\n({count / len(df):.1%})", ha="center", fontsize=11)
    ax.set_title("Target Distribution: No-Show vs Attended", fontsize=14)
    ax.set_ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "target_distribution.png"), dpi=150)
    plt.close()
    print("  ✓ target_distribution.png")


def plot_noshow_by_weekday(df: pd.DataFrame, save_dir: str) -> None:
    """No-show rate by appointment weekday."""
    fig, ax = plt.subplots(figsize=(10, 5))
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    rates = df.groupby("appointment_weekday")[TARGET_COLUMN].mean()
    counts = df.groupby("appointment_weekday")[TARGET_COLUMN].count()
    ax.bar(rates.index, rates.values, color="#3498db", edgecolor="black", alpha=0.85)
    for i, (rate, count) in enumerate(zip(rates.values, counts.values)):
        ax.text(rates.index[i], rate + 0.005, f"{rate:.1%}\n(n={count})",
                ha="center", fontsize=9)
    ax.set_xticks(range(7))
    ax.set_xticklabels(day_names)
    ax.set_title("No-Show Rate by Appointment Weekday", fontsize=14)
    ax.set_ylabel("No-Show Rate")
    ax.set_ylim(0, max(rates.values) * 1.25)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "noshow_by_weekday.png"), dpi=150)
    plt.close()
    print("  ✓ noshow_by_weekday.png")


def plot_noshow_by_channel(df: pd.DataFrame, save_dir: str) -> None:
    """No-show rate by booking channel."""
    fig, ax = plt.subplots(figsize=(8, 5))
    rates = df.groupby("booking_channel")[TARGET_COLUMN].mean().sort_values(ascending=False)
    counts = df.groupby("booking_channel")[TARGET_COLUMN].count()
    colors = ["#e74c3c", "#f39c12", "#2ecc71"]
    ax.bar(rates.index, rates.values, color=colors[:len(rates)], edgecolor="black", alpha=0.85)
    for i, (channel, rate) in enumerate(rates.items()):
        ax.text(i, rate + 0.005, f"{rate:.1%}\n(n={counts[channel]})",
                ha="center", fontsize=10)
    ax.set_title("No-Show Rate by Booking Channel", fontsize=14)
    ax.set_ylabel("No-Show Rate")
    ax.set_ylim(0, max(rates.values) * 1.3)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "noshow_by_channel.png"), dpi=150)
    plt.close()
    print("  ✓ noshow_by_channel.png")


def plot_lead_time_histogram(df: pd.DataFrame, save_dir: str) -> None:
    """Booking lead-time histogram split by outcome."""
    fig, ax = plt.subplots(figsize=(10, 5))
    attended = df[df[TARGET_COLUMN] == 0]["booking_lead_days"].dropna()
    no_show = df[df[TARGET_COLUMN] == 1]["booking_lead_days"].dropna()
    bins = np.arange(0, min(df["booking_lead_days"].dropna().max() + 5, 120), 5)
    ax.hist(attended, bins=bins, alpha=0.6, label="Attended", color="#2ecc71", edgecolor="black")
    ax.hist(no_show, bins=bins, alpha=0.6, label="No-Show", color="#e74c3c", edgecolor="black")
    ax.set_title("Booking Lead Time Distribution", fontsize=14)
    ax.set_xlabel("Lead Days")
    ax.set_ylabel("Count")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "lead_time_histogram.png"), dpi=150)
    plt.close()
    print("  ✓ lead_time_histogram.png")


def plot_appointment_hour(df: pd.DataFrame, save_dir: str) -> None:
    """Appointment hour distribution."""
    fig, ax = plt.subplots(figsize=(10, 5))
    hour_counts = df.groupby("appointment_hour")[TARGET_COLUMN].agg(["count", "mean"])
    ax2 = ax.twinx()
    ax.bar(hour_counts.index, hour_counts["count"], color="#3498db", alpha=0.6,
           edgecolor="black", label="Total Appointments")
    ax2.plot(hour_counts.index, hour_counts["mean"], color="#e74c3c",
             marker="o", linewidth=2, label="No-Show Rate")
    ax.set_title("Appointment Hour Distribution & No-Show Rate", fontsize=14)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Appointment Count")
    ax2.set_ylabel("No-Show Rate")
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "appointment_hour_distribution.png"), dpi=150)
    plt.close()
    print("  ✓ appointment_hour_distribution.png")


def plot_correlation_heatmap(df: pd.DataFrame, save_dir: str) -> None:
    """Correlation heatmap of numerical features + target."""
    cols = NUMERICAL_FEATURES + [TARGET_COLUMN]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                square=True, ax=ax, linewidths=0.5)
    ax.set_title("Feature Correlation Heatmap", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "correlation_heatmap.png"), dpi=150)
    plt.close()
    print("  ✓ correlation_heatmap.png")


def plot_missing_values(df: pd.DataFrame, save_dir: str) -> None:
    """Missing values chart."""
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    if len(missing) == 0:
        print("  ✓ missing_values.png (no missing values — chart shows all complete)")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No Missing Values", ha="center", va="center",
                fontsize=16, transform=ax.transAxes)
        ax.set_title("Missing Values Summary", fontsize=14)
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, "missing_values.png"), dpi=150)
        plt.close()
        return

    fig, ax = plt.subplots(figsize=(10, max(4, len(missing) * 0.5)))
    bars = ax.barh(missing.index, missing.values, color="#e67e22", edgecolor="black", alpha=0.85)
    for bar, val in zip(bars, missing.values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val} ({val / len(df):.1%})", va="center", fontsize=10)
    ax.set_title("Missing Values by Column", fontsize=14)
    ax.set_xlabel("Missing Count")
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, "missing_values.png"), dpi=150)
    plt.close()
    print("  ✓ missing_values.png")


def print_summary_statistics(df: pd.DataFrame) -> None:
    """Print summary statistics."""
    print("\n" + "─" * 50)
    print("Summary Statistics")
    print("─" * 50)

    print(f"\n  Total records: {len(df)}")
    print(f"  No-show rate:  {df[TARGET_COLUMN].mean():.2%}")
    print(f"  Date range:    {df['booking_created_at'].min()} → {df['booking_created_at'].max()}")

    print(f"\n  Numerical Feature Statistics:")
    desc = df[NUMERICAL_FEATURES].describe().T
    print(desc[["mean", "std", "min", "50%", "max"]].to_string())

    print(f"\n  Booking Channel Distribution:")
    channel_dist = df["booking_channel"].value_counts()
    for ch, cnt in channel_dist.items():
        print(f"    {ch}: {cnt} ({cnt / len(df):.1%})")

    print("─" * 50)


def main():
    """Run EDA and generate all charts."""
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("=" * 60)
    print("MORROW — Exploratory Data Analysis")
    print("=" * 60)

    df = load_data()

    print("\nGenerating charts:")
    plot_target_distribution(df, FIGURES_DIR)
    plot_noshow_by_weekday(df, FIGURES_DIR)
    plot_noshow_by_channel(df, FIGURES_DIR)
    plot_lead_time_histogram(df, FIGURES_DIR)
    plot_appointment_hour(df, FIGURES_DIR)
    plot_correlation_heatmap(df, FIGURES_DIR)
    plot_missing_values(df, FIGURES_DIR)

    print_summary_statistics(df)

    print(f"\nAll figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()

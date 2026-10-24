"""
Exploratory Data Analysis (EDA) and chart generation module for BazaarLens-IR.
Generates publication-grade visual charts in `reports/figures/`.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


def generate_all_charts(df_kpi: pd.DataFrame, cat_summary: pd.DataFrame, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    saved_files = []

    # Chart 1: Category Weekly GMV Proxy & Units Sold
    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=180)
    short_labels = [c.split("(")[0].strip() for c in cat_summary["categoryTitle"]]
    gmv_millions = cat_summary["total_weekly_gmv_proxy_toman"] / 1e6
    bars = ax1.barh(short_labels[::-1], gmv_millions[::-1], color="#1B4F72", alpha=0.9)
    ax1.set_xlabel("Estimated Weekly GMV Proxy (Million Tomans)", fontsize=11, fontweight="bold")
    ax1.set_title("BazaarLens-IR: Weekly GMV Proxy by Product Category (Synthetic Validation Data)", fontsize=12, fontweight="bold", pad=12)
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + max(gmv_millions)*0.015, bar.get_y() + bar.get_height()/2, f"{w:,.1f}M", va="center", fontsize=9.5, fontweight="bold")
    ax1.set_xlim(0, max(gmv_millions) * 1.18)
    plt.tight_layout()
    p1 = figures_dir / "fig1_category_gmv_proxy.png"
    fig.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(p1)

    # Chart 2: Impact of Free Shipping & Preparation Days on Weekly Sales Velocity
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    prep_grouped = (
        df_kpi.groupby(["preparationDays", "isFreeShipping"], as_index=False)["sales_count_week"]
        .mean()
    )
    for is_free, label, color, marker in [
        (True, "Free Shipping (Ersal-e Raygan)", "#117A65", "o"),
        (False, "Paid Shipping (Ba Hazineh)", "#B03A2E", "s"),
    ]:
        sub = prep_grouped[prep_grouped["isFreeShipping"] == is_free]
        ax.plot(sub["preparationDays"], sub["sales_count_week"], marker=marker, linewidth=2.4, markersize=7, label=label, color=color)
    ax.set_xlabel("Vendor Preparation Time (Days)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Mean Weekly Units Sold per SKU", fontsize=11, fontweight="bold")
    ax.set_title("Impact of Shipping Policy & Preparation Delay on Weekly Sales Velocity", fontsize=12, fontweight="bold", pad=12)
    ax.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    p2 = figures_dir / "fig2_shipping_prep_velocity.png"
    fig.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(p2)

    # Chart 3: Raw Rating vs. Bayesian Weighted Rating Shrinkage
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
    rated_df = df_kpi[df_kpi["rating_count"] > 0].copy()
    sc = ax.scatter(
        rated_df["rating_count"],
        rated_df["rating_average"],
        alpha=0.45,
        c="#7F8C8D",
        s=28,
        label="Raw Average Rating (Arithmetic Mean)",
    )
    ax.scatter(
        rated_df["rating_count"],
        rated_df["bayesian_rating"],
        alpha=0.75,
        c="#1F618D",
        s=30,
        label="Bayesian Weighted Rating (Shrinkage Adjusted)",
    )
    ax.set_xscale("log")
    ax.set_xlabel("Number of Customer Ratings (Log Scale)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Product Score (1.0 to 5.0)", fontsize=11, fontweight="bold")
    ax.set_title("Bayesian Rating Shrinkage: Filtering Low-Sample Noise in Product Ranking", fontsize=12, fontweight="bold", pad=12)
    ax.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    p3 = figures_dir / "fig3_bayesian_rating_shrinkage.png"
    fig.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    saved_files.append(p3)

    return saved_files

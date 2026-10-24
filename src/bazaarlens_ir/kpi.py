"""
Business KPI calculation module for BazaarLens-IR.
Includes Bayesian Weighted Rating, Weekly GMV Proxy (in Tomans), Discount Depth,
Category Concentration, and Vendor Performance Tiers.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


def compute_bayesian_rating(df: pd.DataFrame, min_votes_quantile: float = 0.60) -> pd.Series:
    """
    Computes Bayesian weighted rating:
    WR = (v / (v + m)) * R + (m / (v + m)) * C
    where:
      R = product rating_average
      v = product rating_count
      m = minimum votes threshold (quantile of positive rating_count)
      C = mean rating across all rated products
    """
    rated = df[df["rating_count"] > 0]
    if rated.empty:
        return pd.Series(np.nan, index=df.index)
    C = float(rated["rating_average"].mean())
    m = float(rated["rating_count"].quantile(min_votes_quantile))
    v = df["rating_count"].astype(float)
    R = df["rating_average"].fillna(C).astype(float)
    wr = (v / (v + m)) * R + (m / (v + m)) * C
    return wr.round(3)


def enrich_with_kpis(df_clean: pd.DataFrame) -> pd.DataFrame:
    """Adds product-level KPI columns to the cleaned DataFrame."""
    df = df_clean.copy()
    # Weekly Gross Merchandise Value (GMV) Proxy in Tomans
    # Caveat: Estimated from current price_toman * sales_count_week (not accounting for intra-week price changes or returns)
    df["weekly_gmv_proxy_toman"] = (df["price_toman"] * df["sales_count_week"]).round(0)
    df["bayesian_rating"] = compute_bayesian_rating(df)
    df["review_to_weekly_sales_ratio"] = np.where(
        df["sales_count_week"] > 0,
        (df["rating_count"] / df["sales_count_week"]).round(2),
        np.nan,
    )
    return df


def summarize_category_kpis(df_kpi: pd.DataFrame) -> pd.DataFrame:
    """Aggregates key marketplace KPIs by categoryTitle."""
    grouped = (
        df_kpi.groupby(["categoryId", "categoryTitle"], as_index=False)
        .agg(
            active_sku_count=("_id", "count"),
            available_sku_ratio=("IsAvailable", "mean"),
            free_shipping_share=("isFreeShipping", "mean"),
            median_price_toman=("price_toman", "median"),
            mean_discount_pct=("discount_pct", "mean"),
            total_weekly_units=("sales_count_week", "sum"),
            total_weekly_gmv_proxy_toman=("weekly_gmv_proxy_toman", "sum"),
            mean_bayesian_rating=("bayesian_rating", "mean"),
            median_prep_days=("preparationDays", "median"),
        )
    )
    grouped["available_sku_ratio"] = (grouped["available_sku_ratio"] * 100.0).round(1)
    grouped["free_shipping_share"] = (grouped["free_shipping_share"] * 100.0).round(1)
    grouped["mean_discount_pct"] = grouped["mean_discount_pct"].round(2)
    grouped["mean_bayesian_rating"] = grouped["mean_bayesian_rating"].round(2)
    total_market_gmv = grouped["total_weekly_gmv_proxy_toman"].sum()
    grouped["gmv_share_pct"] = np.where(
        total_market_gmv > 0,
        (grouped["total_weekly_gmv_proxy_toman"] / total_market_gmv * 100.0).round(2),
        0.0,
    )
    return grouped.sort_values("total_weekly_gmv_proxy_toman", ascending=False).reset_index(drop=True)


def summarize_marketplace_overview(df_kpi: pd.DataFrame) -> Dict[str, Any]:
    """Returns top-level executive summary metrics."""
    free_ship = df_kpi[df_kpi["isFreeShipping"]]["sales_count_week"]
    paid_ship = df_kpi[~df_kpi["isFreeShipping"]]["sales_count_week"]
    return {
        "total_clean_skus": int(len(df_kpi)),
        "total_vendors": int(df_kpi["vendor_name"].nunique()),
        "total_categories": int(df_kpi["categoryId"].nunique()),
        "overall_median_price_toman": float(df_kpi["price_toman"].median()),
        "overall_iqr_price_toman": float(df_kpi["price_toman"].quantile(0.75) - df_kpi["price_toman"].quantile(0.25)),
        "total_weekly_units_sold": int(df_kpi["sales_count_week"].sum()),
        "total_weekly_gmv_proxy_toman": float(df_kpi["weekly_gmv_proxy_toman"].sum()),
        "free_shipping_sku_share_pct": round(float(df_kpi["isFreeShipping"].mean() * 100.0), 2),
        "avg_weekly_sales_free_shipping": round(float(free_ship.mean()), 2),
        "avg_weekly_sales_paid_shipping": round(float(paid_ship.mean()), 2),
        "mean_discount_pct": round(float(df_kpi["discount_pct"].mean()), 2),
    }

"""
Data cleaning and standardization pipeline for BazaarLens-IR.
Converts prices from Rials to Tomans (1 Toman = 10 Rials), removes duplicate _id records,
fixes logical price anomalies, normalizes Persian strings, and imputes missing ratings safely.
"""
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


def normalize_persian_text(series: pd.Series) -> pd.Series:
    """Standardizes Arabic Yeh/Kaf characters to Persian and strips extra whitespace."""
    return (
        series.astype(str)
        .str.replace("ي", "ی", regex=False)
        .str.replace("ك", "ک", regex=False)
        .str.strip()
    )


def clean_products_dataframe(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes reproducible data cleaning rules without mutating the input DataFrame.
    Returns (cleaned_df, cleaning_audit_log).
    """
    df = df_raw.copy()
    initial_rows = len(df)

    # 1. Deduplicate by primary key `_id`
    df = df.drop_duplicates(subset=["_id"], keep="first").copy()
    after_dedup_rows = len(df)

    # 2. Filter out non-positive prices or negative stock
    valid_mask = (df["price"] > 0) & (df["primaryPrice"] > 0) & (df["stock"] >= 0)
    df = df.loc[valid_mask].copy()
    after_valid_filter_rows = len(df)

    # 3. Fix records where price > primaryPrice by aligning primaryPrice = max(price, primaryPrice)
    inverted_price_count = int((df["price"] > df["primaryPrice"]).sum())
    df["primaryPrice"] = np.maximum(df["price"], df["primaryPrice"])

    # 4. Convert Rials to Tomans explicitly
    df["price_toman"] = (df["price"] / 10.0).round(0)
    df["primary_price_toman"] = (df["primaryPrice"] / 10.0).round(0)

    # 5. Compute discount percentage
    df["discount_pct"] = np.where(
        df["primary_price_toman"] > 0,
        ((df["primary_price_toman"] - df["price_toman"]) / df["primary_price_toman"]) * 100.0,
        0.0,
    ).round(2)

    # 6. Normalize text columns
    df["categoryTitle"] = normalize_persian_text(df["categoryTitle"])
    df["vendor_status_title"] = normalize_persian_text(df["vendor_status_title"])

    # 7. Handle missing rating_average: keep NaN for unweighted mean, add `has_rating` flag
    df["has_rating"] = df["rating_count"] > 0
    df.loc[~df["has_rating"], "rating_average"] = np.nan

    audit = {
        "initial_rows": int(initial_rows),
        "duplicates_removed": int(initial_rows - after_dedup_rows),
        "invalid_rows_removed": int(after_dedup_rows - after_valid_filter_rows),
        "inverted_prices_corrected": inverted_price_count,
        "final_clean_rows": int(len(df)),
    }
    return df.reset_index(drop=True), audit

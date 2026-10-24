"""
Data profiling and quality assessment module for BazaarLens-IR.
"""
from typing import Dict, Any
import pandas as pd


def generate_quality_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes comprehensive data quality metrics prior to cleaning."""
    total_rows = len(df)
    duplicate_ids = int(df.duplicated(subset=["_id"]).sum())
    missing_by_col = {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().sum() > 0}
    invalid_price_rows = int((df["price"] <= 0).sum())
    price_exceeds_primary = int((df["price"] > df["primaryPrice"]).sum())
    negative_stock_rows = int((df["stock"] < 0).sum())

    return {
        "total_rows": int(total_rows),
        "unique_product_ids": int(df["_id"].nunique()),
        "duplicate_product_ids": duplicate_ids,
        "missing_values_by_column": missing_by_col,
        "invalid_non_positive_price_rows": invalid_price_rows,
        "price_exceeds_primary_rows": price_exceeds_primary,
        "negative_stock_rows": negative_stock_rows,
    }

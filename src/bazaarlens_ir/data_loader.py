"""
Data loading and schema validation module for BazaarLens-IR.
"""
from pathlib import Path
from typing import Dict, Any
import pandas as pd

REQUIRED_PRODUCT_COLUMNS = {
    "_id",
    "name",
    "price",
    "primaryPrice",
    "stock",
    "isFreeShipping",
    "IsAvailable",
    "rating_average",
    "rating_count",
    "sales_count_week",
    "vendor_name",
    "vendor_score",
    "vendor_status_title",
    "categoryId",
    "categoryTitle",
    "preparationDays",
    "weight",
}


def validate_product_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates that required columns exist in the products DataFrame."""
    missing_cols = REQUIRED_PRODUCT_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required product columns: {sorted(missing_cols)}")
    return {
        "is_valid": True,
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "missing_columns": [],
    }


def load_products_dataset(csv_path: Path) -> pd.DataFrame:
    """Loads products CSV file and performs initial schema check."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Products dataset file not found: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    validate_product_schema(df)
    return df

"""
Automated test suite for BazaarLens-IR.
Compatible with both `pytest` and standard library `python -m unittest`.
"""
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from bazaarlens_ir.data_loader import validate_product_schema, load_products_dataset
from bazaarlens_ir.profiling import generate_quality_profile
from bazaarlens_ir.cleaning import clean_products_dataframe, normalize_persian_text
from bazaarlens_ir.kpi import compute_bayesian_rating, enrich_with_kpis, summarize_category_kpis


class TestBazaarLensPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample_path = Path(__file__).resolve().parents[1] / "data" / "sample" / "synthetic_basalam_products.csv"
        cls.df_raw = load_products_dataset(cls.sample_path)
        cls.df_clean, cls.audit = clean_products_dataframe(cls.df_raw)
        cls.df_kpi = enrich_with_kpis(cls.df_clean)

    def test_schema_validation_passes_on_valid_data(self):
        res = validate_product_schema(self.df_raw)
        self.assertTrue(res["is_valid"])
        self.assertGreater(res["row_count"], 500)

    def test_schema_validation_raises_on_missing_columns(self):
        bad_df = pd.DataFrame({"_id": ["1"], "price": [1000]})
        with self.assertRaises(ValueError):
            validate_product_schema(bad_df)

    def test_profiling_detects_injected_anomalies(self):
        profile = generate_quality_profile(self.df_raw)
        self.assertGreaterEqual(profile["duplicate_product_ids"], 1)
        self.assertGreaterEqual(profile["invalid_non_positive_price_rows"], 1)
        self.assertGreaterEqual(profile["negative_stock_rows"], 1)

    def test_cleaning_removes_duplicates_and_invalid_rows(self):
        self.assertEqual(self.df_clean["_id"].duplicated().sum(), 0)
        self.assertTrue((self.df_clean["price_toman"] > 0).all())
        self.assertTrue((self.df_clean["stock"] >= 0).all())
        self.assertTrue((self.df_clean["primary_price_toman"] >= self.df_clean["price_toman"]).all())

    def test_rial_to_toman_conversion_accuracy(self):
        # 1 Toman = 10 Rials
        ratios = (self.df_clean["price"] / self.df_clean["price_toman"]).round(1)
        self.assertTrue((ratios == 10.0).all())

    def test_persian_text_normalization(self):
        s = pd.Series(["  صنايع دستي و كاشي  "])
        norm = normalize_persian_text(s)
        self.assertEqual(norm.iloc[0], "صنایع دستی و کاشی")

    def test_bayesian_rating_shrinks_single_vote_extremes(self):
        # A product with 1 vote of 5.0 should rank lower than a product with 200 votes of 4.8
        test_df = pd.DataFrame({
            "rating_count": [1, 200, 50, 80, 120],
            "rating_average": [5.0, 4.8, 4.2, 4.3, 4.4],
        })
        wr = compute_bayesian_rating(test_df, min_votes_quantile=0.5)
        self.assertLess(wr.iloc[0], wr.iloc[1])

    def test_category_gmv_share_sums_to_100(self):
        cat_df = summarize_category_kpis(self.df_kpi)
        self.assertAlmostEqual(cat_df["gmv_share_pct"].sum(), 100.0, places=1)


if __name__ == "__main__":
    unittest.main()

"""
Generates a deterministic, schema-faithful synthetic sample (`synthetic_basalam_products.csv`
and `synthetic_basalam_reviews.csv`) for testing, CI/CD, and offline execution.
IMPORTANT: This dataset is explicitly labeled `synthetic` and mirrors the exact column names
and data types of `RadeAI/BaSalam_comments_products` (where prices are stored in Rials).
"""
from pathlib import Path
import numpy as np
import pandas as pd


def generate_synthetic_basalam_data(output_dir: Path, seed: int = 42, n_products: int = 600) -> tuple[Path, Path]:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    categories = [
        (101, "Food & Organic Honey (مواد غذایی و عسل طبیعی)"),
        (102, "Handicrafts & Pottery (صنایع دستی و سفال)"),
        (103, "Nuts & Dried Fruits (خشکبار و آجیل)"),
        (104, "Apparel & Traditional Textiles (پوشاک و منسوجات سنتی)"),
        (105, "Herbal & Natural Cosmetics (عطاری و آرایشی گیاهی)"),
        (106, "Home & Kitchen Decor (خانه و آشپزخانه)"),
    ]

    vendor_ids = [f"VND_{i:03d}" for i in range(1, 81)]
    vendor_scores = {v: round(float(rng.uniform(3.2, 5.0)), 2) for v in vendor_ids}
    vendor_statuses = {v: rng.choice(["غرفه برتر", "غرفه فعال", "غرفه تازهکار"], p=[0.25, 0.60, 0.15]) for v in vendor_ids}

    rows = []
    for idx in range(1, n_products + 1):
        cat_id, cat_title = categories[rng.integers(0, len(categories))]
        v_id = rng.choice(vendor_ids)
        # Base price in Rials (10 Rials = 1 Toman). Typical range: 500,000 to 25,000,000 Rials (50k to 2.5M Tomans)
        base_toman = float(np.round(rng.lognormal(mean=12.4, sigma=0.75), -3))
        base_toman = max(40_000.0, min(base_toman, 8_500_000.0))
        primary_price_rial = int(base_toman * 10)

        has_discount = rng.random() < 0.38
        discount_pct = float(rng.choice([0.05, 0.10, 0.15, 0.20, 0.25, 0.30])) if has_discount else 0.0
        price_rial = int(round(primary_price_rial * (1.0 - discount_pct), -2))

        is_free_shipping = bool(rng.random() < 0.32)
        prep_days = int(rng.choice([1, 2, 3, 5, 7, 10], p=[0.30, 0.30, 0.20, 0.10, 0.06, 0.04]))
        stock = int(rng.integers(0, 120))
        is_available = stock > 0

        # Rating count and rating average correlated with vendor score, free shipping, and reasonable prep days
        lambda_sales = (
            2.5
            + (2.2 if is_free_shipping else 0.0)
            + (3.5 * discount_pct * 4)
            + max(0.0, (5 - prep_days) * 0.5)
            + (vendor_scores[v_id] - 3.0) * 1.8
        )
        sales_count_week = int(rng.poisson(max(0.5, lambda_sales))) if is_available else 0
        rating_count = int(sales_count_week * rng.integers(1, 14) + rng.integers(0, 25))
        if rating_count > 0:
            rating_avg = round(float(np.clip(rng.normal(loc=vendor_scores[v_id] * 0.96, scale=0.35), 1.0, 5.0)), 2)
        else:
            rating_avg = np.nan

        rows.append({
            "_id": f"PRD_{10000 + idx}",
            "_score": round(float(rng.uniform(0.5, 10.0)), 3),
            "name": f"Product_{idx}_{cat_id}",
            "price": price_rial,
            "primaryPrice": primary_price_rial,
            "status_title": "در دسترس" if is_available else "ناموجود",
            "stock": stock,
            "has_delivery": True,
            "isFreeShipping": is_free_shipping,
            "IsAvailable": is_available,
            "IsSaleable": is_available,
            "rating_average": rating_avg,
            "rating_count": rating_count,
            "sales_count_week": sales_count_week,
            "vendor_name": v_id,
            "vendor_score": vendor_scores[v_id],
            "vendor_status_title": vendor_statuses[v_id],
            "categoryId": cat_id,
            "categoryTitle": cat_title,
            "preparationDays": prep_days,
            "weight": int(rng.integers(100, 5000)),
            "data_origin": "synthetic",
        })

    df_prod = pd.DataFrame(rows)

    # Inject controlled data quality anomalies to test cleaning & profiling pipelines:
    # 1. Duplicate rows (8 duplicates)
    dups = df_prod.sample(8, random_state=seed)
    df_prod = pd.concat([df_prod, dups], ignore_index=True)

    # 2. Invalid records: price > primaryPrice (3 rows), negative stock (2 rows), zero price (2 rows)
    df_prod.loc[0, "price"] = df_prod.loc[0, "primaryPrice"] + 500_000
    df_prod.loc[1, "price"] = 0
    df_prod.loc[2, "stock"] = -5
    df_prod.loc[3, "categoryTitle"] = "  " + str(df_prod.loc[3, "categoryTitle"]) + "  "

    prod_path = output_dir / "synthetic_basalam_products.csv"
    df_prod.to_csv(prod_path, index=False, encoding="utf-8")

    # Generate synthetic reviews linked to products (anonymized user IDs)
    review_rows = []
    valid_prod_ids = df_prod["_id"].unique()[:250]
    for r_idx in range(1, 801):
        p_id = str(rng.choice(valid_prod_ids))
        review_rows.append({
            "_id": f"REV_{50000 + r_idx}",
            "productId": p_id,
            "createdAt": f"2024-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 28)):02d}",
            "user_id": f"USR_ANON_{int(rng.integers(1000, 9999))}",
            "likeCount": int(rng.poisson(1.2)),
            "dislikeCount": int(rng.poisson(0.2)),
            "rating": int(rng.choice([1, 2, 3, 4, 5], p=[0.04, 0.05, 0.11, 0.30, 0.50])),
            "description": rng.choice([
                "کیفیت عالی و ارسال سریع",
                "بسته بندی مناسب بود ولی ارسال کمی طول کشید",
                "نسبت به قیمت ارزش خرید بالایی دارد",
                "طعم و کیفیت کاملا طبیعی و خانگی",
                "متاسفانه با تاخیر به دستم رسید",
            ]),
            "data_origin": "synthetic",
        })
    df_rev = pd.DataFrame(review_rows)
    rev_path = output_dir / "synthetic_basalam_reviews.csv"
    df_rev.to_csv(rev_path, index=False, encoding="utf-8")
    return prod_path, rev_path


if __name__ == "__main__":
    sample_dir = Path(__file__).resolve().parents[2] / "data" / "sample"
    p_file, r_file = generate_synthetic_basalam_data(sample_dir)
    print(f"Generated synthetic sample files: {p_file} and {r_file}")

"""
End-to-end execution pipeline for BazaarLens-IR.
Runs synthetic sample generation (if needed), loading, profiling, cleaning, KPI calculation,
SQLite verification of analytical SQL queries, and figure generation.
"""
import json
import sqlite3
from pathlib import Path
from bazaarlens_ir.generate_synthetic_sample import generate_synthetic_basalam_data
from bazaarlens_ir.data_loader import load_products_dataset
from bazaarlens_ir.profiling import generate_quality_profile
from bazaarlens_ir.cleaning import clean_products_dataframe
from bazaarlens_ir.kpi import enrich_with_kpis, summarize_category_kpis, summarize_marketplace_overview
from bazaarlens_ir.eda import generate_all_charts


def run_pipeline(base_dir: Path | None = None) -> dict:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2]

    sample_dir = base_dir / "data" / "sample"
    processed_dir = base_dir / "data" / "processed"
    figures_dir = base_dir / "reports" / "figures"
    processed_dir.mkdir(parents=True, exist_ok=True)

    prod_csv = sample_dir / "synthetic_basalam_products.csv"
    if not prod_csv.exists():
        generate_synthetic_basalam_data(sample_dir)

    df_raw = load_products_dataset(prod_csv)
    profile = generate_quality_profile(df_raw)
    df_clean, audit = clean_products_dataframe(df_raw)
    df_kpi = enrich_with_kpis(df_clean)

    cat_summary = summarize_category_kpis(df_kpi)
    overview = summarize_marketplace_overview(df_kpi)

    # Save processed outputs
    df_kpi.to_csv(processed_dir / "cleaned_products_kpis.csv", index=False, encoding="utf-8")
    cat_summary.to_csv(processed_dir / "category_kpi_summary.csv", index=False, encoding="utf-8")

    # Execute SQL validation on in-memory SQLite database
    conn = sqlite3.connect(":memory:")
    df_kpi.to_sql("products", conn, index=False, if_exists="replace")
    top_vendors_sql = """
        SELECT
            vendor_name,
            vendor_status_title,
            COUNT(_id) AS sku_count,
            SUM(sales_count_week) AS weekly_units,
            ROUND(SUM(weekly_gmv_proxy_toman), 0) AS weekly_gmv_toman,
            ROUND(AVG(bayesian_rating), 2) AS avg_bayesian_rating
        FROM products
        WHERE IsAvailable = 1
        GROUP BY vendor_name, vendor_status_title
        HAVING COUNT(_id) >= 3
        ORDER BY weekly_gmv_toman DESC
        LIMIT 5;
    """
    top_vendors = conn.execute(top_vendors_sql).fetchall()
    conn.close()

    charts = generate_all_charts(df_kpi, cat_summary, figures_dir)

    summary_payload = {
        "data_origin": "synthetic (schema-faithful to RadeAI/BaSalam_comments_products)",
        "quality_profile": profile,
        "cleaning_audit": audit,
        "marketplace_overview": overview,
        "category_summary": cat_summary.to_dict(orient="records"),
        "top_5_vendors_sql": [
            {
                "vendor_name": r[0],
                "vendor_status_title": r[1],
                "sku_count": r[2],
                "weekly_units": r[3],
                "weekly_gmv_toman": r[4],
                "avg_bayesian_rating": r[5],
            }
            for r in top_vendors
        ],
        "generated_charts": [str(c.relative_to(base_dir)) for c in charts],
    }

    (base_dir / "reports" / "execution_metrics.json").write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary_payload


if __name__ == "__main__":
    metrics = run_pipeline()
    print(json.dumps(metrics["marketplace_overview"], indent=2, ensure_ascii=False))

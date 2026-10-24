# Data Directory Guide (`BazaarLens-IR`)

## Directory Layout
- `raw/`: Place downloaded raw files (`BaSalam.products.csv` and `BaSalam.reviews.csv`) here. Files in `raw/` are ignored by Git (`.gitignore`) to prevent committing 435+ MB datasets or violating redistribution norms.
- `processed/`: Contains cleaned and KPI-enriched CSV tables (`cleaned_products_kpis.csv`, `category_kpi_summary.csv`) generated automatically by `python -m bazaarlens_ir.pipeline`.
- `sample/`: Contains deterministic, schema-faithful synthetic files (`synthetic_basalam_products.csv` and `synthetic_basalam_reviews.csv`) with `data_origin = "synthetic"`. These files ARE tracked in Git so unit tests and CI pipelines run out of the box.

## How to Download the Real Dataset Legally
1. **Hugging Face Mirror (Recommended - MIT License):**
   Visit [https://huggingface.co/datasets/RadeAI/BaSalam_comments_products](https://huggingface.co/datasets/RadeAI/BaSalam_comments_products) and download `BaSalam.products.csv` into `data/raw/`.
2. **Kaggle Original Source:**
   Visit [https://www.kaggle.com/datasets/radeai/basalam-comments-and-products](https://www.kaggle.com/datasets/radeai/basalam-comments-and-products) and download via browser or Kaggle CLI:
   ```powershell
   kaggle datasets download -d radeai/basalam-comments-and-products -p data/raw --unzip
   ```

## Privacy & Ethics Rule
When working with `BaSalam.reviews.csv`, always drop or hash `name_of_user` and `photo_of_user` before publishing any sample tables or charts.

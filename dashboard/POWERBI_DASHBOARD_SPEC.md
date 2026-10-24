# راهنمای معماری و پیاده‌سازی داشبورد Power BI (BazaarLens-IR)

## ۱. مدل داده ستاره‌ای (Star Schema)
فایل‌های خروجی پوشه `data/processed/` یا جداول PostgreSQL (`sql/schema.sql`) را وارد Power BI Desktop کنید:
- **جدول حقیقت (Fact Table):** `fact_products` (شامل کلیدهای `product_id`, `category_id`, `vendor_name` و متریک‌های عددی).
- **جداول بُعد (Dimension Tables):**
  - `dim_categories` (رابطه ۱ به چند روی `category_id`)
  - `dim_vendors` (رابطه ۱ به چند روی `vendor_name`)

## ۲. فرمول‌های ضروری DAX
```dax
Total Weekly GMV (Toman) = SUM(fact_products[weekly_gmv_proxy_toman])

Total Weekly Units = SUM(fact_products[sales_count_week])

Median Product Price (Toman) = MEDIAN(fact_products[price_toman])

Active SKU Count = DISTINCTCOUNT(fact_products[product_id])

Free Shipping SKU Share % = 
DIVIDE(
    CALCULATE([Active SKU Count], fact_products[is_free_shipping] = TRUE()),
    [Active SKU Count],
    0
)

Weighted Marketplace Rating = 
DIVIDE(
    SUMX(fact_products, fact_products[bayesian_rating] * fact_products[rating_count]),
    SUM(fact_products[rating_count]),
    0
)
```

## ۳. چیدمان صفحات داشبورد (۳ صفحه استاندارد)
1. **صفحه اول — نمای کلی سلامت بازارگاه (Executive Marketplace Overview):**
   - ۴ کارت KPI در بالا: `Total Weekly GMV (Toman)`, `Total Weekly Units`, `Median Product Price`, `Free Shipping SKU Share %`.
   - نمودار میله‌ای افقی: سهم هر دسته‌بندی از GMV هفتگی و تعداد فروش.
   - نمودار خطی/ستونی ترکیبی: مقایسه سرعت فروش هفتگی بر حسب `preparation_days` و وضعیت `is_free_shipping`.
   - اسلایسرها (فیلترهای سمت راست): `category_title`, `vendor_status_title`, `is_free_shipping`.
2. **صفحه دوم — عملکرد غرفه‌داران و رتبه‌بندی بیزین (Vendor Leaderboard & Quality):**
   - نمودار پراکندگی (Scatter Plot): محور افقی `rating_count` (مقیاس لگاریتمی)، محور عمودی `bayesian_rating`، اندازه حباب `Total Weekly GMV`.
   - جدول ماتریسی (Matrix): فهرست غرفه‌های برتر به تفکیک دسته‌بندی همراه با قالب‌بندی شرطی (Conditional Formatting) روی زمان آماده‌سازی.
3. **صفحه سوم — پایش قیمت و اثربخشی تخفیف‌ها (Pricing & Discount Elasticity):**
   - نمودار جعبه‌ای (Box Plot) توزیع قیمت در هر دسته برای نمایش چولگی و داده‌های پرت.
   - نمودار ستونی میانگین فروش هفتگی در بازه‌های تخفیف (`بدون تخفیف`، `۱ تا ۱۰٪`، `۱۱ تا ۲۰٪`، `بیش از ۲۰٪`).

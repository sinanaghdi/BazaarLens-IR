# راهنمای جامع اجرای پروژه به زبان فارسی (BazaarLens-IR)

## گام ۱: آماده‌سازی محیط در Windows PowerShell
ابتدا PowerShell را باز کرده و دستورات زیر را اجرا کنید:
```powershell
conda create -n bazaarlens python=3.11 -y
conda activate bazaarlens
pip install -r requirements.txt
pip install -e .
```

## گام ۲: اجرای پایپلاین تحلیل و تولید نمودارها
```powershell
python -m bazaarlens_ir.pipeline
```
پس از اجرای این دستور:
- فایل‌های پاکسازی‌شده در `data/processed/` ذخیره می‌شوند.
- ۳ نمودار تحلیلی با کیفیت بالا در `reports/figures/` ساخته می‌شوند.
- فایل خلاصه متریک‌های واقعی اجرا در `reports/execution_metrics.json` ثبت می‌گردد.

## گام ۳: اجرای تست‌های خودکار
```powershell
pytest -v
# یا بدون نیاز به pytest:
python -m unittest discover -s tests -v
```
تمامی ۸ تست واحد باید با وضعیت `OK` پاس شوند.

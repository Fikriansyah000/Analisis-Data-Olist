"""
prepare_data.py
===============
Script untuk merge & clean raw CSV datasets menjadi satu file main_data.csv
yang siap dikonsumsi oleh Streamlit dashboard.

Cara pakai:
    python dashboard/prepare_data.py
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_PATH = os.path.join(BASE_DIR, "dashboard", "main_data.csv")

# ---------------------------------------------------------------------------
# 1. Load raw CSV files
# ---------------------------------------------------------------------------
print("[1/5] Memuat file CSV …")

orders_df = pd.read_csv(os.path.join(DATA_DIR, "orders_dataset.csv"))
order_items_df = pd.read_csv(os.path.join(DATA_DIR, "order_items_dataset.csv"))
order_payments_df = pd.read_csv(os.path.join(DATA_DIR, "order_payments_dataset.csv"))
order_reviews_df = pd.read_csv(os.path.join(DATA_DIR, "order_reviews_dataset.csv"))
customers_df = pd.read_csv(os.path.join(DATA_DIR, "customers_dataset.csv"))
products_df = pd.read_csv(os.path.join(DATA_DIR, "products_dataset.csv"))
category_translation_df = pd.read_csv(
    os.path.join(DATA_DIR, "product_category_name_translation.csv")
)

print(f"   orders          : {len(orders_df)} baris")
print(f"   order_items     : {len(order_items_df)} baris")
print(f"   order_payments  : {len(order_payments_df)} baris")
print(f"   order_reviews   : {len(order_reviews_df)} baris")
print(f"   customers       : {len(customers_df)} baris")
print(f"   products        : {len(products_df)} baris")
print(f"   category_trans  : {len(category_translation_df)} baris")

# ---------------------------------------------------------------------------
# 2. Cleaning – konversi datetime & buat year_month
# ---------------------------------------------------------------------------
print("[2/5] Cleaning datetime …")

datetime_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for col in datetime_cols:
    orders_df[col] = pd.to_datetime(orders_df[col], errors="coerce")

orders_df["year_month"] = orders_df["order_purchase_timestamp"].dt.to_period("M").astype(str)

# ---------------------------------------------------------------------------
# 3. Merge datasets
# ---------------------------------------------------------------------------
print("[3/5] Merge datasets …")

# Terjemahan kategori produk
products_df = products_df.merge(
    category_translation_df, on="product_category_name", how="left"
)

# Merge utama: orders → customers → order_items → products → payments → reviews
merged = orders_df.merge(customers_df, on="customer_id", how="inner")
merged = merged.merge(order_items_df[["order_id", "product_id", "price", "freight_value"]],
                      on="order_id", how="inner")
merged = merged.merge(
    products_df[["product_id", "product_category_name", "product_category_name_english"]],
    on="product_id", how="left",
)
merged = merged.merge(
    order_payments_df[["order_id", "payment_type", "payment_value"]],
    on="order_id", how="inner",
)
merged = merged.merge(
    order_reviews_df[["order_id", "review_score"]],
    on="order_id", how="left",
)

# Drop duplikat (karena bisa ada multi-item / multi-payment per order)
# kita simpan semua baris untuk fleksibilitas analisis
print(f"   Hasil merge: {len(merged)} baris")

# ---------------------------------------------------------------------------
# 4. Filtering – hanya order yang telah delivered, periode Jan 2017 – Ags 2018
# ---------------------------------------------------------------------------
print("[4/5] Filtering data …")

merged = merged[merged["order_status"] == "delivered"].copy()
merged = merged[
    (merged["year_month"] >= "2017-01") & (merged["year_month"] <= "2018-08")
].copy()

print(f"   Setelah filter delivered + periode: {len(merged)} baris")

# ---------------------------------------------------------------------------
# 5. Pilih kolom yang diperlukan & simpan
# ---------------------------------------------------------------------------
print("[5/5] Menyimpan main_data.csv …")

columns_to_keep = [
    "order_id",
    "customer_unique_id",
    "customer_state",
    "order_purchase_timestamp",
    "year_month",
    "product_category_name_english",
    "payment_type",
    "payment_value",
    "review_score",
]

merged[columns_to_keep].to_csv(OUTPUT_PATH, index=False)
print(f"   [OK] Berhasil disimpan ke: {OUTPUT_PATH}")
print(f"   Total baris: {len(merged)}")

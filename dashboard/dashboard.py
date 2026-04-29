
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import streamlit as st

# ============================================================================
# 1. PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Dashboard Analitik E-Commerce Olist",
    page_icon="",
    layout="wide",
)

# -- Custom Font & Styling --
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Playfair Display', serif !important;
    }

    .stMetric label {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    .stMetric [data-testid="stMetricValue"] {
        font-family: 'Playfair Display', serif !important;
    }

    .small-subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.85rem;
        color: #888;
        margin-top: -10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 2. DATA LOADING (cached)
# ============================================================================
@st.cache_data
def load_data():
    """Membaca main_data.csv dan melakukan parsing datetime."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "main_data.csv")
    df = pd.read_csv(filepath)
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df

try:
    all_data = load_data()
except FileNotFoundError:
    st.error(
        "⚠️ File `main_data.csv` tidak ditemukan di folder `dashboard/`. "
        "Jalankan `python dashboard/prepare_data.py` terlebih dahulu."
    )
    st.stop()

# ============================================================================
# 3. SIDEBAR – Panel Interaktif
# ============================================================================
with st.sidebar:
    st.title("Olist Dashboard")
    st.markdown("---")

    # -- Filter Waktu --
    st.subheader("Filter Waktu")
    min_date = all_data["order_purchase_timestamp"].min().date()
    max_date = all_data["order_purchase_timestamp"].max().date()
    start_date = st.date_input("Dari", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("Sampai", value=max_date, min_value=min_date, max_value=max_date)

    st.markdown("---")

    # -- Filter State --
    st.subheader("Filter Negara Bagian")

    # Mapping kode state Brasil → nama lengkap
    STATE_NAME_MAP = {
        "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
        "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
        "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
        "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba",
        "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
        "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
        "TO": "Tocantins",
    }
    # Reverse mapping: nama → kode
    NAME_TO_CODE = {v: k for k, v in STATE_NAME_MAP.items()}

    all_state_codes = sorted(all_data["customer_state"].dropna().unique())
    all_state_names = sorted([STATE_NAME_MAP.get(c, c) for c in all_state_codes])
    selected_state_names = st.multiselect("Pilih State", options=all_state_names, default=[])

    st.markdown("---")

    # -- Filter Metode Pembayaran --
    st.subheader("Filter Metode Pembayaran")
    all_payments = sorted(all_data["payment_type"].dropna().unique())
    selected_payments = st.multiselect("Pilih Metode", options=all_payments, default=[])

# ============================================================================
# 4. APPLY FILTERS → filtered_df
# ============================================================================
filtered_df = all_data.copy()

# Filter waktu
filtered_df = filtered_df[
    (filtered_df["order_purchase_timestamp"].dt.date >= start_date)
    & (filtered_df["order_purchase_timestamp"].dt.date <= end_date)
]

# Filter state (jika dipilih) – konversi nama kembali ke kode
if selected_state_names:
    selected_codes = [NAME_TO_CODE.get(n, n) for n in selected_state_names]
    filtered_df = filtered_df[filtered_df["customer_state"].isin(selected_codes)]

# Filter payment (jika dipilih)
if selected_payments:
    filtered_df = filtered_df[filtered_df["payment_type"].isin(selected_payments)]

# ============================================================================
# 5. HEADER
# ============================================================================
st.title("Dashboard Analitik E-Commerce Olist")
st.markdown(
    '<p class="small-subtitle">Coding Camp by DBS Foundation And Dicoding</p>',
    unsafe_allow_html=True,
)
st.markdown(
    "Analisis performa platform **Olist** berdasarkan data pesanan yang berhasil "
    "dikirim (**delivered**) pada periode **Januari 2017 – Agustus 2018**."
)
st.markdown("---")

# ============================================================================
# 6. BARIS 1 – KPI SCORECARDS
# ============================================================================
total_orders = filtered_df["order_id"].nunique()
total_revenue = filtered_df["payment_value"].sum()
aov = total_revenue / total_orders if total_orders > 0 else 0
delivered_pct = 100.0  # Semua data sudah difilter delivered di prepare_data.py

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Pesanan", f"{total_orders:,}")
with col2:
    st.metric("Total Pendapatan (GMV)", f"R$ {total_revenue:,.2f}")
with col3:
    st.metric("Rata-rata Nilai Pesanan (AOV)", f"R$ {aov:,.2f}")
with col4:
    st.metric("Pesanan Berhasil", f"{delivered_pct:.1f}%")

st.markdown("---")

# ============================================================================
# 7. BARIS 2 – VISUALISASI UTAMA (2 kolom)
# ============================================================================
row2_left, row2_right = st.columns(2)

# ---------- PERTANYAAN 1: Tren MoM ----------
with row2_left:
    st.subheader("Pertanyaan 1: Tren Pertumbuhan Pesanan Bulanan (MoM)")

    monthly = (
        filtered_df.groupby("year_month")["order_id"]
        .nunique()
        .reset_index()
        .rename(columns={"order_id": "total_orders"})
        .sort_values("year_month")
    )
    monthly["mom_growth_pct"] = monthly["total_orders"].pct_change() * 100

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    sns.lineplot(
        data=monthly,
        x="year_month",
        y="total_orders",
        marker="o",
        linewidth=2.5,
        color="steelblue",
        label="Total Pesanan",
        ax=ax1,
    )

    # Highlight bulan dengan penurunan > 10%
    drop_months = monthly[monthly["mom_growth_pct"] < -10]
    if not drop_months.empty:
        sns.scatterplot(
            data=drop_months,
            x="year_month",
            y="total_orders",
            color="red",
            s=200,
            zorder=5,
            label="Penurunan > 10%",
            ax=ax1,
        )

    # Anotasi persentase
    for i in range(1, len(monthly)):
        x = monthly["year_month"].iloc[i]
        y = monthly["total_orders"].iloc[i]
        pct = monthly["mom_growth_pct"].iloc[i]
        if pd.isna(pct):
            continue
        if pct < -10:
            ax1.text(x, y - y * 0.08, f"{pct:.1f}%", color="red", ha="center", fontweight="bold", fontsize=8)
        elif pct < 0:
            ax1.text(x, y - y * 0.08, f"{pct:.1f}%", color="darkred", ha="center", fontsize=7)
        else:
            ax1.text(x, y + y * 0.04, f"+{pct:.1f}%", color="green", ha="center", fontsize=7)

    ax1.set_title("Tren Pesanan Bulanan (MoM)", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Bulan", fontsize=10)
    ax1.set_ylabel("Total Pesanan", fontsize=10)
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(fontsize=8)
    plt.tight_layout()
    st.pyplot(fig1)

# ---------- PERTANYAAN 3: Segmentasi RFM ----------
with row2_right:
    st.subheader("Pertanyaan 3: Segmentasi Pelanggan (RFM)")

    # Hitung RFM
    reference_date = filtered_df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (
        filtered_df.groupby("customer_unique_id")
        .agg(
            Recency=("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),
            Frequency=("order_id", "nunique"),
            Monetary=("payment_value", "sum"),
        )
        .reset_index()
    )

    # Scoring – Recency: semakin kecil semakin bagus (skor 5)
    rfm["R_Score"] = pd.qcut(rfm["Recency"], q=5, labels=[5, 4, 3, 2, 1])
    rfm["R_Score"] = rfm["R_Score"].astype(int)

    # Segmentasi berdasarkan R_Score
    def assign_segment(r):
        if r >= 4:
            return "Active"
        elif r >= 3:
            return "At Risk"
        else:
            return "Lost"

    rfm["Segment"] = rfm["R_Score"].apply(assign_segment)

    segment_summary = (
        rfm.groupby("Segment")["customer_unique_id"]
        .count()
        .reset_index()
        .rename(columns={"customer_unique_id": "Total_Customers"})
    )
    segment_summary["Percentage (%)"] = (
        segment_summary["Total_Customers"]
        / segment_summary["Total_Customers"].sum()
        * 100
    ).round(2)

    # Donut chart
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    colors = ["#2ecc71", "#f39c12", "#e74c3c"]
    wedges, texts, autotexts = ax3.pie(
        segment_summary["Total_Customers"],
        labels=segment_summary["Segment"],
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        pctdistance=0.75,
        textprops={"fontsize": 11},
    )
    # Inner circle → donut
    centre_circle = plt.Circle((0, 0), 0.50, fc="white")
    ax3.add_artist(centre_circle)
    ax3.set_title("Distribusi Segmen Pelanggan (RFM)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig3)

st.markdown("---")

# ============================================================================
# 8. BARIS 3 – VISUALISASI KINERJA (2 kolom)
# ============================================================================
row3_left, row3_right = st.columns(2)

# ---------- PERTANYAAN 2: Kategori Produk Kritis ----------
with row3_left:
    st.subheader("Pertanyaan 2: Kategori Produk dengan Review Rendah")

    cat_perf = (
        filtered_df.groupby("product_category_name_english")
        .agg(
            total_orders=("order_id", "nunique"),
            avg_review=("review_score", "mean"),
        )
        .reset_index()
    )

    # Filter: orders > 1000 & avg review < 4.0
    bad_cats = cat_perf[
        (cat_perf["total_orders"] > 1000) & (cat_perf["avg_review"] < 4.0)
    ].sort_values("avg_review")

    if bad_cats.empty:
        st.info("Tidak ada kategori yang memenuhi kriteria (orders > 1000 & review < 4.0) pada filter saat ini.")
    else:
        fig2, ax2 = plt.subplots(figsize=(8, max(4, len(bad_cats) * 0.6 + 1)))
        palette = sns.color_palette("YlOrRd_r", len(bad_cats))
        sns.barplot(
            data=bad_cats,
            x="avg_review",
            y="product_category_name_english",
            hue="product_category_name_english",
            palette=palette,
            legend=False,
            ax=ax2,
        )
        # Garis threshold 4.0
        ax2.axvline(x=4.0, color="gray", linestyle="--", linewidth=1, label="Batas 4.0")

        # Anotasi skor
        for i, row in enumerate(bad_cats.itertuples()):
            ax2.text(
                row.avg_review + 0.02,
                i,
                f"{row.avg_review:.2f}  ({row.total_orders:,} pesanan)",
                va="center",
                fontsize=9,
            )

        ax2.set_title(
            "Kategori Kritis (Orders > 1.000 & Review < 4.0)",
            fontsize=13,
            fontweight="bold",
        )
        ax2.set_xlabel("Rata-rata Skor Review", fontsize=10)
        ax2.set_ylabel("")
        ax2.legend(fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2)

# ---------- PERTANYAAN 4: Target State ----------
with row3_right:
    st.subheader("Pertanyaan 4: Target Negara Bagian untuk Optimasi")

    # Data: customer spending per unique customer
    cust_spending = (
        filtered_df.groupby(["customer_unique_id", "customer_state"])["payment_value"]
        .sum()
        .reset_index()
        .rename(columns={"payment_value": "total_spending"})
    )

    national_avg = cust_spending["total_spending"].mean()

    state_perf = (
        cust_spending.groupby("customer_state")
        .agg(
            total_customers=("customer_unique_id", "nunique"),
            avg_spending=("total_spending", "mean"),
        )
        .reset_index()
        .sort_values("total_customers", ascending=False)
    )

    # Filter: customers > 2000 & avg spending < national avg
    target_states = state_perf[
        (state_perf["total_customers"] > 2000)
        & (state_perf["avg_spending"] < national_avg)
    ].sort_values("avg_spending")

    if target_states.empty:
        st.info("Tidak ada state yang memenuhi kriteria pada filter saat ini.")
    else:
        fig4, ax4 = plt.subplots(figsize=(8, max(4, len(target_states) * 0.6 + 1)))

        bar_colors = ["#e74c3c" if v < national_avg else "#2ecc71" for v in target_states["avg_spending"]]

        ax4.barh(
            target_states["customer_state"],
            target_states["avg_spending"],
            color=bar_colors,
        )
        # Garis rata-rata nasional
        ax4.axvline(
            x=national_avg,
            color="steelblue",
            linestyle="--",
            linewidth=1.5,
            label=f"Rata-rata Nasional (R$ {national_avg:,.2f})",
        )

        # Anotasi
        for i, row in enumerate(target_states.itertuples()):
            ax4.text(
                row.avg_spending + 1,
                i,
                f"R$ {row.avg_spending:,.2f}  ({row.total_customers:,} pelanggan)",
                va="center",
                fontsize=9,
            )

        ax4.set_title(
            "Target State: Pelanggan > 2.000 & Spending < Rata-rata",
            fontsize=13,
            fontweight="bold",
        )
        ax4.set_xlabel("Rata-rata Spending per Pelanggan (R$)", fontsize=10)
        ax4.set_ylabel("")
        ax4.legend(fontsize=8)
        ax4.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig4)

st.markdown("---")
st.caption("© 2024 Dashboard Analitik E-Commerce Olist | Data: Kaggle Brazilian E-Commerce Public Dataset")

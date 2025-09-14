import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re

st.set_page_config(page_title="Raw to Ready ✨", page_icon="🧹", layout="wide")

# ---------------------------
# Custom CSS for Theme
# ---------------------------
theme_css = """
<style>
    body {
        background-color: #F4F6F6;
    }
    .main-title {
        text-align: center;
        font-size: 2.5em;
        font-weight: bold;
        color: #2E86C1;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2em;
        color: #555;
        margin-bottom: 30px;
    }
    .report-card {
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
        border-left: 6px solid #2E86C1;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    .step-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #117A65;
        margin-top: 20px;
    }
</style>
"""
st.markdown(theme_css, unsafe_allow_html=True)

# ---------------------------
# Helper functions
# ---------------------------
def standardize_dates(series):
    def parse_date(x):
        for fmt in ("%Y-%m-%d", "%d/%m/%y", "%d/%m/%Y", "%b %d, %Y", "%Y.%m.%d"):
            try:
                return datetime.strptime(str(x), fmt).strftime("%Y-%m-%d")
            except:
                continue
        return x
    return series.apply(parse_date)

def normalize_text(series):
    return series.astype(str).str.strip().str.lower().str.title()

def validate_emails(series):
    return series.apply(lambda x: x if re.match(r"[^@]+@[^@]+\.[^@]+", str(x)) else "invalid@example.com")

def fill_missing(df, method="N/A"):
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].isnull().sum() > 0:
            if method == "N/A":
                df_copy[col].fillna("N/A", inplace=True)
            elif method == "Mean" and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col].fillna(df_copy[col].mean(), inplace=True)
            elif method == "Median" and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col].fillna(df_copy[col].median(), inplace=True)
            elif method == "Most Frequent":
                df_copy[col].fillna(df_copy[col].mode()[0], inplace=True)
    return df_copy

# ---------------------------
# Hero Section
# ---------------------------
st.markdown("<div class='main-title'>🧹 Raw to Ready ✨</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Upload your messy CSV, clean it in a few clicks, and download a ready-to-use dataset </div>", unsafe_allow_html=True)

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Data Cleaning Wizard")
st.sidebar.markdown("Follow the steps below:")

# Step 1: Upload
uploaded_file = st.sidebar.file_uploader("📥 Step 1: Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Save original stats
    rows_before = int(len(df))
    nulls_before = int(df.isnull().sum().sum())
    duplicates_before = int(df.duplicated().sum())

    # Step 2: Options
    st.sidebar.markdown("### ⚙️ Step 2: Choose Cleaning Options")
    fill_method = st.sidebar.selectbox("Missing Values", ["N/A", "Mean", "Median", "Most Frequent"])
    with st.sidebar.expander("Advanced Options"):
        do_duplicates = st.checkbox("Remove duplicates")
        do_standardize_cols = st.checkbox("Standardize column names")
        do_normalize_text = st.checkbox("Normalize text (names, cities)")
        do_fix_dates = st.checkbox("Fix date formats")
        do_validate_emails = st.checkbox("Validate emails")

    # Tabs for Raw vs Cleaned data
    tab1, tab2 = st.tabs(["🧹 Raw Data Preview", "✨ Cleaned Data Preview"])

    with tab1:
        st.dataframe(df.head())

    # Step 3: Run Cleaning
    if st.sidebar.button("🧹 Step 3: Run Cleaning"):
        df_cleaned = df.copy()

        # Apply cleaning
        df_cleaned = fill_missing(df_cleaned, method=fill_method)
        if do_duplicates:
            df_cleaned.drop_duplicates(inplace=True)
        if do_standardize_cols:
            df_cleaned.columns = [c.strip().lower().replace(" ", "_") for c in df_cleaned.columns]
        if do_normalize_text:
            for col in df_cleaned.select_dtypes(include=["object"]).columns:
                df_cleaned[col] = normalize_text(df_cleaned[col])
        if do_fix_dates:
            for col in df_cleaned.columns:
                if "date" in col.lower():
                    df_cleaned[col] = standardize_dates(df_cleaned[col])
        if do_validate_emails:
            for col in df_cleaned.columns:
                if "email" in col.lower():
                    df_cleaned[col] = validate_emails(df_cleaned[col])

        # Save cleaned stats
        rows_after = int(len(df_cleaned))
        nulls_after = int(df_cleaned.isnull().sum().sum())
        duplicates_after = int(df_cleaned.duplicated().sum())

        # Report
        st.success("Cleaning completed successfully!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='report-card'><h3>Rows</h3><p>{rows_after}</p><small>Δ {rows_after - rows_before}</small></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='report-card'><h3>Nulls</h3><p>{nulls_after}</p><small>Fixed {nulls_before - nulls_after}</small></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='report-card'><h3>Duplicates</h3><p>{duplicates_after}</p><small>Removed {duplicates_before - duplicates_after}</small></div>", unsafe_allow_html=True)

        with tab2:
            st.dataframe(df_cleaned.head())

        # Step 4: Download or Restart
        st.subheader("📥 Step 4: Save")
        csv = df_cleaned.to_csv(index=False).encode("utf-8")
        colA = st.columns(2)
        with colA:
            st.download_button("⬇️ Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")

else:
    st.info(" Upload a CSV file in the sidebar to get started!")


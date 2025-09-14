import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re

st.set_page_config(page_title="Raw to Ready ✨", page_icon="🧹", layout="wide")

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
# Styling
# ---------------------------
st.markdown(
    """
    <style>
    body {
        background-color: #f4f6f9;
    }
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .css-1d391kg, .css-1v3fvcr {
        background-color: #2C3E50 !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Sidebar (steps)
# ---------------------------
st.sidebar.title("🧹 Cleaning Pipeline")
st.sidebar.markdown("Follow the steps below:")

# Initialize session state for reset
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "options_reset" not in st.session_state:
    st.session_state.options_reset = False

# Step 1: File upload
uploaded_file = st.sidebar.file_uploader("📥 Upload CSV", type=["csv"])

# Reset options if a new file is uploaded
if uploaded_file is not None and uploaded_file != st.session_state.last_uploaded:
    st.session_state.last_uploaded = uploaded_file
    st.session_state.options_reset = True
else:
    st.session_state.options_reset = False

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Save original stats
    rows_before = len(df)
    nulls_before = df.isnull().sum().sum()
    duplicates_before = df.duplicated().sum()

    st.title("📊 Raw to Ready Data Cleaner")
    st.markdown("Make your dataset clean, consistent, and ready for analysis 🚀")

    # Step 2: Choose options
    st.sidebar.subheader("⚙️ Options")

    # Reset cleaning options if new file uploaded
    fill_method = st.sidebar.selectbox(
        "Missing Values",
        ["N/A", "Mean", "Median", "Most Frequent"],
        index=0 if st.session_state.options_reset else None
    )
    do_duplicates = st.sidebar.checkbox("Remove duplicates", value=False if st.session_state.options_reset else None)
    do_standardize_cols = st.sidebar.checkbox("Standardize column names", value=False if st.session_state.options_reset else None)
    do_normalize_text = st.sidebar.checkbox("Normalize text (names, cities)", value=False if st.session_state.options_reset else None)
    do_fix_dates = st.sidebar.checkbox("Fix date formats", value=False if st.session_state.options_reset else None)
    do_validate_emails = st.sidebar.checkbox("Validate emails", value=False if st.session_state.options_reset else None)

    # Step 3: Preview raw data
    st.subheader("📂 Raw Data Preview")
    st.dataframe(df.head())

    # Step 4: Apply cleaning
    if st.sidebar.button("🧹 Run Cleaning"):
        df_cleaned = df.copy()

        # Handle missing values
        df_cleaned = fill_missing(df_cleaned, method=fill_method)

        # Remove duplicates
        if do_duplicates:
            df_cleaned.drop_duplicates(inplace=True)

        # Standardize column names
        if do_standardize_cols:
            df_cleaned.columns = [c.strip().lower().replace(" ", "_") for c in df_cleaned.columns]

        # Normalize text
        if do_normalize_text:
            for col in df_cleaned.select_dtypes(include=["object"]).columns:
                df_cleaned[col] = normalize_text(df_cleaned[col])

        # Fix dates
        if do_fix_dates:
            for col in df_cleaned.columns:
                if "date" in col.lower():
                    df_cleaned[col] = standardize_dates(df_cleaned[col])

        # Validate emails
        if do_validate_emails:
            for col in df_cleaned.columns:
                if "email" in col.lower():
                    df_cleaned[col] = validate_emails(df_cleaned[col])

        # Save cleaned stats
        rows_after = len(df_cleaned)
        nulls_after = df_cleaned.isnull().sum().sum()
        duplicates_after = df_cleaned.duplicated().sum()

        st.success("✅ Cleaning completed!")

        # Step 5: Report
        st.subheader("📑 Data Cleaning Report")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", rows_before, rows_after - rows_before)
        col2.metric("Nulls Fixed", nulls_before, f"{nulls_before - nulls_after}")
        col3.metric("Duplicates Removed", f"{duplicates_before - duplicates_after}")

        st.write("### 🔍 Before vs After Summary")
        report_df = pd.DataFrame({
            "Metric": ["Rows", "Null values", "Duplicates"],
            "Before": [rows_before, nulls_before, duplicates_before],
            "After": [rows_after, nulls_after, duplicates_after],
        })
        st.table(report_df)

        # Step 6: Show cleaned data
        st.subheader("✨ Cleaned Data Preview")
        st.dataframe(df_cleaned.head())

        # Step 7: Download option
        csv = df_cleaned.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Cleaned CSV", csv, "cleaned_data.csv", "text/csv")

else:
    st.info("👆 Upload a CSV file to get started!")

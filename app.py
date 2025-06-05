import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Transaction Filter App", layout="wide")
st.title("📊 Transaction CSV Filter & Export")

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV file loaded successfully.")

    st.subheader("📋 Available Filters")
    filters = {}

    # Define target keywords to match
    filter_keywords = ["wallet", "asset", "categorisation", "operation", "type"]

    # Map detected columns based on keyword presence
    matched_columns = []
    for col in df.columns:
        for keyword in filter_keywords:
            if keyword in col.lower():
                matched_columns.append(col)
                break

    col1, col2 = st.columns(2)

    for i, col in enumerate(matched_columns):
        with (col1 if i % 2 == 0 else col2):
            unique_vals = df[col].dropna().unique().tolist()
            selected_vals = st.multiselect(f"{col}", options=unique_vals)
            if selected_vals:
                filters[col] = selected_vals

    # Apply filters
    filtered_df = df.copy()
    for col, selected_vals in filters.items():
        filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    st.subheader("🔍 Filtered Results")
    st.dataframe(filtered_df, use_container_width=True)

    # Download button
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_bytes = convert_df(filtered_df)

    st.download_button(
        label="📅 Download Filtered CSV",
        data=csv_bytes,
        file_name="filtered_report.csv",
        mime="text/csv"
    )

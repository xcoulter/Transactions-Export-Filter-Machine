import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Transactions Report Analyser", layout="wide")
st.title("📊 Transactions Report Analyser")

# Page selector
st.markdown("##")
pages = {
    "Home": "home",
    "Report Filtering": "filtering",
    "Balances": "balances"
}
selected_page = st.radio("Navigation", list(pages.keys()), horizontal=True)

if selected_page == "Home":
    st.markdown("""
    Welcome to the **Transactions Report Analyser**.

    This app helps you quickly analyze and work with your transaction reports by:
    - Uploading and previewing CSV files
    - Filtering by wallet, asset, operation type, and more
    - Narrowing down transactions by value range
    - Exporting refined datasets for reporting or auditing

    Use the navigation bar above to explore available features.
    """)

elif selected_page == "Report Filtering":
    # Upload CSV
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("CSV file loaded successfully.")

        st.subheader("📋 Available Filters")
        filters = {}
        range_filters = {}

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

                # Embed range sliders in expanders for numeric columns
                if col in ["assetvalueInBaseCurrency", "assetAmount"]:
                    try:
                        min_val, max_val = float(df[col].min()), float(df[col].max())
                        with st.expander(f"Set range for {col}"):
                            range_min, range_max = st.slider(
                                f"Select range for {col}",
                                min_value=min_val,
                                max_value=max_val,
                                value=(min_val, max_val),
                                key=f"slider_{col}"
                            )
                            range_filters[col] = (range_min, range_max)
                    except:
                        st.warning(f"Column {col} contains non-numeric values and cannot be filtered by range.")

        # Apply filters
        filtered_df = df.copy()
        for col, selected_vals in filters.items():
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

        for col, (min_val, max_val) in range_filters.items():
            filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]

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

elif selected_page == "Balances":
    st.subheader("💰 Balances by Wallet and Asset")
    uploaded_file = st.file_uploader("Upload a CSV file for balances", type=["csv"], key="balances_uploader")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("CSV file loaded successfully.")

        # Try to detect the date column
        date_col = next((col for col in df.columns if "date" in col.lower()), None)
        if not date_col:
            st.error("No date column found in the uploaded file.")
        else:
            # Normalize values
            df["assetAmount"] = df["assetAmount"].abs()
            df["feeAmount"] = df["feeAmount"].abs()

            # Parse date
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            df["month"] = df[date_col].dt.month
            df["year"] = df[date_col].dt.year

            # Asset transactions
            asset_df = df[df["operation"].isin(["DEPOSIT", "WITHDRAW"])].copy()
            asset_df["direction"] = asset_df["operation"].apply(lambda x: 1 if x == "DEPOSIT" else -1)
            asset_df["asset_balance"] = asset_df["assetAmount"] * asset_df["direction"]
            asset_df = asset_df[["walletName", "asset", "asset_balance", date_col, "month", "year"]].rename(columns={"asset_balance": "amount"})

            # Fee transactions
            fee_df = df[df["operation"] == "FEE"].copy()
            fee_df["fee_balance"] = -fee_df["feeAmount"]
            fee_df = fee_df[["walletName", "feeAsset", "fee_balance", date_col, "month", "year"]].rename(columns={"feeAsset": "asset", "fee_balance": "amount"})

            # Combine
            combined = pd.concat([asset_df, fee_df], ignore_index=True)

            # Group and summarize
            balances = combined.groupby(["walletName", "asset", "year", "month"])["amount"].sum().reset_index()

            st.dataframe(balances, use_container_width=True)

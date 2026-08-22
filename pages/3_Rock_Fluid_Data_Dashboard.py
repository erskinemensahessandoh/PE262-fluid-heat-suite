"""
3_Rock_Fluid_Dashboard.py
===========================
Module C: Rock & Fluid Data Dashboard.

Lets the user upload a CSV of rock/fluid property data, view summary
statistics, filter interactively, view a histogram and a
porosity-permeability crossplot, and download the filtered data.
"""

import io

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="📊", layout="wide")
st.title("📊 Rock & Fluid Data Dashboard")
st.caption(
    "Upload a CSV of rock or fluid property data (e.g. core analysis "
    "results) to explore summary statistics, filter samples, and "
    "visualize relationships between properties."
)

# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload rock/fluid data (CSV)", type=["csv"],
    help="A sample dataset is available in the repository under "
         "sample_data/sample_core_data.csv if you'd like to try the "
         "dashboard before uploading your own file."
)

use_sample = False
if uploaded_file is None:
    use_sample = st.checkbox("Use the built-in sample core dataset instead", value=True)

df = None
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the uploaded file as a CSV: {e}")
        st.stop()
elif use_sample:
    try:
        df = pd.read_csv("sample_data/sample_core_data.csv")
    except FileNotFoundError:
        st.error("Sample dataset not found in the repository.")
        st.stop()

if df is None:
    st.info("Upload a CSV file, or check the box above to use the sample dataset.")
    st.stop()

if df.empty:
    st.error("The uploaded file contains no data.")
    st.stop()

# ---------------------------------------------------------------------------
# Data preview + summary statistics
# ---------------------------------------------------------------------------
st.subheader("Data Preview")
st.dataframe(df.head(20), use_container_width=True)
st.caption(f"{len(df)} rows × {len(df.columns)} columns loaded.")

st.subheader("Summary Statistics")
numeric_cols = df.select_dtypes(include="number").columns.tolist()

if not numeric_cols:
    st.warning("No numeric columns were found in this file, so summary "
               "statistics and charts cannot be generated.")
    st.stop()

st.dataframe(df[numeric_cols].describe().T, use_container_width=True)

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
st.subheader("Filter Samples")

filter_col = st.selectbox(
    "Column to filter on", options=numeric_cols,
    help="Choose a numeric column to filter the dataset by a minimum "
         "threshold, e.g. porosity_pct."
)

col_min = float(df[filter_col].min())
col_max = float(df[filter_col].max())

threshold = st.slider(
    f"Show only samples where {filter_col} >",
    min_value=col_min, max_value=col_max, value=col_min,
    help="Rows below this threshold are excluded from the filtered view, "
         "the charts below, and the downloaded CSV."
)

filtered_df = df[df[filter_col] > threshold].copy()
st.write(f"**{len(filtered_df)}** of {len(df)} samples match this filter.")

if filtered_df.empty:
    st.warning("No rows match the current filter. Adjust the threshold above.")
    st.stop()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
st.subheader("Charts")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Histogram**")
    hist_col = st.selectbox(
        "Column for histogram", options=numeric_cols, index=numeric_cols.index(filter_col),
        key="hist_col",
    )
    fig_hist = px.histogram(
        filtered_df, x=hist_col, nbins=25,
        title=f"Distribution of {hist_col}",
    )
    fig_hist.update_layout(height=400)
    st.plotly_chart(fig_hist, use_container_width=True)

with chart_col2:
    st.markdown("**Crossplot**")
    # Try to default to a porosity/permeability pair if present
    default_x = next((c for c in numeric_cols if "poros" in c.lower()), numeric_cols[0])
    default_y = next((c for c in numeric_cols if "perm" in c.lower()),
                      numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])

    x_col = st.selectbox("X-axis", options=numeric_cols,
                          index=numeric_cols.index(default_x), key="x_col")
    y_col = st.selectbox("Y-axis", options=numeric_cols,
                          index=numeric_cols.index(default_y), key="y_col")

    log_y = st.checkbox(
        "Log scale on Y-axis",
        value=("perm" in y_col.lower()),
        help="Permeability data commonly spans several orders of "
             "magnitude, so a log scale is usually clearer."
    )

    color_col = None
    non_numeric_cols = df.select_dtypes(exclude="number").columns.tolist()
    if non_numeric_cols:
        color_choice = st.selectbox(
            "Color by (optional)", options=["None"] + non_numeric_cols, key="color_col"
        )
        color_col = None if color_choice == "None" else color_choice

    fig_cross = px.scatter(
        filtered_df, x=x_col, y=y_col, color=color_col,
        title=f"{y_col} vs {x_col}",
        log_y=log_y,
    )
    fig_cross.update_layout(height=400)
    st.plotly_chart(fig_cross, use_container_width=True)

# ---------------------------------------------------------------------------
# Download filtered data
# ---------------------------------------------------------------------------
st.subheader("Download Filtered Data")

csv_buffer = io.StringIO()
filtered_df.to_csv(csv_buffer, index=False)

st.download_button(
    label="Download filtered data (CSV)",
    data=csv_buffer.getvalue(),
    file_name="filtered_rock_fluid_data.csv",
    mime="text/csv",
)

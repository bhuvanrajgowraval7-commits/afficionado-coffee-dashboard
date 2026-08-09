import streamlit as st
import pandas as pd
import plotly.express as px


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Afficionado Coffee Roasters",
    page_icon="☕",
    layout="wide",
)


# -----------------------------
# Load and prepare the data
# -----------------------------
@st.cache_data
def load_data():
    data = pd.read_excel(
        "Afficionado Coffee Roasters (1).xlsx",
        sheet_name="Transactions",
    )

    # Revenue for each transaction
    data["revenue"] = data["transaction_qty"] * data["unit_price"]

    return data


df = load_data()


# -----------------------------
# Dashboard header
# -----------------------------
st.title("☕ Afficionado Coffee Roasters")
st.subheader("Product Optimization & Revenue Contribution Analysis")

st.write(
    "This dashboard looks at product popularity, revenue contribution, "
    "category performance, revenue concentration, and individual product performance."
)


# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Dashboard Filters")

store_options = ["All"] + sorted(
    df["store_location"].dropna().unique().tolist()
)
selected_store = st.sidebar.selectbox("Store Location", store_options)

category_options = ["All"] + sorted(
    df["product_category"].dropna().unique().tolist()
)
selected_category = st.sidebar.selectbox("Product Category", category_options)

product_type_options = ["All"] + sorted(
    df["product_type"].dropna().unique().tolist()
)
selected_product_type = st.sidebar.selectbox(
    "Product Type",
    product_type_options,
)

top_n = st.sidebar.slider(
    "Top-N Products",
    min_value=5,
    max_value=50,
    value=10,
    step=5,
)


# -----------------------------
# Apply the selected filters
# -----------------------------
filtered_df = df.copy()

if selected_store != "All":
    filtered_df = filtered_df[
        filtered_df["store_location"] == selected_store
    ]

if selected_category != "All":
    filtered_df = filtered_df[
        filtered_df["product_category"] == selected_category
    ]

if selected_product_type != "All":
    filtered_df = filtered_df[
        filtered_df["product_type"] == selected_product_type
    ]


# -----------------------------
# Key metrics
# -----------------------------
total_revenue = filtered_df["revenue"].sum()
total_units = filtered_df["transaction_qty"].sum()
total_transactions = filtered_df["transaction_id"].nunique()
product_count = filtered_df["product_id"].nunique()

average_transaction = (
    total_revenue / total_transactions
    if total_transactions
    else 0
)


st.header("Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(
    [1.2, 1, 1, 1.2, 1]
)

with col1:
    st.markdown("**Total Revenue**")
    st.markdown(
        f"<h3>${total_revenue:,.2f}</h3>",
        unsafe_allow_html=True
    )

with col2:
    st.markdown("**Units Sold**")
    st.markdown(
        f"<h3>{total_units:,.0f}</h3>",
        unsafe_allow_html=True
    )

with col3:
    st.markdown("**Transactions**")
    st.markdown(
        f"<h3>{total_transactions:,}</h3>",
        unsafe_allow_html=True
    )

with col4:
    st.markdown("**Average Transaction**")
    st.markdown(
        f"<h3>${average_transaction:,.2f}</h3>",
        unsafe_allow_html=True
    )

with col5:
    st.markdown("**Products**")
    st.markdown(
        f"<h3>{product_count}</h3>",
        unsafe_allow_html=True
    )

# -----------------------------
# Product-level summary
# -----------------------------
product_summary = (
    filtered_df
    .groupby(
        ["product_id", "product_detail", "product_category"],
        as_index=False,
    )
    .agg(
        units_sold=("transaction_qty", "sum"),
        revenue=("revenue", "sum"),
        transactions=("transaction_id", "nunique"),
    )
)

total_product_revenue = product_summary["revenue"].sum()

if total_product_revenue:
    product_summary["revenue_share"] = (
        product_summary["revenue"] / total_product_revenue
    ) * 100
else:
    product_summary["revenue_share"] = 0

product_summary["revenue_per_unit"] = (
    product_summary["revenue"] / product_summary["units_sold"]
)

product_summary["volume_rank"] = (
    product_summary["units_sold"]
    .rank(method="min", ascending=False)
    .astype(int)
)

product_summary["revenue_rank"] = (
    product_summary["revenue"]
    .rank(method="min", ascending=False)
    .astype(int)
)


# -----------------------------
# Product rankings
# -----------------------------
st.header("1. Product Rankings")

col1, col2 = st.columns(2)

with col1:
    top_revenue = (
        product_summary
        .sort_values("revenue", ascending=False)
        .head(top_n)
    )

    revenue_chart = px.bar(
        top_revenue.sort_values("revenue"),
        x="revenue",
        y="product_detail",
        orientation="h",
        title=f"Top {top_n} Products by Revenue",
        labels={
            "revenue": "Revenue ($)",
            "product_detail": "Product",
        },
    )

    st.plotly_chart(revenue_chart, use_container_width=True)


with col2:
    top_volume = (
        product_summary
        .sort_values("units_sold", ascending=False)
        .head(top_n)
    )

    volume_chart = px.bar(
        top_volume.sort_values("units_sold"),
        x="units_sold",
        y="product_detail",
        orientation="h",
        title=f"Top {top_n} Products by Sales Volume",
        labels={
            "units_sold": "Units Sold",
            "product_detail": "Product",
        },
    )

    st.plotly_chart(volume_chart, use_container_width=True)


# -----------------------------
# Category performance
# -----------------------------
st.header("2. Category Revenue Distribution")

category_summary = (
    filtered_df
    .groupby("product_category", as_index=False)
    .agg(
        revenue=("revenue", "sum"),
        units_sold=("transaction_qty", "sum"),
    )
)

total_category_revenue = category_summary["revenue"].sum()

if total_category_revenue:
    category_summary["revenue_share"] = (
        category_summary["revenue"] / total_category_revenue
    ) * 100
else:
    category_summary["revenue_share"] = 0


col1, col2 = st.columns(2)

with col1:
    category_chart = px.bar(
        category_summary.sort_values("revenue"),
        x="revenue",
        y="product_category",
        orientation="h",
        title="Revenue by Product Category",
        labels={
            "revenue": "Revenue ($)",
            "product_category": "Category",
        },
    )

    st.plotly_chart(category_chart, use_container_width=True)


with col2:
    category_pie = px.pie(
        category_summary,
        names="product_category",
        values="revenue",
        title="Category Revenue Share",
    )

    st.plotly_chart(category_pie, use_container_width=True)


# -----------------------------
# Popularity compared with revenue
# -----------------------------
st.header("3. Product Popularity vs Revenue")

median_units = product_summary["units_sold"].median()
median_revenue = product_summary["revenue"].median()

popularity_chart = px.scatter(
    product_summary,
    x="units_sold",
    y="revenue",
    size="revenue",
    color="product_category",
    hover_name="product_detail",
    hover_data={
        "units_sold": True,
        "revenue": ":.2f",
        "revenue_share": ":.2f",
    },
    title="Product Popularity vs Revenue",
    labels={
        "units_sold": "Units Sold",
        "revenue": "Revenue ($)",
        "product_category": "Category",
    },
)

popularity_chart.add_vline(
    x=median_units,
    line_dash="dash",
    annotation_text="Median Volume",
)

popularity_chart.add_hline(
    y=median_revenue,
    line_dash="dash",
    annotation_text="Median Revenue",
)

st.plotly_chart(popularity_chart, use_container_width=True)


# -----------------------------
# Classify products into segments
# -----------------------------
def classify_product(row):
    units = row["units_sold"]
    revenue = row["revenue"]

    if units >= median_units and revenue >= median_revenue:
        return "Hero Product"

    if units >= median_units and revenue < median_revenue:
        return "Volume Driver"

    if units < median_units and revenue >= median_revenue:
        return "Premium / Niche"

    return "Long Tail"


product_summary["product_segment"] = product_summary.apply(
    classify_product,
    axis=1,
)


# -----------------------------
# Product portfolio summary
# -----------------------------
st.subheader("Product Portfolio Segments")

segment_summary = (
    product_summary
    .groupby("product_segment")
    .agg(
        products=("product_id", "count"),
        units=("units_sold", "sum"),
        revenue=("revenue", "sum"),
    )
    .reset_index()
)

total_segment_revenue = segment_summary["revenue"].sum()

if total_segment_revenue:
    segment_summary["revenue_share"] = (
        segment_summary["revenue"] / total_segment_revenue
    ) * 100
else:
    segment_summary["revenue_share"] = 0

st.dataframe(segment_summary, use_container_width=True)


# -----------------------------
# Pareto analysis
# -----------------------------
st.header("4. Revenue Concentration — Pareto Analysis")

pareto = (
    product_summary
    .sort_values("revenue", ascending=False)
    .copy()
)

total_revenue_for_pareto = pareto["revenue"].sum()

if total_revenue_for_pareto:
    pareto["cumulative_revenue_pct"] = (
        pareto["revenue"].cumsum() / total_revenue_for_pareto
    ) * 100
else:
    pareto["cumulative_revenue_pct"] = 0

pareto["product_rank"] = range(1, len(pareto) + 1)

pareto_chart = px.line(
    pareto,
    x="product_rank",
    y="cumulative_revenue_pct",
    title="Cumulative Revenue by Product Rank",
    labels={
        "product_rank": "Product Revenue Rank",
        "cumulative_revenue_pct": "Cumulative Revenue (%)",
    },
)

pareto_chart.add_hline(
    y=80,
    line_dash="dash",
    annotation_text="80% Revenue",
)

st.plotly_chart(pareto_chart, use_container_width=True)


# -----------------------------
# Product drill-down
# -----------------------------
st.header("5. Product Drill-Down")

available_products = sorted(
    product_summary["product_detail"].unique()
)

selected_product = st.selectbox(
    "Select Product",
    available_products,
)

selected_data = product_summary[
    product_summary["product_detail"] == selected_product
].iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Units Sold",
    f"{selected_data['units_sold']:,.0f}",
)

col2.metric(
    "Revenue",
    f"${selected_data['revenue']:,.2f}",
)

col3.metric(
    "Revenue Share",
    f"{selected_data['revenue_share']:.2f}%",
)

col4.metric(
    "Revenue / Unit",
    f"${selected_data['revenue_per_unit']:.2f}",
)

st.write(
    f"**Product Segment:** {selected_data['product_segment']}"
)


# -----------------------------
# Detailed product table
# -----------------------------
st.subheader("Product Performance Table")

display_columns = [
    "product_detail",
    "product_category",
    "units_sold",
    "revenue",
    "revenue_share",
    "revenue_per_unit",
    "volume_rank",
    "revenue_rank",
    "product_segment",
]

product_table = (
    product_summary[display_columns]
    .sort_values("revenue", ascending=False)
)

st.dataframe(product_table, use_container_width=True)


# -----------------------------
# Footer
# -----------------------------
st.divider()

st.caption(
    "Afficionado Coffee Roasters | "
    "Product Optimization & Revenue Contribution Analysis"
)
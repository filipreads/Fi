import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Finance Dashboard", layout="wide", page_icon="💰")

@st.cache_data
def load_data():
    df = pd.read_csv("data.csv", parse_dates=["Datum"])
    df["Částka"] = pd.to_numeric(df["Částka"], errors="coerce")
    df["Month"] = df["Datum"].dt.to_period("M").astype(str)
    df["Year"] = df["Datum"].dt.year
    df["Kategorie"] = df["Kategorie"].fillna("Nezatříděná")
    df["Merchant"] = df["Merchant"].fillna("Unknown")
    return df.dropna(subset=["Datum", "Částka"])

df = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────[...]
with st.sidebar:
    st.title("🔍 Filters")
    min_d, max_d = df["Datum"].min().date(), df["Datum"].max().date()
    start, end = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
    cats = sorted(df["Kategorie"].dropna().unique().tolist())
    sel_cats = st.multiselect("Categories", cats, default=cats)
    mer_q = st.text_input("Merchant search", "")
    show_income = st.checkbox("Include income (+)", value=False)

# ── Filter ─────────────────────────────────────────────────────────────[...]
f = df[(df["Datum"].dt.date >= start) & (df["Datum"].dt.date <= end)]
if sel_cats:    f = f[f["Kategorie"].isin(sel_cats)]
if mer_q:       f = f[f["Merchant"].str.contains(mer_q, case=False, na=False)]
if not show_income: f = f[f["Částka"] < 0]

# ── KPIs ──────────────────────────────────────────────────────────────[...]
st.title("💰 Finance Dashboard")
st.caption(f"{len(f):,} transactions · {start} → {end}")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Transactions",    f"{len(f):,}")
k2.metric("Total spent",     f"{abs(f['Částka'].sum()):,.0f} CZK")
k3.metric("Average / tx",    f"{abs(f['Částka'].mean()):,.0f} CZK")
k4.metric("Unique merchants",f"{f['Merchant'].nunique():,}")
st.divider()

# ── Monthly trend ───────────────────────────────────────────────────────────[...]
monthly = f.groupby("Month", as_index=False)["Částka"].sum()
monthly["Částka"] = monthly["Částka"].abs()
fig_line = px.area(monthly, x="Month", y="Částka", markers=True,
                   title="Monthly spending", labels={"Částka":"CZK","Month":""})
fig_line.update_traces(line_color="#6366f1", fillcolor="rgba(99,102,241,0.15)")
st.plotly_chart(fig_line, use_container_width=True)

# ── Category & Merchant bars ───────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    by_cat = f.groupby("Kategorie", as_index=False)["Částka"].sum()
    by_cat["Částka"] = by_cat["Částka"].abs()
    by_cat = by_cat.sort_values("Částka", ascending=False)
    st.plotly_chart(
        px.bar(by_cat, x="Kategorie", y="Částka", title="By category",
               color="Částka", color_continuous_scale="Purples",
               labels={"Částka":"CZK","Kategorie":""}),
        use_container_width=True)
with col2:
    by_mer = f.groupby("Merchant", as_index=False)["Částka"].sum()
    by_mer["Částka"] = by_mer["Částka"].abs()
    by_mer = by_mer.sort_values("Částka", ascending=False).head(20)
    st.plotly_chart(
        px.bar(by_mer, y="Merchant", x="Částka", orientation="h",
               title="Top 20 merchants",
               color="Částka", color_continuous_scale="Teal",
               labels={"Částka":"CZK","Merchant":""}),
        use_container_width=True)

# ── Pie ──────────────────────────────────────────────────────────────[...]
st.plotly_chart(
    px.pie(by_cat, values="Částka", names="Kategorie",
           title="Category share", hole=0.4),
    use_container_width=True)

# ── Merchants Search List ───────────────────────────────────────────────────────
st.subheader("🏪 Merchants Search")
mer_search = st.text_input("Search merchants", key="merchant_search_list")

# Get all merchants with their stats
merchants_stats = f.groupby("Merchant", as_index=False).agg({
    "Částka": ["sum", "count", "mean"]
}).round(2)
merchants_stats.columns = ["Merchant", "Total", "Count", "Average"]
merchants_stats["Total"] = merchants_stats["Total"].abs()
merchants_stats["Average"] = merchants_stats["Average"].abs()
merchants_stats = merchants_stats.sort_values("Total", ascending=False)

# Filter merchants by search
if mer_search:
    merchants_stats = merchants_stats[
        merchants_stats["Merchant"].str.contains(mer_search, case=False, na=False)
    ]

# Display merchants list
if len(merchants_stats) > 0:
    st.dataframe(
        merchants_stats[["Merchant", "Total", "Count", "Average"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Merchant": st.column_config.TextColumn("Merchant", width="large"),
            "Total": st.column_config.NumberColumn("Total (CZK)", format="%.2f"),
            "Count": st.column_config.NumberColumn("Transactions", format="%d"),
            "Average": st.column_config.NumberColumn("Avg (CZK)", format="%.2f"),
        }
    )
else:
    st.info("No merchants found matching your search.")

# ── Table + export ──────────────────────────────────────────────────────────[...]
st.subheader("Transactions")
st.dataframe(
    f[["Datum","Částka","Kategorie","Merchant"]]
    .sort_values("Datum", ascending=False).reset_index(drop=True),
    use_container_width=True, height=420)
st.download_button(
    "⬇ Download filtered CSV",
    data=f.to_csv(index=False).encode("utf-8"),
    file_name="filtered_transactions.csv", mime="text/csv")

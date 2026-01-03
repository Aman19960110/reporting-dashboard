import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Reporting Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# GOOGLE SHEETS CONNECTION (CACHED)
# -------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("repoting").worksheet("Sheet1")

    df = pd.DataFrame(sheet.get_all_records())
    return df

df = load_data()

# -------------------------------------------------
# DATA CLEANING
# -------------------------------------------------
df["Date"] = pd.to_datetime(df["Date"])
df["Pnl"] = pd.to_numeric(df["Pnl"], errors="coerce")

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.title("Filters")

date_range = st.sidebar.date_input(
    "Date Range",
    [df["Date"].min(), df["Date"].max()]
)

start_date, end_date = map(pd.to_datetime, date_range)

df_filtered = df[
    (df["Date"] >= start_date) &
    (df["Date"] <= end_date)
].dropna(subset=["Pnl"])

# -------------------------------------------------
# EMPTY CHECK
# -------------------------------------------------
if df_filtered.empty:
    st.warning("No data available for the selected date range")
    st.stop()

# -------------------------------------------------
# KPI SECTION
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total PnL", f"₹ {int(df_filtered['Pnl'].sum())}", border=True)

col2.metric(
    "Stock CR Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy'] == 'stocks']['Pnl'].sum())}",
    border=True
)

col3.metric(
    "Index Box Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy'] == 'index']['Pnl'].sum())}",
    border=True
)

# -------------------------------------------------
# EQUITY CURVE
# -------------------------------------------------
df_filtered = df_filtered.sort_values("Date")
df_filtered["equity"] = df_filtered["Pnl"].cumsum()

col1, col2 = st.columns(2)

with col1:
    fig_eq = px.line(
        df_filtered,
        x="Date",
        y="equity",
        title="Equity Curve"
    )
    st.plotly_chart(fig_eq, use_container_width=True)

with col2:
    fig_pie = px.pie(
        df_filtered,
        names="Strategy",
        values="Pnl",
        title="PnL by Strategy"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

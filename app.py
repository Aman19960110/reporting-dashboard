import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title='Repotting-Dashboard',layout="wide",initial_sidebar_state="expanded")

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

st.sidebar.title("Filters")

df["Date"] = pd.to_datetime(df["Date"])

date_range = st.sidebar.date_input(
    "Date Range",
    [df["Date"].min(), df["Date"].max()]
)

start_date, end_date = map(pd.to_datetime, date_range)

df_filtered = df[
    (df["Date"] >= start_date) &
    (df["Date"] <= end_date)
]

col1, col2, col3 = st.columns(3)

col1.metric("Total PnL", f"₹ {int(df_filtered['Pnl'].sum()):,.0f}", border=True)
col2.metric(
    "Stock CR Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy']=='stocks']['Pnl'].sum()):,.0f}",
    border=True
)
col3.metric(
    "Index Box Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy']=='index']['Pnl'].sum()):,.0f}",
    border=True
)

import plotly.express as px

col1, col2 = st.columns(2)

with col1:
    fig_eq = px.bar(
        df_filtered,
        x="Date",
        y="Pnl",
        color='Strategy',
        title="Equity Curve"
    )
    st.plotly_chart(fig_eq,width='stretch',)

with col2:
    fig_dd = px.pie(
        df_filtered,
        names='Strategy',
        values='Pnl',
        title="Pnl by Strategy")
    st.plotly_chart(fig_dd, use_container_width=True)

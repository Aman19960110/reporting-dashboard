import streamlit as st
import pandas as pd
import datetime
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
def load_data(sheet='Sheet1'):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("repoting").worksheet(sheet)

    df = pd.DataFrame(sheet.get_all_records())
    return df

df = load_data()

# -------------------------------------------------
# DATA CLEANING
# -------------------------------------------------
df["Date"] = pd.to_datetime(df["Date"])
df["Pnl"] = pd.to_numeric(df["Pnl"], errors="coerce")



if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
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

grouped_df = df_filtered.groupby('Date')

# -------------------------------------------------
# KPI SECTION
# -------------------------------------------------
today = datetime.date.today().strftime("%d-%b-%Y")
st.title('PORTFOLIO REPORT ',text_alignment='center')
st.subheader(f'AS OF {today} ',text_alignment='center')
st.subheader(' AGILE VENTURES PVT LTD',text_alignment='center')





st.divider()

col1, col2, col3 = st.columns(3)
total_fund = pd.to_numeric(df_filtered['Total Fund'].iloc[0])
total_pnl = pd.to_numeric(df_filtered['Pnl'].sum())
pct_return = round((total_pnl/(total_fund*10**7))*100,2)

col1.metric("TOTAL INVESTEMENT", f"₹ {total_fund}Cr", border=True,)

col2.metric(
    "PNL",
    f"₹ {int(df_filtered['Pnl'].sum()):,}",
    border=True
)

col3.metric(
    "TOTAL RETURN (%)",
    f"{pct_return}%",
    border=True
)
st.divider()
# -------------------------------------------------
# EQUITY CURVE
# -------------------------------------------------
df_filtered = df_filtered.sort_values("Date")
df_filtered["equity"] = df_filtered["Pnl"].cumsum()
mask_equity = grouped_df['Pnl'].sum()
col1, col2 = st.columns(2)

with col1:
    fig_eq = px.line(
        x=mask_equity.index,
        y=mask_equity.cumsum(),
        title=" EQUITY CURVE ",
        labels={
            "Date": "Date",
            "equity": "Equity Value"
        }
    )

    # Improve hover information
    fig_eq.update_traces(
        mode="lines",
        hovertemplate=
        "<b>Date:</b> %{x}<br>"
        "<b>Equity:</b> ₹%{y:,.2f}"
        "<extra></extra>"
    )

    # Layout improvements
    fig_eq.update_layout(
        xaxis_tickformat="%d-%b-%Y",
        xaxis_title = 'Date',
        yaxis_title="Equity (₹)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # Improve line aesthetics
    fig_eq.update_traces(
        line=dict(width=2)
    )

    # Optional: range slider (great for long equity curves)
    fig_eq.update_xaxes(
        tickangle=-45
    )

    st.plotly_chart(fig_eq, use_container_width=True)


with col2:
    fig_pie = px.bar(
        x=mask_equity.index,
        y=mask_equity,
        title=" DAILY PNL ",
    )

    # Improve layout
    fig_pie.update_layout(
        xaxis_tickformat="%d-%b-%Y",
        yaxis_title="PnL (₹)",
        xaxis_title='Date',
        bargap=0.25,
        hovermode="x unified"
        
    )

    # Optional: rotate x-axis labels for readability
    fig_pie.update_xaxes(tickangle=-45)

    st.plotly_chart(fig_pie, use_container_width=True)


mask_fund = df_filtered.groupby(['Expiry','Strategy']).agg({
    'Fund used': 'sum',
    'Total Fund': 'first'
}).reset_index()


used_fund = df_filtered['Tfund used'].iloc[-1]
used_fund_pct = (used_fund/total_fund)*100
idle_fund = 100 - used_fund_pct

st.divider()

col1, col2,col3 = st.columns(3)

with col1:
    fig_pie_fund = px.pie(
        values=[used_fund_pct,idle_fund],
        names=['Used Fund','Idle Fund'],
        title="CAPITAL ALLOCATION (%)",
        hole=0.4
    )



    fig_pie_fund.update_traces(
        textinfo='percent+label',
        hovertemplate="%{label}: %{percent}",
        pull=[0.05]       # optional: separate slices slightly
    )

    st.plotly_chart(fig_pie_fund, use_container_width=True)

with col2:
    fig_pie_index = px.pie(
        data_frame=mask_fund,
        values='Fund used',
        names='Expiry',              # or 'Expiry'
        hover_data='Expiry',
        hole=0.4,
        title='CAPITAL DISTRIBUTION ACROSS EXPIRIES'
    )



    fig_pie_index.update_traces(
        textinfo='percent+label',
        pull=[0.05] * len(mask_fund)        # optional: separate slices slightly
    )

    st.plotly_chart(fig_pie_index, use_container_width=True)


with col3:
    fig_pie_stock = px.pie(
        data_frame=mask_fund,
        values='Fund used',
        names='Strategy',              # or 'Expiry'
        hover_data='Strategy',
        hole=0.4,
        title='CAPITAL DISTRIBUTION ACROSS PRODUCTS'
    )



    fig_pie_stock.update_traces(
        textinfo='percent+label',
        pull=[0.05] * len(mask_fund)        # optional: separate slices slightly
    )

    st.plotly_chart(fig_pie_stock, use_container_width=True)


st.divider()





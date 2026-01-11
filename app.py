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
stocks_df = load_data('Sheet2')
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

# -------------------------------------------------
# KPI SECTION
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total PnL", f"₹ {int(df_filtered['Pnl'].sum()):,}", border=True)

col2.metric(
    "Stock CR Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy'] == 'stocks']['Pnl'].sum()):,}",
    border=True
)

col3.metric(
    "Index Box Total PnL",
    f"₹ {int(df_filtered[df_filtered['Strategy'] == 'index']['Pnl'].sum()):,}",
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
    fig_pie = px.bar(x=df_filtered['Date'],
                     y=df_filtered['Pnl'],
                     color=df_filtered['Strategy'],
                     title='Daily Pnl'

    )
    st.plotly_chart(fig_pie, use_container_width=True)

mask = df_filtered.groupby(['Strategy','Expiry']).agg({
    'Pnl': "sum",

})
mask = mask.reset_index()


with col1:
    fig_pie_stocks = px.pie(
        data_frame=mask[mask['Strategy']=='stocks'],
        values='Pnl',
        names='Expiry',              # or 'Expiry'
        hover_data='Expiry',
        title='PnL Distribution by Expiry (STOCKS)'
    )



    fig_pie_stocks.update_traces(
        textinfo='percent+label',
        pull=[0.05] * len(mask)        # optional: separate slices slightly
    )

    st.plotly_chart(fig_pie_stocks, use_container_width=True)

with col2:
    fig_pie_index = px.pie(
        data_frame=mask[mask['Strategy']=='index'],
        values='Pnl',
        names='Expiry',              # or 'Expiry'
        hover_data='Expiry',
        title='PnL Distribution by Expiry (INDEX)'
    )



    fig_pie_index.update_traces(
        textinfo='percent+label',
        pull=[0.05] * len(mask)        # optional: separate slices slightly
    )

    st.plotly_chart(fig_pie_index, use_container_width=True)
###________stocks Data###
stock_mask = stocks_df['Data'].str.split(',',expand=True)
print(len(stock_mask.columns))
stock_mask.columns = ['abc','bce','symbol','cont_typ','expiry','strike','inst_type','inst_name','cef','efd','id','efg','buy_sell','quantity','price','ghi','mod','id_2','hij','datetime','datetime_02','xyz','pqr','stu','tqp']

stocks_df = stock_mask[['symbol','cont_typ','expiry','strike','inst_type','inst_name','id','buy_sell','quantity','price','id_2','datetime','datetime_02']].copy()
stocks_df['date'] = stocks_df['datetime_02'].str.extract(r'(\d{2} [A-Za-z]{3} \d{4})')

stocks_df['inst_type'] = stocks_df['inst_type'].astype(str).str.strip().str.upper()
stocks_df['buy_sell'] = pd.to_numeric(stocks_df['buy_sell'], errors='coerce').fillna(0).astype(int)
stocks_df['quantity'] = pd.to_numeric(stocks_df['quantity'], errors='coerce').fillna(0).astype(int)
stocks_df['price'] = pd.to_numeric(stocks_df['price'], errors='coerce')
stocks_df['strike'] = pd.to_numeric(stocks_df['strike'], errors='coerce')

stocks_df['date_str'] = stocks_df['datetime_02'].astype(str).str.extract(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', expand=False)
stocks_df['date'] = pd.to_datetime(stocks_df['date_str'], format="%d %b %Y", errors='coerce')

collected_data = []
for expiry in stocks_df['expiry'].unique():
  mask1 = stocks_df[stocks_df['expiry']==expiry]







  mask = mask1.groupby(['symbol','expiry','inst_type','buy_sell']).agg({
      'date' : 'first',
      'strike': 'mean',
      'quantity':'sum',
      'price': 'mean',

  }).reset_index()

  stock_list = mask['symbol'].unique()
  for stock in stock_list:
      data = mask[mask['symbol'] == stock]

      # Extract net_quantity


      # Get all rows where inst_type is 'XX'
      xx_data = data[data['inst_type'] == 'XX']

      for _, row in xx_data.iterrows():
          # For each row in xx_data, check the buy_sell condition
          if row['buy_sell'] == 2:
              # Calculate parity for 'open' trade
              parity = round(abs(data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 1)]['price'].iloc[0] -
                                data[(data['inst_type'] == 'PE') & (data['buy_sell'] == 2)]['price'].iloc[0] -
                                row['price']) -
                            data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 1)]['strike'].iloc[0], 2)
              trade = 'open'
              net_quantity = data[(data['inst_type'] == 'PE')&(data['buy_sell']==2)]['quantity'].iloc[0]
              expence = round(((data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 1)]['price'].iloc[0] * 0.00055) +
                        (data[(data['inst_type'] == 'PE') & (data['buy_sell'] == 2)]['price'].iloc[0] * 0.001625) +
                        (row['price']*0.00028118)),2)
              date = data['date'].iloc[0]
              expiry = data['expiry'].iloc[0]
          else:
              # Calculate parity for 'close' trade
              parity = round(-abs(-data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 2)]['price'].iloc[0] +
                                  data[(data['inst_type'] == 'PE') & (data['buy_sell'] == 1)]['price'].iloc[0] +
                                  row['price']) +
                            data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 2)]['strike'].iloc[0], 2)
              trade = 'close'
              net_quantity = data[(data['inst_type'] == 'PE')&(data['buy_sell']==1)]['quantity'].iloc[0]
              expence = round((data[(data['inst_type'] == 'CE') & (data['buy_sell'] == 2)]['price'].iloc[0]*0.001625) +
                        (data[(data['inst_type'] == 'PE') & (data['buy_sell'] == 1)]['price'].iloc[0]*0.00055) +
                        (row['price']*0.00005618),2)
              date = data['date'].iloc[0]
              expiry = data['expiry'].iloc[0]
          # Append the result for each row to the list
          collected_data.append({
              'date' : date,
              'expiry': expiry,
              'stock': stock,
              'net_quantity': net_quantity,
              'trade': trade,
              'parity': parity,
              'expence': expence
          })

# Convert to DataFrame if needed
collected_data_df = pd.DataFrame(collected_data)
collected_data_df['pnl'] = (collected_data_df['parity']-collected_data_df['expence'])*collected_data_df['net_quantity']

collected_data_df = collected_data_df[
    (collected_data_df["date"] >= start_date) &
    (collected_data_df["date"] <= end_date)
]
# Group by stock & expiry if not already aggregated
df_mask = collected_data_df.groupby(['stock', 'expiry'], as_index=False)['pnl'].sum()

fig_stocks_pnl = px.bar(
    df_mask,
    x="stock",
    y="pnl",
    color="expiry",
    barmode="group",
    title="Total PnL for Each Stock Across Expiries",
    text="pnl"
)

fig_stocks_pnl.update_traces(textposition='outside')
fig_stocks_pnl.update_layout(
    xaxis_title="Stock",
    yaxis_title="Total PnL",
    legend_title="Expiry",
    bargap=0.15,
)

st.plotly_chart(fig_stocks_pnl,width='stretch')





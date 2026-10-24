
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

from datetime import date

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------

st.set_page_config(
    page_title="Trade Life Cycle Management",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trade Life Cycle Management System")
st.caption(
    "Equity Trading | Trade Processing | Settlement Monitoring"
)

st.divider()

# -------------------------------
# DATABASE CONNECTION
# -------------------------------

conn = sqlite3.connect(
    "trades.db",
    check_same_thread=False
)

conn.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock TEXT NOT NULL,
        trade_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        trade_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending'
    )
""")

conn.commit()

# -------------------------------
# LOAD TRADE RECORDS
# -------------------------------

trades = pd.read_sql_query("""
    SELECT
        trade_id AS 'Trade ID',
        stock AS 'Stock',
        trade_type AS 'Trade Type',
        quantity AS 'Quantity',
        price AS 'Price (₹)',
        status AS 'Status',
        trade_date AS 'Trade Date'
    FROM trades
    ORDER BY trade_id DESC
""", conn)

trades["Trade Value (₹)"] = (
    trades["Quantity"] * trades["Price (₹)"]
)

# -------------------------------
# DASHBOARD METRICS
# -------------------------------

total_trades = len(trades)

total_value = trades["Trade Value (₹)"].sum()

pending_trades = (
    trades["Status"] == "Pending"
).sum()

settled_trades = (
    trades["Status"] == "Settled"
).sum()

metrics = st.columns(4)

metrics[0].metric(
    "Total Trades",
    total_trades
)

metrics[1].metric(
    "Total Trade Value",
    f"₹{total_value:,.2f}"
)

metrics[2].metric(
    "Pending Trades",
    int(pending_trades)
)

metrics[3].metric(
    "Settled Trades",
    int(settled_trades)
)

st.divider()

# -------------------------------
# TRADE STATUS CHART
# -------------------------------

st.subheader("Trade Status Overview")

if not trades.empty:

    status_counts = (
        trades["Status"]
        .value_counts()
        .reset_index()
    )

    status_counts.columns = [
        "Status",
        "Count"
    ]

    fig_pie = px.pie(
        status_counts,
        names="Status",
        values="Count",
        title="Distribution of Trade Status",
        hole=0.35
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

else:
    st.info(
        "No trades available yet. Enter a trade below to get started."
    )

# -------------------------------
# TRADE VALUE CHART
# -------------------------------

st.subheader("Trade Value by Stock")

if not trades.empty:

    fig_bar = px.bar(
        trades,
        x="Stock",
        y="Trade Value (₹)",
        color="Trade Type",
        title="Trade Value by Stock",
        hover_data=[
            "Trade ID",
            "Quantity",
            "Price (₹)",
            "Status"
        ]
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )

else:
    st.info(
        "The trade value chart will appear after you enter a trade."
    )

st.divider()

# -------------------------------
# TRADE RECORDS TABLE
# -------------------------------

st.subheader("Trade Records")

if not trades.empty:

    st.dataframe(
        trades,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No trade records found.")

st.info(
    "This application tracks simulated equity trades. "
    "It does not execute real stock market orders."
)

st.divider()

# -------------------------------
# ENTER A NEW TRADE
# -------------------------------

st.header("➕ Enter a New Trade")

stock = st.text_input(
    "Stock Symbol",
    placeholder="e.g., INFY"
).strip().upper()

trade_type = st.selectbox(
    "Trade Type",
    ["BUY", "SELL"]
)

quantity = st.number_input(
    "Quantity",
    min_value=1,
    step=1
)

price = st.number_input(
    "Trade Price (₹)",
    min_value=0.01,
    step=0.05
)

trade_date = st.date_input(
    "Trade Date",
    value=date.today()
)

if st.button("Submit Trade"):

    if not stock:

        st.error(
            "Please enter a stock symbol."
        )

    else:

        conn.execute("""
            INSERT INTO trades (
                stock,
                trade_type,
                quantity,
                price,
                trade_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            stock,
            trade_type,
            int(quantity),
            float(price),
            str(trade_date),
            "Pending"
        ))

        conn.commit()

        st.success(
            "Trade saved successfully!"
        )

        st.rerun()

st.divider()

# -------------------------------
# UPDATE TRADE STATUS
# -------------------------------

st.header("🔄 Update Trade Status")

if not trades.empty:

    trade_options = {}

    for _, row in trades.iterrows():

        label = (
            f"ID {row['Trade ID']} | "
            f"{row['Stock']} | "
            f"{row['Trade Type']} | "
            f"{row['Status']}"
        )

        trade_options[label] = int(
            row["Trade ID"]
        )

    selected_label = st.selectbox(
        "Select Trade",
        list(trade_options.keys())
    )

    selected_trade = trade_options[
        selected_label
    ]

    new_status = st.selectbox(
        "Select New Status",
        [
            "Pending",
            "Executed",
            "Settled",
            "Failed"
        ]
    )

    if st.button("Update Trade Status"):

        current_status = conn.execute(
            """
            SELECT status
            FROM trades
            WHERE trade_id = ?
            """,
            (selected_trade,)
        ).fetchone()

        if current_status is None:

            st.error(
                "Trade not found."
            )

        elif current_status[0] == new_status:

            st.warning(
                "The trade already has this status."
            )

        else:

            conn.execute(
                """
                UPDATE trades
                SET status = ?
                WHERE trade_id = ?
                """,
                (
                    new_status,
                    selected_trade
                )
            )

            conn.commit()

            st.success(
                "Trade status updated successfully!"
            )

            st.rerun()

else:

    st.info(
        "Enter a trade first to enable status updates."
    )

# -------------------------------
# CLOSE DATABASE CONNECTION
# -------------------------------

conn.close()

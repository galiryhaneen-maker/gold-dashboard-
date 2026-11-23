import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import time
from datetime import datetime

st.set_page_config(page_title="Gold Dashboard", layout="wide")
st.title("GOLD DASHBOARD - XAU/USD")

# --- DATA: CHART FROM STOOQ ---
def get_data(interval):
    mp = {"1m": "1", "5m": "5", "15m": "15", "30m": "30"}
    mp["1h"] = "60"
    mp["4h"] = "240"
    mp["1d"] = "d"
    mp["1wk"] = "w"
    mp["1mo"] = "m"
    stooq_i = mp.get(interval, "60")
    url = "https://stooq.com/q/d/l/?s=gc.f.us&i=" + stooq_i
    try:
        r = requests.get(url, timeout=10)
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})
        return df.tail(200)
    except:
        return None

def get_futures_price():
    try:
        url = "https://stooq.com/q/l/?s=gc.f.us&f=sd2t2ohlcv&h&e=csv"
        r = requests.get(url, timeout=8)
        df = pd.read_csv(io.StringIO(r.text))
        return float(df["Close"].iloc[0])
    except:
        return None

# --- DATA: EXNESS / SPOT PRICE ---
def get_exness_price():
    # المصدر 1: goldprice.org - سعر السبوت مثل Exness
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        r = requests.get(url, timeout=8)
        j = r.json()
        p = float(j["items"][0]["xauPrice"])
        return p
    except:
        pass
    # المصدر 2: gold-api - بديل
    try:
        url2 = "https://api.gold-api.com/price/XAU"
        r2 = requests.get(url2, timeout=8)
        p2 = float(r2.json()["price"])
        return p2
    except:
        return None

def heikin(df):
    ha = pd.DataFrame(index=df.index)
    ha["Close"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
    ha["Open"] = 0.0
    for i in range(len(df)):
        if i == 0:
            ha.iloc[i, ha.columns.get_loc("Open")] = df["Open"].iloc[0]
        else:
            ha.iloc[i, ha.columns.get_loc("Open")] = (ha["Open"].iloc[i-1] + ha["Close"].iloc[i-1]) / 2
    ha["High"] = ha[["Open", "Close"]].join(df["High"]).max(axis=1)
    ha["Low"] = ha[["Open", "Close"]].join(df["Low"]).min(axis=1)
    return ha

# --- UI: PRICES ---
fut = get_futures_price()
ex = get_exness_price()

colA, colB = st.columns(2)
colA.metric("Gold Futures (For Chart)", f"${fut:,.2f}" if fut else "Loading...")
colB.metric("Exness / Spot Price", f"${ex:,.2f}" if ex else "Loading...")

if ex and fut:
    diff = fut - ex
    st.caption(f"Spread Futures - Spot: ${diff:,.2f} - طبيعي، العقود الآجلة أغلى شوي من السبوت")

# --- UI: CHART ---
tf = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"], index=4)

with st.spinner("Loading chart..."):
    df = get_data(tf)

if df is None or df.empty:
    st.error("No data. Try Reboot or change timeframe.")
else:
    ha = heikin(df)
    ema_fast = df["Close"].ewm(span=9).mean().iloc[-1]
    ema_slow = df["Close"].ewm(span=21).mean().iloc[-1]
    last_close = df["Close"].iloc[-1]
    if ema_fast > ema_slow:
        sig = "🟢 BUY - Uptrend"
    elif ema_fast < ema_slow:
        sig = "🔴 SELL - Downtrend"
    else:
        sig = "🟡 NEUTRAL"
    c1, c2, c3 = st.columns(3)
    c1.metric("Close", f"${last_close:,.2f}")
    c2.metric("EMA 9", f"${ema_fast:,.2f}")
    c3.metric("Signal", sig)

    st.subheader(f"Chart - {tf} - Heikin Ashi Close")
    st.line_chart(ha["Close"])

   

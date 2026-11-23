import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import time
from datetime import datetime

st.set_page_config(page_title="Gold Dashboard", layout="wide")
st.title("GOLD DASHBOARD - XAU/USD")

# --- DATA: CHART FROM YAHOO CHART API (بدون مكتبة yfinance) ---
def get_data(interval):
    mp = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m"}
    mp["1h"] = "60m"
    mp["4h"] = "60m"
    mp["1d"] = "1d"
    mp["1wk"] = "1wk"
    mp["1mo"] = "1mo"
    yi = mp.get(interval, "60m")
    rng = "5d" if yi in ["1m", "5m", "15m", "30m", "60m"] else "1y"
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
    url += f"?interval={yi}&range={rng}"
    try:
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=h, timeout=10)
        j = r.json()["chart"]["result"][0]
        ts = j["timestamp"]
        q = j["indicators"]["quote"][0]
        df = pd.DataFrame({"Open": q["open"], "High": q["high"], "Low": q["low"], "Close": q["close"]}, index=pd.to_datetime(ts, unit="s"))
        df = df.dropna()
        if interval == "4h":
            df = df.resample("4h").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
        return df.tail(200)
    except:
        return None

def get_futures_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d"
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=h, timeout=8)
        j = r.json()["chart"]["result"][0]
        return float(j["meta"]["regularMarketPrice"])
    except:
        return None

# --- DATA: EXNESS / SPOT PRICE ---
def get_exness_price():
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        r = requests.get(url, timeout=8)
        j = r.json()
        p = float(j["items"][0]["xauPrice"])
        return p
    except:
        pass
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
    st.caption(f"Spread Futures - Spot: ${diff:,.2f}")

# --- UI: CHART ---
tf_list = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"]
tf = st.selectbox("Timeframe", tf_list, index=4)

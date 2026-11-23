import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Gold Pro", layout="wide")
st.title("🏆 شاشة الذهب Pro")
if st.button("🔄 حدث هلأ"):
    st.rerun()
auto = st.toggle("تحديث تلقائي", value=False)
if auto:
    time.sleep(60)
    st.rerun()
st.caption(f"اخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

st.sidebar.header("⚙️ الإعدادات")
timeframe = st.sidebar.selectbox("الفريم الرئيسي:", ["1m","5m","15m","30m","1h","4h","1d","1wk","1mo"], index=5)
capital = st.sidebar.number_input("راس مالك:", value=1000, step=100)
risk_pct = st.sidebar.slider("المخاطرة %:", 0.5, 5.0, 1.0)
period_map = {"1m":"1d","5m":"5d","15m":"5d","30m":"1mo","1h":"3mo","4h":"6mo","1d":"1y","1wk":"5y","1mo":"10y"}
interval_map = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"60m","1d":"1d","1wk":"1wk","1mo":"1mo"}

def get_data(interval, period):
    import io
    import requests
    import pandas as pd
    url = "https://stooq.com/q/d/l/"
    url += "?s=gc.f.us&i="
    url += interval
    try:
        r = requests.get(url, timeout=10)
        df = pd.read_csv(io.StringIO(r.text))
        df = df.rename(columns={"Date": "Date"})
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        df = df.rename(columns={"Open": "Open"})
        df = df.rename(columns={"High": "High"})
        df = df.rename(columns={"Low": "Low"})
        df = df.rename(columns={"Close": "Close"})
        return df.tail(200)
    except:
        return None

def get_live_price():
    import requests
    import re
    try:
        url = "https://www.google.com/finance/"
        url += "quote/COMEX:GCZ25"
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=h, timeout=8)
        m = re.search(r'"lastPrice[^0-9]*([0-9,]+\.[0-9]+)', r.text)
        if m:
            p = m.group(1).replace(",", "")
            return float(p)
    except:
        pass
    return None

def add_heikin(df):
    df = df.copy()
    for c in ['Open','High','Low','Close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().reset_index(drop=True)
    ha_close = []
    ha_open = []
    for i in range(len(df)):
        o = float(df['Open'].iloc[i])
        h = float(df['High'].iloc[i])
        l = float(df['Low'].iloc[i])
        c = float(df['Close'].iloc[i])
        hc = (o+h+l+c)/4
        ha_close.append(hc)
        if i == 0:
            ho = (o+c)/2
        else:
            ho = (ha_open[i-1]+ha_close[i-1])/2
        ha_open.append(ho)
    df['HA_Close'] = ha_close
    df['HA_Open'] = ha_open
    df['HA_High'] = df[['High','HA_Open','HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low','HA_Open','HA_Close']].min(axis=1)
    return df

def analyze_news(title):

    text = title.lower()
    score = 0
    reason = ""
    pos = {}
    pos["rate cut"] = 2
    pos["central bank buys"] = 2
    pos["safe haven"] = 2
    pos["gold rallies"] = 2
    pos["gold jumps"] = 2
    pos["gold surges"] = 2
    pos["war"] = 2
    pos["crisis"] = 2
    pos["recession"] = 1.5
    pos["dollar falls"] = 1.5
    pos["gold gains"] = 1.5
    pos["gold rises"] = 1.5
    pos["record high"] = 2
    neg = {}
    neg["rate hike"] = -2
    neg["hike bets"] = -2
    neg["hawkish"] = -2
    neg["gold slides"] = -2
    neg["gold falls"] = -2
    neg["gold drops"] = -2
    neg["selloff"] = -2
    neg["under pressure"] = -2
    neg["strong dollar"] = -1.5
    neg["dollar rises"] = -1
    neg["gold tumbles"] = -2
    neg["gold plunges"] = -2
    neg["profit-taking"] = -1.5
    for p,w in pos.items():
        if p in text:
            score += w
            reason += p + " "
    for p,w in neg.items():
        if p in text:
            score += w
            reason += p + " "
    if score == 0:
        if any(w in text for w in ["falls","drops","slides","losses","pressure","hurt","down"]):
            score = -1
            reason = "كلمة هبوط"
        elif any(w in text for w in ["rises","jumps","surges","gains","rebound","up"]):
            score = 1
            reason = "كلمة صعود"
        else:
            reason = "محايد"
    if score > 0.5:
        label = "ايجابي"
    elif score < -0.5:
        label = "سلبي"
    else:
        label = "محايد"
    return score, label, reason

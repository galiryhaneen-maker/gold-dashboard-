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
    if interval == "4h":
        df = yf.download("GC=F", interval="60m", period=period, progress=False, auto_adjust=True)
        if hasattr(df.columns, 'get_level_values'):
            try: df.columns = df.columns.get_level_values(0)
            except: pass
        df = df.reset_index()
        df = df.rename(columns={"Datetime":"Date","Open":"Open","High":"High","Low":"Low","Close":"Close"})
        df = df.set_index("Date").resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
        return df
    df = yf.download("GC=F", interval=interval, period=period, progress=False, auto_adjust=True)
    if hasattr(df.columns, 'get_level_values'):
        try: df.columns = df.columns.get_level_values(0)
        except: pass
    df = df.reset_index()
    date_col = [c for c in df.columns if "Date" in str(c) or "Datetime" in str(c)][0]
    df = df.rename(columns={date_col:"Date"})
    return df

def add_heikin(df):
    df = df.copy()
    for c in ['Open','High','Low','Close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().reset_index(drop=True)
    ha_close, ha_open = [], []
    for i in range(len(df)):
        o,h,l,c = float(df['Open'].iloc[i]), float(df['High'].iloc[i]), float(df['Low'].iloc[i]), float(df['Close'].iloc[i])
        hc = (o+h+l+c)/4
        ha_close.append(hc)
        ho = (o+c)/2 if i==0 else (ha_open[i-1]+ha_close[i-1])/2
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
    pos = {"rate cut":2,"central bank buys":2,"safe haven":2,"gold rallies":2,"gold jumps":2,"gold surges":2,"war":2,"crisis":2,"recession":1.5,"dollar falls":1.5,"gold gains":1.5,"gold rises":1.5}
    neg = {"rate hike":-2,"hike bets":-2,"hawkish":-2,"gold slides":-2,"gold falls":-2,"gold drops":-2,"selloff":-2,"slide deepens":-2,"under pressure":-2,"strong dollar":-1.5,"dollar rises":-1,"gold tumbles":-2,"gold plunges":-2}
    for p,w in pos.items():
        if p in text:
            score += w
            reason += f"'{p}' (+{w}) "
    for p,w in neg.items():
        if p in text:
            score += w
            reason += f"'{p}' ({w}) "
    if score == 0:
        if any(w in text for w in ["falls","drops","slides","losses","pressure","hurt"]):
            score = -1
            reason = "كلمة هبوط"
        elif any(w in text for w in ["rises","jumps","surges","gains","rebound"]):
            score = 1
            reason = "كلمة صعود"
        else:
            reason = "محايد"
    label = "ايجابي 🟢" if score > 0.5 else "سلبي 🔴" if score < -0.5 else "محايد ⚪"
    return score, label, reason.strip()

def analyze_tf(tf):
    try:
        df = add_heikin(get_data(interval_map[tf], period_map[tf]))
        if len(df) < 5:
            return None
        price = float(df['Close'].iloc[-1])
        df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
        atr_raw = float(df['TR'].rolling(14).mean().iloc[-1])
        if np.isnan(atr_raw) or atr_raw == 0:
            atr_raw = price * 0.002
        atr = min(atr_raw, price * 0.015)
        atr = max(atr, price * 0.0005)
        last = df.iloc[-1]
        trend, score = ("صاعد ✅",1) if last['HA_Close'] > last['HA_Open'] else ("هابط 🔻",-1)
        look = df.tail(50)
        resistance = float(look['High'].max())
        support = float

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
        df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={"Datetime":"Date"})
        df = df.set_index("Date").resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
        return df
    df = yf.download("GC=F", interval=interval, period=period, progress=False, auto_adjust=True)
    df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    date_col = [c for c in df.columns if "Date" in str(c)][0]
    df = df.rename(columns={date_col:"Date"})
    return df

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
    pos = {"rate cut":2,"central bank buys":2,"safe haven

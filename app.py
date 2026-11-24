import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.graph_objects as go
from datetime import datetime
st.set_page_config(page_title="Gold Pro", layout="wide")
PASSWORD = "gold2026"
if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.title("Gold Pro")
    pw = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("كلمة السر غلط")
    st.stop()
if st.button("تحديث", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
now_txt = datetime.now().strftime("%H:%M:%S")
st.write("اخر تحديث: " + now_txt)
st.title("Gold Pro - 3 جداول")
def get_news(url):
    feed = feedparser.parse(url)
    titles = []
    for e in feed.entries[:10]:
        titles.append(e.title.lower())
    return feed, titles
def score_titles(titles):
    pos_w = ["rise", "surge", "gain", "bullish", "rally", "jump", "rebound", "haven", "record"]
    neg_w = ["fall", "falls", "drop", "drops", "bearish", "decline", "crash", "plunge", "slump", "tumble"]
    p = 0
    n = 0
    for t in titles:
        tt = " " + t + " "
        is_p = False
        is_n = False
        for w in pos_w:
            if " " + w + " " in tt:
                is_p = True
        for w in neg_w:
            if " " + w + " " in tt:
                is_n = True
        if is_p and not is_n:
            p = p + 1
        if is_n and not is_p:
            n = n + 1
    return p, n
u_eco = "https://news.google.com/rss/search?q=gold+inflation+interest+dollar&hl=en&gl=US&ceid=US:en"
u_pol = "https://news.google.com/rss/search?q=gold+war+geopolitical+tension&hl=en&gl=US&ceid=US:en"
feed_eco, tit_eco = get_news(u_eco)
feed_pol, tit_pol = get_news(u_pol)
eco_pos, eco_neg = score_titles(tit_eco)
pol_pos, pol_neg = score_titles(tit_pol)
total_pos = eco_pos + pol_pos
total_neg = eco_neg + pol_neg
if total_pos > total_neg:
    news_score = "ايجابي"
elif total_neg > total_pos:
    news_score = "سلبي"
else:
    news_score = "محايد"
st.subheader("اخبار الذهب")
st.write("اقتصادية: ايجابي " + str(eco_pos) + " - سلبي " + str(eco_neg))
st.write("سياسية: ايجابي " + str(pol_pos) + " - سلبي " + str(pol_neg))
st.info("مجموع الاخبار: " + news_score)
st.subheader("حاسبة اللوت")
balance = st.number_input("رصيدك", value=1000, min_value=10)
risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
risk_money = balance * (risk_pct / 100)
@st.cache_data(ttl=60)
def analyze_tf(period, interval):
    df = yf.download("GC=F", period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    close = df["Close"]
    open_p = df["Open"]
    high = df["High"]
    low = df["Low"]
    last = float(close.iloc[-1])
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / loss))
    rsi_last = float(rsi.iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1])
    h1 = high - low
    h2 = (high - close.shift()).abs()
    h3 = (low - close.shift()).abs()
    tr = pd.concat([h1, h2, h3], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    c0_o = float(open_p.iloc[-1])
    c0_c = float(close.iloc[-1])
    c0_h = float(high.iloc[-1])
    c0_l = float(low.iloc[-1])
    c1_o = float(open_p.iloc[-2])
    c1_c = float(close.iloc[-2])
    body0 = abs(c0_c - c0_o)
    range0 = c0_h - c0_l
    up_wick = c0_h - max(c0_o, c0_c)
    low_wick = min(c0_o, c0_c) - c0_l
    pattern = "بدون نمط"
    pscore = 0
    if c1_c < c1_o and c0_c > c0_o and c0_c > c1_o and c0_o < c1_c:
        pattern = "ابتلاع صاعد"
        pscore = 2
    elif c1_c > c1_o and c0_c < c0_o and c0_c < c1_o and c0_o > c1_c:
        pattern = "ابتلاع هابط"
        pscore = -2
    elif low_wick > body0 * 2 and up_wick < body0 * 0.5:
        pattern = "مطرقة"
        pscore = 1.5
    elif up_wick > body0 * 2 and low_wick < body0 * 0.5:
        pattern = "شهاب"
        def show_table(title, frames):
    st.subheader(title)
    rows = []
    for name, per, inter in frames:
        r = analyze_tf(per, inter)
        rows.append({"الفريم": name, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["tp2"], 2), "هدف 3": round(r["tp3"], 2), "اللوت": r["lot"], "RSI": round(r["rsi"], 0), "سبب الدخول": r["reason"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
st.markdown("---")
if st.button("حساب جدول السكالبينج", use_container_width=True):
    st.session_state.show1 = True
if st.session_state.get("show1", False):
    show_table("جدول 1 - سكالبينج", [("1m", "1d", "1m"), ("5m", "1d", "5m"), ("15m", "5d", "15m")])
st.markdown("---")
if st.button("حساب جدول اليومي", use_container_width=True):
    st.session_state.show2 = True
if st.session_state.get("show2", False):
    show_table("جدول 2 - يومي", [("30m", "5d", "30m"), ("1h", "5d", "1h"), ("4h", "1mo", "1h")])
st.markdown("---")
if st.button("حساب جدول الطويل", use_container_width=True):
    st.session_state.show3 = True
if st.session_state.get("show3", False):
    show_table("جدول 3 - طويل", [("1d", "3mo", "1d"), ("1wk", "1y", "1wk"), ("1mo", "5y", "1mo")])
st.markdown("---")
st.subheader("شارت واحد")
timeframe = st.selectbox("اختار فريم", ["1m", "5m", "15m", "30m", "1h", "4h", "

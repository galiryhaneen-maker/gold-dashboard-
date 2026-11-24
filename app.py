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
st.title("Gold Pro - شموع + اخبار")

timeframe = st.selectbox(
    "الفريم",
    ["5m", "15m", "30m", "1h", "4h", "1d"],
    index=3
)
pmap = {}
pmap["5m"] = ("1d", "5m")
pmap["15m"] = ("5d", "15m")
pmap["30m"] = ("5d", "30m")
pmap["1h"] = ("5d", "1h")
pmap["4h"] = ("1mo", "1h")
pmap["1d"] = ("3mo", "1d")
period, interval = pmap[timeframe]

@st.cache_data(ttl=60)
def get_gold(period, interval):
    df = yf.download("GC=F", period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

df = get_gold(period, interval)
close = df["Close"]
open_p = df["Open"]
high = df["High"]
low = df["Low"]
last = float(close.iloc[-1])
prev = float(close.iloc[-2])
change = last - prev
pct = (change / prev) * 100

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

pattern = "لا يوجد نمط واضح"
pscore = 0
if c1_c < c1_o and c0_c > c0_o and c0_c > c1_o and c0_o < c1_c:
    pattern = "ابتلاع صاعد - قوي للشراء"
    pscore = 2
elif c1_c > c1_o and c0_c < c0_o and c0_c < c1_o and c0_o > c1_c:
    pattern = "ابتلاع هابط - قوي للبيع"
    pscore = -2
elif low_wick > body0 * 2 and up_wick < body0 * 0.5:
    pattern = "مطرقة - انعكاس صاعد"
    pscore = 1.5
elif up_wick > body0 * 2 and low_wick < body0 * 0.5:
    pattern = "شهاب - انعكاس هابط"
    pscore = -1.5
elif body0 < range0 * 0.1:
    pattern = "دوجي - تردد"
    pscore = 0

swing_low = float(low.tail(10).min())
swing_high = float(high.tail(10).max())
support = swing_low
resistance = swing_high

c1, c2, c3, c4 = st.columns(4)
c1.metric("سعر الذهب", str(round(last, 2)))
c2.metric("RSI", str(round(rsi_last, 0)))
c3.metric("ATR", str(round(atr, 2)))
c4.metric("النمط", pattern)

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=open_p,
    high=high,
    low=low,
    close=close
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=close.rolling(20).mean(),
    line=dict(color="orange", width=1),
    name="MA 20"
))
fig.update_layout(height=450)
fig.update_layout(xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
st.info("نمط الشموع: " + pattern)

st.subheader("اخبار الذهب - سياسية + اقتصادية")

def get_news(url):
    feed = feedparser.parse(url)
    titles = []
    for e in feed.entries[:10]:
        titles.append(e.title.lower())
    return feed, titles

def count_pos_neg(titles):
    pos_w = ["rise", "surge", "gain", "bullish", "rally", "jump", "rebound", "haven"]
    neg_w = ["fall", "drop", "bearish", "decline", "crash", "plunge", "slump"]
    p = 0
    n = 0
    for t in titles:
        tt = " " + t + " "
        for w in pos_w:
            if " " + w + " " in tt:
                p = p + 1
        for w in neg_w:
            if " " + w + " " in tt:
                n = n + 1
    return p, n

u_eco = "https://news.google.com/rss/search?q=gold+inflation+interest+dollar&hl=en&gl=US&ceid=US:en"
u_pol = "https://news.google.com/rss/search?q=gold+war+geopolitical+tension&hl=en&gl=US&ceid=US:en"
feed_eco, tit_eco = get_news(u_eco)
feed_pol, tit_pol = get_news(u_pol)
eco_pos, eco_neg = count_pos_neg(tit_eco)
pol_pos, pol_neg = count_pos_neg(tit_pol)

st.write("اخبار اقتصادية:")
if eco_pos > eco_neg:
    st.success("اقتصادي ايجابي للذهب")
elif eco_neg > eco_pos:
    st.error("اقتصادي سلبي للذهب")
else:
    st.warning("اقتصادي محايد")
for e in feed_eco.entries[:3]:
    st.write("- " + e.title)

st.write("اخبار سياسية:")
if pol_pos > pol_neg:
    st.success("سياسي ايجابي للذهب - ملاذ امن")
elif pol_neg > pol_pos:
    st.error("سياسي سلبي للذهب")
else:
    st.warning("سياسي محايد")
for e in feed_pol.entries[:3]:
    st.write("- " + e.title)

total_pos = eco_pos + pol_pos
total_neg = eco_neg + pol_neg
if total_pos > total_neg:
    news_score = "ايجابي"
elif total_neg > total_pos:
    news_score = "سلبي"
else:
    news_score = "محايد"
st.info("مجموع الاخبار: " + news_score)

st.subheader("حاسبة اللوت")
balance = st.number_input("رصيدك", value=1000, min_value=10)
risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
risk_money = balance * (risk_pct / 100)

score = pscore
if rsi_last < 30:
    score = score + 1.5
if rsi_last > 70:
    score = score - 1.5
if news_score == "ايجابي":
    score = score + 1
if news_score == "سلبي":
    score = score - 1
if last > ma20:
    score = score + 0.5
else:
    score = score - 0.5

st.subheader("اقتراح الصفقة")
if score >= 1:
    entry = last
    sl = swing_low - atr * 0.5
    sl_dist = abs(entry - sl)
    tp1 = entry + sl_dist * 1.5
    tp2 = entry + sl_dist * 2.5
    tp3 = entry + sl_dist * 4.0
    st.success("شراء BUY")
elif score <= -1:
    entry = last
    sl = swing_high + atr * 0.5
    sl_dist = abs(entry - sl)
    tp1 = entry - sl_dist * 1.5
    tp2 = entry - sl_dist * 2.5
    tp3 = entry - sl_dist * 4.0
    st.error("بيع SELL")
else:
    entry = last
    sl = swing_low - atr * 0.5
    sl_dist = abs(entry - sl)
    tp1 = entry + sl_dist * 1.0
    tp2 = entry + sl_dist * 2.0
    tp3 = entry + sl_dist * 3.0
    st.warning("انتظار")

lot_raw = risk_money / (sl_dist * 100)
lot = round(lot_raw, 2)
if lot < 0.01:
    lot = 0.01
profit1 = lot * abs(tp1 - entry) * 100

s1, s2, s3, s4, s5 = st.columns(5)
s1.metric("دخول", str(round(entry, 2)))
s2.metric("ستوب", str(round(sl, 2)))
s3.metric("هدف 1", str(round(tp1, 2)))
s4.metric("هدف 2", str(round(tp2, 2)))
s5.metric("هدف 3", str(round(tp3, 2)))

lot_txt = str(round(lot, 2))
risk_txt = str(round(risk_money, 2))
sl_txt = str(round(sl_dist, 2))
prof_txt = str(round(profit1, 2))
st.success("اللوت: " + lot_txt)
st.success("مخاطرة: " + risk_txt + " دولار")
st.success("مسافة الستوب: " + sl_txt)
st.success("ربح هدف 1: " + prof_txt + " دولار")
st.info("ستوب من الشموع + ATR")
st.caption("رصيد: " + str(balance))

if st.button("تحديث الصفحة", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

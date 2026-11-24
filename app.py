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

top1, top2 = st.columns([1, 4])
with top1:
    if st.button("تحديث 🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with top2:
    st.write(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

st.title("Gold Pro - تحليل الذهب - شموع + اخبار سياسية و اقتصادية")

timeframe = st.selectbox("الفريم", ["5m", "15m", "30m", "1h", "4h", "1d"], index=3)
period_map = {"5m": ("1d", "5m"), "15m": ("5d", "15m"), "30m": ("5d", "30m"), "1h": ("5d", "1h"), "4h": ("1mo", "1h"), "1d": ("3mo", "1d")}
period, interval = period_map[timeframe]

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

# RSI
delta = close.diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
rsi = 100 - (100 / (1 + gain / loss))
rsi_last = float(rsi.iloc[-1])
ma20 = float(close.rolling(20).mean().iloc[-1])

# ATR حقيقي
tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
atr = float(tr.rolling(14).mean().iloc[-1])

# ===== تحليل الشموع اليابانية - اخر 3 شموع =====
c0_o, c0_c, c0_h, c0_l = float(open_p.iloc[-1]), float(close.iloc[-1]), float(high.iloc[-1]), float(low.iloc[-1])
c1_o, c1_c, c1_h, c1_l = float(open_p.iloc[-2]), float(close.iloc[-2]), float(high.iloc[-2]), float(low.iloc[-2])
c2_o, c2_c = float(open_p.iloc[-3]), float(close.iloc[-3])

body0 = abs(c0_c - c0_o)
body1 = abs(c1_c - c1_o)
range0 = c0_h - c0_l
upper_wick0 = c0_h - max(c0_o, c0_c)
lower_wick0 = min(c0_o, c0_c) - c0_l

pattern = "لا يوجد نمط واضح"
pattern_score = 0
# ابتلاع صاعد
if c1_c < c1_o and c0_c > c0_o and c0_c > c1_o and c0_o < c1_c:
    pattern = "ابتلاع صاعد Bullish Engulfing - قوي للشراء"
    pattern_score = 2
# ابتلاع هابط
elif c1_c > c1_o and c0_c < c0_o and c0_c < c1_o and c0_o > c1_c:
    pattern = "ابتلاع هابط Bearish Engulfing - قوي للبيع"
    pattern_score = -2
# هامر
elif lower_wick0 > body0 * 2 and upper_wick0 < body0 * 0.5 and range0 > 0:
    pattern = "مطرقة Hammer - انعكاس صاعد"
    pattern_score = 1.5
# شوتينغ ستار
elif upper_wick0 > body0 * 2 and lower_wick0 < body0 * 0.5 and range0 > 0:
    pattern = "شهاب Shooting Star - انعكاس هابط"
    pattern_score = -1.5
# دوجي
elif body0 < range0 * 0.1 and range0 > 0:
    pattern = "دوجي Doji - تردد، انتظار"
    pattern_score = 0
# 3 شموع صاعدة
elif c0_c > c1_c > c2_c:
    pattern = "3 شموع صاعدة متتالية"
    pattern_score = 1
elif c0_c < c1_c < c2_c:
    pattern = "3 شموع هابطة متتالية"
    pattern_score = -1

# قاع وقمة حقيقيين من الشموع - اخر 10 شموع
swing_low = float(low.tail(10).min())
swing_high = float(high.tail(10).max())
support = swing_low
resistance = swing_high

c1, c2, c3, c4 = st.columns(4)
c1.metric("سعر الذهب", f"${last:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("RSI", f"{rsi_last:.0f}")
c3.metric("ATR", f"${atr:.2f}")
c4.metric("النمط", pattern.split(" - ")[0])

fig = go.Figure(data=[go.Candlestick(x=df.index, open=open_p, high=high, low=low, close=close)])
fig.add_trace(go.Scatter(x=df.index, y=close.rolling(20).mean(), line=dict(color="orange", width=1), name="MA 20"))
fig.update_layout(height=450, xaxis_rangeslider_visible=False, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)
st.info(f"نمط الشموع: {pattern} | القاع الحقيقي: ${swing_low:,.2f} | القمة الحقيقية: ${swing_high:,.2f}")

# ===== اخبار الذهب - سياسية و اقتصادية =====
st.subheader("تحليل الاخبار - سياسية + اقتصادية - ذهب فقط")

def analyze_feed(url, label):
    feed = feedparser.parse(url)
    titles = [e.title.lower() for e in feed.entries[:10]]
    def cnt(word, titles):
        n = 0
        for t in titles:
            if f" {word} " in f" {t} ":
                n += 1
        return n
    pos_words = ["rise", "surge", "gain", "bullish", "record", "rally", "jump", "rebound", "safe", "haven"]
    neg_words = ["fall", "drop", "bearish", "decline", "crash", "plunge", "slump", "selloff"]
    pos = sum(cnt(w, titles) for w in pos_words)
    neg = sum(cnt(w, titles) for w in neg_words)
    return feed, pos, neg

# اخبار اقتصادية - فائدة، تضخم، دولار
feed_eco, eco_pos, eco_neg = analyze_feed("https://news.google.com/rss/search?q=gold+price+inflation+interest+rate+dollar&hl=en&gl=US&ceid=US:en", "eco")
# اخبار سياسية - حرب، توتر، انتخابات
feed_pol, pol_pos, pol_neg = analyze_feed("https://news.google.com/rss/search?q=gold+war+geopolitical+tension+political&hl=en&gl=US&ceid=US:en", "pol")

st.write("**اخبار اقتصادية (فائدة - تضخم - دولار):**")
if eco_pos > eco_neg:
    st.success(f"اقتصادي: ايجابي للذهب | ايجابي {eco_pos} - سلبي {eco_neg}")
elif eco_neg > eco_pos:
    st.error(f"اقتصادي: سلبي للذهب | ايجابي {eco_pos} - سلبي {eco_neg}")
else:
    st.warning(f"اقتصادي: محايد | ايجابي {eco_pos} - سلبي {eco_neg}")
for e in feed_eco.entries[:3]:
    st.write(f"- {e.title}")

st.write("**اخبار سياسية (حرب - توتر - انتخابات):**")
if pol_pos > pol_neg:
    st.success(f"سياسي: ايجابي للذهب - ملاذ آمن | ايجابي {pol_pos} - سلبي {pol_neg}")
elif pol_neg > pol_pos:
    st.error(f"سياسي: سلبي للذهب | ايجابي {pol_pos} - سلبي {pol_neg}")
else:
    st.warning(f"سياسي: محايد | ايجابي {pol_pos} - سلبي {pol_neg}")
for e in feed_pol.entries[:3]:
    st.write(f"- {e.title}")

# النتيجة النهائية للاخبار
total_pos = eco_pos + pol_pos
total_neg = eco_neg + pol_neg
if total_pos > total_neg:
    news_score = "ايجابي"
elif total_neg > total_pos:
    news_score = "سلبي"
else:
    news_score = "محايد"
st.info(f"مجموع الاخبار: ايجابي {total_pos} - سلبي {total_neg} = {news_score}")

# ===== حاسبة اللوت اولا - مشان الستوب ينحسب عليها =====
st.subheader("حاسبة اللوت و مبلغ التداول")
lc1, lc2 = st.columns(2)
with lc1:
    balance = st.number_input("رصيدك $", value=1000, min_value=10, key="bal")
with lc2:
    risk_pct = st.slider("مخاطرة % من رصيدك", 0.5, 5.0, 1.0, key="risk")
risk_money = balance * (risk_pct / 100)

# ===== قرار الصفقة من الشموع + الاخبار + RSI =====
score = pattern_score
if rsi_last < 30:
    score += 1.5
elif rsi_last > 70:
    score -= 1.5
if news_score == "ايجابي":
    score += 1
elif news_score == "سلبي":
    score -= 1
if last > ma20:
    score += 0.5
else:
    score -= 0.5

st.subheader("اقتراح الصفقة - محسوب من الشموع + ATR + اللوت")

if score >= 1:
    direction = "BUY"
    # الستوب: تحت القاع الحقيقي + ATR * 0.5 - واقعي من الشموع
    sl = swing_low - atr * 0.5
    # اذا الستوب بعيد كتير على رصيدك، قربو شوي مشان اللوت يظبط
    sl_dist_raw = last - sl
    max_sl = (risk_money / 0.01 / 100) if risk_money > 0 else sl_dist_raw
    if sl_dist_raw > max_sl and max_sl > 5:
        sl = last - max_sl
    entry = last
    sl_dist = abs(entry - sl)
    tp1 = entry + sl_dist * 1.5
    tp2 = entry + sl_dist * 2.5
    tp3 = entry + sl_dist * 4.0
    st.success(f"شراء BUY - السبب: {pattern} + RSI {rsi_last:.0f} + اخبار {news_score}")
elif score <= -1:
    direction = "SELL"
    sl = swing_high + atr * 0.5
    sl_dist_raw = sl - last
    max_sl = (risk_money / 0.01 / 100) if risk_money > 0 else sl_dist_raw
    if sl_dist_raw > max_sl and max_sl > 5:
        sl = last + max_sl
    entry = last
    sl_dist = abs(entry - sl)
    tp1 = entry - sl_dist * 1.5
    tp2 = entry - sl_dist * 2.5
    tp3 = entry - sl_dist * 4.0
    st.error(f"بيع SELL - السبب: {pattern} + RSI {rsi_last:.0f} + اخبار {news_score}")
else:
    direction = "WAIT"
    entry = last
    sl = swing_low - atr * 0.5
    sl_dist = abs(entry - sl)
    tp1 = entry + sl_dist * 1.0
    tp2 = entry + sl_dist * 2.0
    tp3 = entry + sl_dist * 3.0
    st.warning(f"انتظار - السوق متذبذب | نمط: {pattern} | RSI: {rsi_last:.0f} | اخبار: {news_score}")

# اللوت محسوب من الستوب الحقيقي
lot_raw = risk_money / (sl_dist * 100) if sl_dist > 0 else 0
lot = round(lot_raw, 2)
if lot < 0.01:
    lot = 0.01

sc1, sc2, sc3, sc4, sc5 = st.columns(5)
sc1.metric("سعر الدخول", f"${entry:,.2f}")
sc2.metric("وقف الخسارة (ATR + شموع)", f"${sl:,.2f}")
sc3.metric("هدف 1", f"${tp1:,.2f}")
sc4.metric("هدف 2", f"${tp2:,.2f}")
sc5.metric("هدف 3", f"${tp3:,.2f}")

st.success(f"اللوت المناسب لحسابك: {lot:.2f} | مخاطرة: ${risk_money:.2f

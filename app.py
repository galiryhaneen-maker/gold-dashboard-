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

# ===== زر التحديث =====
top1, top2 = st.columns([1, 4])
with top1:
    if st.button("تحديث 🔄", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with top2:
    st.write(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

st.title("Gold Pro - تحليل الذهب الحي")
timeframe = st.selectbox("الفريم", ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"], index=6)
period_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "30m": ("5d", "30m"), "1h": ("5d", "1h"), "4h": ("1mo", "1h"), "1d": ("3mo", "1d"), "1wk": ("1y", "1wk"), "1mo": ("5y", "1mo")}
period, interval = period_map[timeframe]

@st.cache_data(ttl=60)
def get_gold(period, interval):
    df = yf.download("GC=F", period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

df = get_gold(period, interval)
close = df["Close"]
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
ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) > 50 else ma20

c1, c2, c3, c4 = st.columns(4)
c1.metric("سعر الذهب", f"${last:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("RSI", f"{rsi_last:.0f}")
c3.metric("اعلى", f"${float(df['High'].iloc[-1]):,.2f}")
c4.metric("ادنى", f"${float(df['Low'].iloc[-1]):,.2f}")

fig = go.Figure(data=[go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"])])
fig.add_trace(go.Scatter(x=df.index, y=close.rolling(20).mean(), line=dict(color="orange", width=1), name="MA 20"))
fig.add_trace(go.Scatter(x=df.index, y=close.rolling(50).mean(), line=dict(color="blue", width=1), name="MA 50"))
fig.update_layout(height=450, xaxis_rangeslider_visible=False, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

support = float(df["Low"].tail(30).min())
resistance = float(df["High"].tail(30).max())
risk_range = abs(last - support) if last > support else abs(resistance - last)
if risk_range < 5:
    risk_range = 15

st.subheader("تقييم الاخبار")
feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
news_text = " ".join([e.title for e in feed.entries[:8]])
pos_words = ["rise", "surge", "gain", "bullish", "record", "up", "higher", "strong", "rally"]
neg_words = ["fall", "drop", "bearish", "down", "lower", "weak", "decline", "crash"]
pos = sum(1 for w in pos_words if w.lower() in news_text.lower())
neg = sum(1 for w in neg_words if w.lower() in news_text.lower())
if pos > neg:
    news_score = "ايجابي"
    st.success(f"الاخبار: ايجابي - داعم للصعود | ايجابي {pos} - سلبي {neg}")
elif neg > pos:
    news_score = "سلبي"
    st.error(f"الاخبار: سلبي - داعم للهبوط | ايجابي {pos} - سلبي {neg}")
else:
    news_score = "محايد"
    st.warning(f"الاخبار: محايد | ايجابي {pos} - سلبي {neg}")
for e in feed.entries[:5]:
    st.write(f"- {e.title}")

st.subheader("اقتراح الصفقة - سعر الدخول / وقف الخسارة / سحب الارباح")
is_buy = (last > ma20 and rsi_last < 70) or (news_score == "ايجابي" and last > ma20)
is_sell = (last < ma20 and rsi_last > 30) or (news_score == "سلبي" and last < ma20)
if is_buy:
    entry = last
    sl = support
    tp1 = last + risk_range * 1.0
    tp2 = last + risk_range * 2.0
    tp3 = resistance if resistance > last else last + risk_range * 3.0
    st.success("شراء BUY - الدخول الان")
elif is_sell:
    entry = last
    sl = resistance
    tp1 = last - risk_range * 1.0
    tp2 = last - risk_range * 2.0
    tp3 = support if support < last else last - risk_range * 3.0
    st.error("بيع SELL - الدخول الان")
else:
    entry = last
    sl = support
    tp1 = last + risk_range * 0.5
    tp2 = resistance
    tp3 = resistance + risk_range
    st.warning("انتظار - لا تدخل هلأ، السوق متذبذب")

sc1, sc2, sc3, sc4, sc5 = st.columns(5)
sc1.metric("سعر الدخول", f"${entry:,.2f}")
sc2.metric("وقف الخسارة", f"${sl:,.2f}")
sc3.metric("سحب ارباح 1", f"${tp1:,.2f}")
sc4.metric("سحب ارباح 2", f"${tp2:,.2f}")
sc5.metric("سحب ارباح 3", f"${tp3:,.2f}")
st.info(f"الدعم: ${support:,.2f} | المقاومة: ${resistance:,.2f} | MA20: ${ma20:,.2f}")

st.subheader("حاسبة اللوت")
lc1, lc2, lc3 = st.columns(3)
with lc1:
    balance = st.number_input("رصيدك $", value=1000, min_value=10)
with lc2:
    risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
with lc3:
    sl_dist = st.number_input("مسافة الستوب $", value=abs(entry - sl) if abs(entry - sl) > 1 else 15.0, min_value=0.5)
risk_money = balance * (risk_pct / 100)
lot = risk_money / (sl_dist * 100) if sl_dist > 0 else 0
st.info(f"اللوت: {lot:.2f} | رح تخسر اذا ضرب ستوب: ${risk_money:.2f} | الربح المتوقع عند هدف 1: ${lot * abs(tp1 - entry) * 100:,.2f}")

# زر تحديث تحت كمان مشان ما تطلع لفوق
if st.button("تحديث الصفحة 🔄", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

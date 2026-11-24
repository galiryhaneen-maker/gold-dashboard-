import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.graph_objects as go

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

st.title("Gold Pro - تحليل الذهب الحي")

# ===== الفريمات من دقيقة لشهر =====
timeframe = st.selectbox("الفريم", ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"], index=6)
period_map = {
    "1m": ("1d", "1m"),
    "5m": ("1d", "5m"),
    "15m": ("5d", "15m"),
    "30m": ("5d", "30m"),
    "1h": ("5d", "1h"),
    "4h": ("1mo", "1h"),
    "1d": ("3mo", "1d"),
    "1wk": ("1y", "1wk"),
    "1mo": ("5y", "1mo"),
}
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

# ===== الدعم والمقاومة =====
support = float(df["Low"].tail(30).min())
resistance = float(df["High"].tail(30).max())
risk_range = abs(last - support) if last > support else abs(resistance - last)
if risk_range < 5:
    risk_range = 15

# ===== تقييم الاخبار =====
st.subheader("تقييم الاخبار")
try:
    feed = feedparser.parse("https://www.investing.com/rss/news_285.rss")
    news_text = " ".join([e.title for e in feed.entries[:8]])
    pos_words = ["rise", "surge", "gain", "bullish", "record", "up", "higher", "strong", "rally", "ارتفاع", "صعود"]
    neg_words = ["fall", "drop", "bearish", "down", "lower", "weak", "decline", "crash", "انخفاض", "هبوط"]
    pos = sum(1 for w in pos_words if w.lower() in news_text.lower())
    neg = sum(1 for w in neg_words if w.lower() in news_text.lower())
    if pos > neg:
        news_score = "ايجابي - داعم للصعود"
        st.success(f"الاخبار: {news_score} | ايجابي {pos} - سلبي {neg}")
    elif neg > pos:
        news_score = "سلبي - داعم للهبوط"
        st.error(f"الاخبار: {news_score} | ايجابي {pos} - سلبي {neg}")
    else:
        news_score = "محايد"
        st.warning(f"الاخبار: محايد | ايجابي {pos} - سلبي {neg}")
    for e in feed.entries[:5]:
        st.write

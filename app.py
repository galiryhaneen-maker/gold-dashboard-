import streamlit as st
import pandas as pd
import yfinance as yf
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
timeframe = st.selectbox("الفريم", ["15m", "1h", "4h", "1d"], index=3)
period_map = {"15m": ("1d", "15m"), "1h": ("5d", "1h"), "4h": ("1mo", "1h"), "1d": ("3mo", "1d")}
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

c1, c2, c3, c4 = st.columns(4)
c1.metric("سعر الذهب", f"${last:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("RSI", f"{rsi_last:.0f}")
c3.metric("اعلى", f"${float(df['High'].iloc[-1]):,.2f}")
c4.metric("ادنى", f"${float(df['Low'].iloc[-1]):,.2f}")

fig = go.Figure(data=[go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"])])
fig.add_trace(go.Scatter(x=df.index, y=close.rolling(20).mean(), line=dict(color="orange", width=1), name="MA 20"))
fig.update_layout(height=450, xaxis_rangeslider_visible=False, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

support = float(df["Low"].tail(20).min())
resistance = float(df["High"].tail(20).max())
ma20 = float(close.rolling(20).mean().iloc[-1])

st.subheader("اشارة الصفقة")
if last > ma20 and rsi_last < 70:
    signal = "شراء BUY"
    entry = last
    sl = support
    tp1 = last + (last - support) * 1.5
    tp2 = resistance
    st.success(signal)
elif last < ma20 and rsi_last > 30:
    signal = "بيع SELL"
    entry = last
    sl = resistance
    tp1 = last - (resistance - last) * 1.5
    tp2 = support
    st.error(signal)
else:
    signal = "انتظار"
    entry = last
    sl = support
    tp1 = resistance
    tp2 = resistance
    st.warning(signal)

sc1, sc2, sc3, sc4 = st.columns(4)
sc1.metric("الدخول", f"${entry:,.2f}")
sc2.metric("ستوب", f"${sl:,.2f}")
sc3.metric("هدف 1", f"${tp1:,.2f}")
sc4.metric("هدف 2", f"${tp2:,.2f}")

st.subheader("حاسبة اللوت")
lc1, lc2, lc3 = st.columns(3)
with lc1:
    balance = st.number_input("رصيدك $", value=1000, min_value=10)
with lc2:
    risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
with lc3:
    sl_pips = st.number_input("الستوب $", value=abs(entry - sl), min_value=0.1)
risk_money = balance * (risk_pct / 100)
lot = risk_money / (sl_pips * 100) if sl_pips > 0 else 0
st.info(f"اللوت: {lot:.2f} | رح تخسر اذا ضرب ستوب: ${risk_money:.2f}")

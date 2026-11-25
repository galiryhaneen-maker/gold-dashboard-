import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Gold Pro", layout="wide", page_icon="🥇")

# ===== ستايل احترافي =====
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
div[data-testid="stMetric"] { background: white; border-radius: 12px; padding: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
button { border-radius: 12px !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

PASSWORD = "gold2026"
if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.title("🥇 Gold Pro")
    pw = st.text_input("كلمة السر", type="password")
    if st.button("دخول", use_container_width=True):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("كلمة السر غلط")
    st.stop()

if st.button("🔄 تحديث", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.caption("اخر تحديث: " + datetime.now().strftime("%H:%M:%S"))

# ===== السعر اللحظي - مع بديل =====
def get_gold_price():
    # مصدر 1: goldprice.org
    try:
        r = requests.get("https://data-asg.goldprice.org/db/XAUUSD.json", timeout=5).json()
        return r["items"][0]["curr"], r["items"][0]["chg"]
    except:
        pass
    # مصدر 2: yfinance GC=F - بديل مضمون
    try:
        d = yf.download("GC=F", period="1d", interval="1m", progress=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        d = d.dropna()
        last = float(d["Close"].iloc[-1])
        prev = float(d["Close"].iloc[-2])
        return last, last - prev
    except:
        return None, None

price, change = get_gold_price()

st.title("🥇 Gold Pro - تحليل الذهب الذكي")
if price:
    color = "#00c853" if change >= 0 else "#ff1744"
    bg = "#e8fdf0" if change >= 0 else "#ffebee"
    border = "#00c853" if change >= 0 else "#ff1744"
    arrow = "▲" if change >= 0 else "▼"
    st.markdown(f"""
    <div style="background:{bg}; border:2px solid {border}; border-radius:15px; padding:14px; text-align:center; margin-bottom:10px;">
        <div style="font-size:13px; color:#555;">سعر الذهب اللحظي - XAU/USD LIVE</div>
        <div style="font-size:30px; font-weight:bold; line-height:1.1;">${price:,.2f}</div>
        <div style="color:{color}; font-weight:bold; font-size:16px;">{arrow} {change:.2f} $</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("ما قدرنا نجيب السعر اللحظي - جرب تحديث")

# ===== الأخبار =====
def get_news(url):
    feed = feedparser.parse(url)
    return feed, [e.title.lower() for e in feed.entries[:10]]

def score_titles(titles):
    pos_w = ["rise", "surge", "gain", "bullish", "rally", "jump", "rebound", "haven", "record"]
    neg_w = ["fall", "falls", "drop", "drops", "bearish", "decline", "crash", "plunge", "slump", "tumble"]
    p = sum(1 for t in titles if any(" " + w + " " in " " + t + " " for w in pos_w) and not any(" " + w + " " in " " + t + " " for w in neg_w))
    n = sum(1 for t in titles if any(" " + w + " " in " " + t + " " for w in neg_w) and not any(" " + w + " " in " " + t + " " for w in pos_w))
    return p, n

feed_eco, tit_eco = get_news("https://news.google.com/rss/search?q=gold+inflation+interest+dollar&hl=en&gl=US&ceid=US:en")
feed_pol, tit_pol = get_news("https://news.google.com/rss/search?q=gold+war+geopolitical+tension&hl=en&gl=US&ceid=US:en")
eco_pos, eco_neg = score_titles(tit_eco)
pol_pos, pol_neg = score_titles(tit_pol)
total_pos = eco_pos + pol_pos
total_neg = eco_neg + pol_neg
news_score = "ايجابي" if total_pos > total_neg else "سلبي" if total_neg > total_pos else "محايد"

st.subheader("📰 اخبار الذهب")
c_eco, c_pol = st.columns(2)
c_eco.metric("اقتصادية - ايجابي", eco_pos, delta=f"-{eco_neg} سلبي")
c_pol.metric("سياسية - ايجابي", pol_pos, delta=f"-{pol_neg} سلبي")
if news_score == "ايجابي":
    st.success(f"مجموع الاخبار: {news_score} - تدعم الصعود 🟢")
elif news_score == "سلبي":
    st.error(f"مجموع الاخبار: {news_score} - تدعم الهبوط 🔴")
else:
    st.info(f"مجموع الاخبار: {news_score} - محايدة ⚪")

# ===== حاسبة اللوت =====
st.subheader("⚖️ حاسبة اللوت")
balance = st.number_input("رصيدك $", value=1000, min_value=10)
risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
risk_money = balance * (risk_pct / 100)
st.caption(f"رح تخاطر بـ {risk_money:.2f} $ بهاي الصفقة")

@st.cache_data(ttl=60)
def analyze_tf(per, inter, news_score_val, risk_money_val):
    df = yf.download("GC=F", period=per, interval=inter, progress=False)
    df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns
    df = df.dropna()
    close = df["Close"]; open_p = df["Open"]; high = df["High"]; low = df["Low"]
    last = float(close.iloc[-1])
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi_last = float((100 - (100 / (1 + gain / loss))).iloc[-1])
    ma20 = float(close.rolling(20).mean().iloc[-1])
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    c0_o = float(open_p.iloc[-1]); c0_c = float(close.iloc[-1]); c0_h = float(high.iloc[-1]); c0_l = float(low.iloc[-1])
    c1_o = float(open_p.iloc[-2]); c1_c = float(close.iloc[-2])
    body0 = abs(c0_c - c0_o); range0 = c0_h - c0_l
    up_wick = c0_h - max(c0_o, c0_c); low_wick = min(c0_o, c0_c) - c0_l
    pattern = "ابتلاع صاعد" if (c1_c < c1_o and c0_c > c0_o and c0_c > c1_o and c0_o < c1_c) else "ابتلاع هابط" if (c1_c > c1_o and c0_c < c0_o and c0_c < c1_o and c0_o > c1_c) else "مطرقة" if (low_wick > body0 * 2 and up_wick < body0 * 0.5) else "شهاب" if (up_wick > body0 * 2 and low_wick < body0 * 0.5) else "دوجي" if (body0 < range0 * 0.1) else "بدون نمط"
    pscore = 2 if pattern == "ابتلاع صاعد" else -2 if pattern == "ابتلاع هابط" else 1.5 if pattern == "مطرقة" else -1.5 if pattern == "شهاب" else 0
    swing_low = float(low.tail(10).min()); swing_high = float(high.tail(10).max())
    score = pscore + (1.5 if rsi_last < 30 else -1.5 if rsi_last > 70 else 0) + (1 if news_score_val == "ايجابي" else -1 if news_score_val == "سلبي" else 0) + (0.5 if last > ma20 else -0.5)
    direction = "شراء BUY" if score >= 1 else "بيع SELL" if score <= -1 else "انتظار WAIT"
    sl = (swing_low - atr * 0.5) if direction == "شراء BUY" else (swing_high + atr * 0.5) if direction == "بيع SELL" else (swing_low - atr * 0.5)
    sl_dist = abs(last - sl)
    tp1 = (last + sl_dist * 1.5) if direction == "شراء BUY" else (last - sl_dist * 1.5) if direction == "بيع SELL" else (last + sl_dist * 1.0)
    tp2 = (last + sl_dist * 2.5) if direction == "شراء BUY" else (last - sl_dist * 2.5) if direction == "بيع SELL" else (last + sl_dist * 2.0)
    tp3 = (last + sl_dist * 4.0) if direction == "شراء BUY" else (last - sl_dist * 4.0) if direction == "بيع SELL" else (last + sl_dist * 3.0)
    reason_txt = ((pattern + " + ") if pattern != "بدون نمط" else "") + ("RSI تشبع بيع + " if rsi_last < 30 else "RSI تشبع شراء + " if rsi_last > 70 else "RSI متوازن + ") + ("اخبار ايجابية + " if news_score_val == "ايجابي" else "اخبار سلبية + " if news_score_val == "سلبي" else "اخبار محايدة + ") + ("فوق MA20" if last > ma20 else "تحت MA20")
    if direction == "انتظار WAIT":
        reason_txt += " = لا توافق"
    lot = max(round(risk_money_val / (sl_dist * 100), 2), 0.01) if sl_dist > 0 else 0.01
    return {"last": last, "rsi": rsi_last, "atr": atr, "pattern": pattern, "direction": direction, "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "lot": lot, "reason": reason_txt, "df": df, "score": score}

# ===== الإشارة الأوتوماتيك - مع اختيار الفريم =====
st.subheader("🎯 الإشارة الأوتوماتيك")
sig_tf_choice = st.selectbox("اختار فريم الإشارة الأوتوماتيك", ["15m", "30m", "1h", "4h", "1d"], index=2, key="sig_tf")
sig_map = {"15m": ("5d", "15m"), "30m": ("5d", "30m"), "1h": ("5d", "1h"), "4h": ("1mo", "1h"), "1d": ("3mo", "1d")}
sig_p, sig_i = sig_map[sig_tf_choice]
sig_h1 = analyze_tf(sig_p, sig_i, news_score, risk_money)

if sig_h1["direction"] != "انتظار WAIT":
    is_buy = sig_h1["direction"] == "شراء BUY"
    bg = "#e8fdf0" if is_buy else "#ffebee"
    border = "#00c853" if is_buy else "#ff1744"
    label = "شراء BUY ▲" if is_buy else "بيع SELL ▼"
    st.markdown(f"""
    <div style="background:{bg}; border:2px solid {border}; border-radius:15px; padding:15px;">
        <div style="display:flex; justify-content:space-between; align-items:center;"><b style="font-size:20px;">{label}</b><b>فريم {sig_tf_choice} • لوت {sig_h1['lot']}</b></div>
        <div style="margin-top:10px; font-size:14px;">🕯️ {sig_h1['pattern']} | 📰 أخبار {news_score} | RSI {sig_h1['rsi']:.0f}<br>{sig_h1['reason']}</div>
        <div style="display:flex; gap:8px; margin-top:12px; text-align:center; flex-wrap:wrap;">
            <div style="flex:1; min-width:70px; background:white; border-radius:10px; padding:8px;"><div style="font-size:11px;">دخول</div><b>{sig_h1['last']:,.2f}</b></div>
            <div style="flex:1; min-width:70px; background:white; border-radius:10px; padding:8px;"><div style="font-size:11px; color:red;">وقف</div><b>{sig_h1['sl']:,.2f}</b></div>
            <div style="flex:1; min-width:70px; background:white; border-radius:10px; padding:8px;"><div style="font-size:11px; color:green;">هدف 1</div><b>{sig_h1['tp1']:,.2f}</b></div>
            <div style="flex:1; min-width:70px; background:white; border-radius:10px; padding:8px;"><div style="font-size:11px; color:green;">هدف 2</div><b>{sig_h1['tp2']:,.2f}</b></div>
            <div style="flex:1; min-width:70px; background:white; border-radius:10px; padding:8px;"><div style="font-size:11px; color:green;">هدف 3</div><b>{sig_h1['tp3']:,.2f}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info(f"⏳ لا توجد صفقة الآن على {sig_tf_choice} - {sig_h1['pattern']} | أخبار {news_score} | {sig_h1['reason']}")

# ===== الجداول =====
st.subheader("📊 الجداول")
if st.button("حساب جدول السكالبينج", use_container_width=True):
    st.session_state.show1 = True
if st.session_state.get("show1", False):
    st.markdown("**جدول 1 - سكالبينج**")
    d = [analyze_tf(p, i, news_score, risk_money) for n, p, i in [("1m", "1d", "1m"), ("5m", "1d", "5m"), ("15m", "5d", "15m")]]
    rows = [{"الفريم": n, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["tp2"], 2), "هدف 3": round(r["tp3"], 2), "اللوت": r["lot"], "RSI": round(r["rsi"], 0), "سبب الدخول": r["reason"]} for (n, p, i), r in zip([("1m", "1d", "1m"), ("5m", "1d", "5m"), ("15m", "5d", "15m")], d)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if st.button("حساب جدول اليومي", use_container_width=True):
    st.session_state.show2 = True
if st.session_state.get("show2", False):
    st.markdown("**جدول 2 - يومي**")
    d = [analyze_tf(p, i, news_score, risk_money) for n, p, i in [("30m", "5d", "30m"), ("1h", "5d", "1h"), ("4h", "1mo", "1h")]]
    rows = [{"الفريم": n, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["tp2"], 2), "هدف 3": round(r["tp3"], 2), "اللوت": r["lot"], "RSI": round(r["rsi"], 0), "سبب الدخول": r["reason"]} for (n, p, i), r in zip([("30m", "5d", "30m"), ("1h", "5d", "1h"), ("4h", "1mo", "1h")], d)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

if st.button("حساب جدول الطويل", use_container_width=True):
    st.session_state.show3 = True
if st.session_state.get("show3", False):
    st.markdown("**جدول 3 - طويل**")
    d = [analyze_tf(p, i, news_score, risk_money) for n, p, i in [("1d", "3mo", "1d"), ("1wk", "1y", "1wk"), ("1mo", "5y", "1mo")]]
    rows = [[n, r["direction"], round(r["last"], 2), round(r["sl"], 2), round(r["tp1"], 2), round(r["tp2"], 2), round(r["tp3"], 2), r["lot"], round(r["rsi"], 0), r["reason"]] for (n, p, i), r in zip([("1d", "3mo", "1d"), ("1wk", "1y", "1wk"), ("1mo", "5y", "1mo")], d)]
    st.dataframe(pd.DataFrame(rows, columns=["الفريم", "الاتجاه", "السعر", "الستوب", "هدف 1", "هدف 2", "هدف 3", "اللوت", "RSI", "سبب الدخول"]), use_container_width=True, hide_index=True)

# ===== الشارت =====
st.subheader("📈 الشارت - الشموع اليابانية")
tf_choice = st.selectbox("اختار فريم الشارت", ["1m", "5m", "15m", "1h", "4h", "1d"], index=3, key="chart_tf")
tf_map = {"1m": ("1d", "1m"), "5m": ("1d", "5m"), "15m": ("5d", "15m"), "1h": ("5d", "1h"), "4h": ("1mo", "1h"), "1d": ("3mo", "1d")}
tf_p, tf_i = tf_map[tf_choice]
chart_res = analyze_tf(tf_p, tf_i, news_score, risk_money)
chart_data = chart_res["df"]
close_c = chart_data["Close"].astype(float)
delta_c = close_c.diff()
gain_c = delta_c.where(delta_c > 0, 0).rolling(14).mean()
loss_c = -delta_c.where(delta_c < 0, 0).rolling(14).mean()
rs_c = gain_c / loss_c.replace(0, 0.00001)
rsi_v = float(100 - (100 / (1 + rs_c.iloc[-1])))
ema12_c = close_c.ewm(span=12).mean()
ema26_c = close_c.ewm(span=26).mean()
macd_v = float(ema12_c.iloc[-1] - ema26_c.iloc[-1])
sig_v = float((ema12_c - ema26_c).ewm(span=9).mean().iloc[-1])
rsi_txt = "مشبع شراء - لا تشتري" if rsi_v > 70 else "مشبع بيع - فرصة شراء" if rsi_v < 30 else "عادي"
macd_txt = "صاعد" if macd_v > sig_v else "هابط"
st.warning(f"RSI: {rsi_v:.1f} - {rsi_txt} | MACD: {macd_v:.2f} - {macd_txt} | اتجاه {tf_choice}: {chart_res['direction']}")
fig = go.Figure(data=[go.Candlestick(x=chart_data.index, open=chart_data["Open"], high=chart_data["High"], low=chart_data["Low"], close=chart_data["Close"], name="ذهب")])
fig.add_hline(y=chart_res["last"], line_color="blue", line_width=2, line_dash="dash", annotation_text="دخول " + str(round(chart_res["last"], 2)), annotation_position="top left")
fig.add_hline(y=chart_res["sl"], line_color="red", line_width=2, line_dash="dash", annotation_text="ستوب " + str(round(chart_res["sl"], 2)), annotation_position="bottom left")
fig.add_hline(y=chart_res["tp1"], line_color="green", line_width=2, line_dash="dash", annotation_text="هدف 1 " + str(round(chart_res["tp1"], 2)), annotation_position="top left")
fig.add_hline(y=chart_res["tp2"], line_color="green", line_width=2, line_dash="dash", annotation_text="هدف 2 " + str(round(chart_res["tp2"], 2)), annotation_position="bottom left")
fig.add_hline(y=chart_res["tp3"], line_color="green", line_width=2, line_dash="dash", annotation_text="هدف 3 " + str(round(chart_res["tp3"], 2)), annotation_position="top left")
y_low = min(chart_res["sl"], chart_res["tp1"], chart_res["tp2"], chart_res["tp3"], chart_res["last"]) - chart_res["atr"]
y_high = max(chart_res["sl"], chart_res["tp1"], chart_res["tp2"], chart_res["tp3"], chart_res["last"]) + chart_res["atr"]
fig.update_layout(title="الذهب - " + tf_choice, yaxis_title="السعر", height=600, yaxis=dict(range=[y_low, y_high]), xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# ===== تفاصيل الأخبار =====
st.subheader("تفاصيل الاخبار")
econ_news = [e.title for e in feedparser.parse("https://news.google.com/rss/search?q=gold+price&hl=en-US&gl=US&ceid=US:en").entries[:5]]
pol_news = [e.title for e in feedparser.parse("https://news.google.com/rss/search?q=Trump+tariffs+gold&hl=en-US&gl=US&ceid=US:en").entries[:5]]
st.write("اقتصادية:")
for t in econ_news[:5]:
    st.write("- " + t)
st.write("سياسية:")
for t in pol_news[:5]:
    st.write("- " + t)

# ===== حاسبة الربح =====
st.subheader("💰 حاسبة الربح والخسارة")
c1, c2, c3, c4 = st.columns(4)
calc_entry = c1.number_input("سعر الدخول:", value=float(chart_res["last"]))
calc_sl = c2.number_input("الستوب:", value=float(chart_res["sl"]))
calc_tp = c3.number_input("الهدف:", value=float(chart_res["tp1"]))
calc_lot = c4.number_input("اللوت:", value=0.10)
calc_profit = abs(calc_tp - calc_entry) * 100 * calc_lot
calc_loss = abs(calc_entry - calc_sl) * 100 * calc_lot
st.success(f"ربح الهدف: {round(calc_profit, 2)} $ | خسارة الستوب: {round(calc_loss, 2)} $ | نسبة ربح/خسارة: {round(calc_profit/max(calc_loss,0.01),2)}")

# ===== التقويم =====
st.subheader("📅 التقويم الاقتصادي - USD")
try:
    cal = feedparser.parse("https://nfs.faireconomy.media/ff_calendar_thisweek.xml")
    found = 0
    for e in cal.entries:
        title = e.title if hasattr(e, 'title') else ""
        if "USD" in title and ("High" in title or "high" in title.lower()):
            st.warning(f"🔴 {e.title} - {e.published if hasattr(e, 'published') else ''}")
            found += 1
            if found >= 5:
                break
    if found == 0:
        st.info("ما في أخبار قوية بالدولار اليوم - السوق هادي")
except:
    st.info("ما قدرنا نجيب التقويم هلأ - فوت على ForexFactory قبل ما تدخل")

st.caption("⚠️ تنبيه: هاد التطبيق للمساعدة بالتحليل فقط، مو نصيحة مالية. دايماً التزم بإدارة رأس المال.")

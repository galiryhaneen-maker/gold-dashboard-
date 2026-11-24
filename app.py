import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
import plotly.graph_objects as go
from datetime import datetime
st.set_page_config(page_title="Gold Pro", layout="wide")
PASSWORD = "gold2026"
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth: st.title("Gold Pro")
pw = st.text_input("كلمة السر", type="password") if not st.session_state.auth else ""
if not st.session_state.auth and st.button("دخول", use_container_width=True): st.session_state.auth = (pw == PASSWORD); st.rerun() if st.session_state.auth else st.error("كلمة السر غلط")
if not st.session_state.auth: st.stop()
if st.button("تحديث", use_container_width=True): st.cache_data.clear(); st.rerun()
st.write("اخر تحديث: " + datetime.now().strftime("%H:%M:%S"))
st.title("Gold Pro - 3 جداول")
def get_news(url): feed = feedparser.parse(url); return feed, [e.title.lower() for e in feed.entries[:10]]
def score_titles(titles): pos_w = ["rise", "surge", "gain", "bullish", "rally", "jump", "rebound", "haven", "record"]; neg_w = ["fall", "falls", "drop", "drops", "bearish", "decline", "crash", "plunge", "slump", "tumble"]; p = sum(1 for t in titles if any(" " + w + " " in " " + t + " " for w in pos_w) and not any(" " + w + " " in " " + t + " " for w in neg_w)); n = sum(1 for t in titles if any(" " + w + " " in " " + t + " " for w in neg_w) and not any(" " + w + " " in " " + t + " " for w in pos_w)); return p, n
feed_eco, tit_eco = get_news("https://news.google.com/rss/search?q=gold+inflation+interest+dollar&hl=en&gl=US&ceid=US:en")
feed_pol, tit_pol = get_news("https://news.google.com/rss/search?q=gold+war+geopolitical+tension&hl=en&gl=US&ceid=US:en")
eco_pos, eco_neg = score_titles(tit_eco)
pol_pos, pol_neg = score_titles(tit_pol)
total_pos = eco_pos + pol_pos
total_neg = eco_neg + pol_neg
news_score = "ايجابي" if total_pos > total_neg else "سلبي" if total_neg > total_pos else "محايد"
st.subheader("اخبار الذهب")
st.write("اقتصادية: ايجابي " + str(eco_pos) + " - سلبي " + str(eco_neg))
st.write("سياسية: ايجابي " + str(pol_pos) + " - سلبي " + str(pol_neg))
st.info("مجموع الاخبار: " + news_score)
st.subheader("حاسبة اللوت")
balance = st.number_input("رصيدك", value=1000, min_value=10)
risk_pct = st.slider("مخاطرة %", 0.5, 5.0, 1.0)
risk_money = balance * (risk_pct / 100)
@st.cache_data(ttl=60)
def analyze_tf(per, inter): df = yf.download("GC=F", period=per, interval=inter, progress=False); df.columns = df.columns.get_level_values(0) if isinstance(df.columns, pd.MultiIndex) else df.columns; df = df.dropna(); close = df["Close"]; open_p = df["Open"]; high = df["High"]; low = df["Low"]; last = float(close.iloc[-1]); delta = close.diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean(); rsi_last = float((100 - (100 / (1 + gain / loss))).iloc[-1]); ma20 = float(close.rolling(20).mean().iloc[-1]); tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1); atr = float(tr.rolling(14).mean().iloc[-1]); c0_o = float(open_p.iloc[-1]); c0_c = float(close.iloc[-1]); c0_h = float(high.iloc[-1]); c0_l = float(low.iloc[-1]); c1_o = float(open_p.iloc[-2]); c1_c = float(close.iloc[-2]); body0 = abs(c0_c - c0_o); range0 = c0_h - c0_l; up_wick = c0_h - max(c0_o, c0_c); low_wick = min(c0_o, c0_c) - c0_l; pattern = "ابتلاع صاعد" if (c1_c < c1_o and c0_c > c0_o and c0_c > c1_o and c0_o < c1_c) else "ابتلاع هابط" if (c1_c > c1_o and c0_c < c0_o and c0_c < c1_o and c0_o > c1_c) else "مطرقة" if (low_wick > body0 * 2 and up_wick < body0 * 0.5) else "شهاب" if (up_wick > body0 * 2 and low_wick < body0 * 0.5) else "دوجي" if (body0 < range0 * 0.1) else "بدون نمط"; pscore = 2 if pattern == "ابتلاع صاعد" else -2 if pattern == "ابتلاع هابط" else 1.5 if pattern == "مطرقة" else -1.5 if pattern == "شهاب" else 0; swing_low = float(low.tail(10).min()); swing_high = float(high.tail(10).max()); score = pscore + (1.5 if rsi_last < 30 else -1.5 if rsi_last > 70 else 0) + (1 if news_score == "ايجابي" else -1 if news_score == "سلبي" else 0) + (0.5 if last > ma20 else -0.5); direction = "شراء BUY" if score >= 1 else "بيع SELL" if score <= -1 else "انتظار WAIT"; sl = (swing_low - atr * 0.5) if direction == "شراء BUY" else (swing_high + atr * 0.5) if direction == "بيع SELL" else (swing_low - atr * 0.5); sl_dist = abs(last - sl); tp1 = (last + sl_dist * 1.5) if direction == "شراء BUY" else (last - sl_dist * 1.5) if direction == "بيع SELL" else (last + sl_dist * 1.0); tp2 = (last + sl_dist * 2.5) if direction == "شراء BUY" else (last - sl_dist * 2.5) if direction == "بيع SELL" else (last + sl_dist * 2.0); tp3 = (last + sl_dist * 4.0) if direction == "شراء BUY" else (last - sl_dist * 4.0) if direction == "بيع SELL" else (last + sl_dist * 3.0); reason_txt = ((pattern + " + ") if pattern != "بدون نمط" else "") + ("RSI تشبع بيع + " if rsi_last < 30 else "RSI تشبع شراء + " if rsi_last > 70 else "RSI متوازن + ") + ("اخبار ايجابية + " if news_score == "ايجابي" else "اخبار سلبية + " if news_score == "سلبي" else "اخبار محايدة + ") + ("فوق MA20" if last > ma20 else "تحت MA20"); reason_txt = reason_txt + " = لا توافق" if direction == "انتظار WAIT" else reason_txt; lot = max(round(risk_money / (sl_dist * 100), 2), 0.01); return {"last": last, "rsi": rsi_last, "atr": atr, "pattern": pattern, "direction": direction, "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "lot": lot, "reason": reason_txt, "df": df}
st.subheader("الجداول")
if st.button("حساب جدول السكالبينج", use_container_width=True): st.session_state.show1 = True
if st.session_state.get("show1", False): st.subheader("جدول 1 - سكالبينج"); d = [analyze_tf(p, i) for n, p, i in [("1m", "1d", "1m"), ("5m", "1d", "5m"), ("15m", "5d", "15m")]]; rows = [{"الفريم": n, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["tp2"], 2), "هدف 3": round(r["tp3"], 2), "اللوت": r["lot"], "RSI": round(r["rsi"], 0), "سبب الدخول": r["reason"]} for (n, p, i), r in zip([("1m", "1d", "1m"), ("5m", "1d", "5m"), ("15m", "5d", "15m")], d)]; st.dataframe(pd.DataFrame(rows), use_container_width=True)
if st.button("حساب جدول اليومي", use_container_width=True): st.session_state.show2 = True
if st.session_state.get("show2", False): st.subheader("جدول 2 - يومي"); d = [analyze_tf(p, i) for n, p, i in [("30m", "5d", "30m"), ("1h", "5d", "1h"), ("4h", "1mo", "1h")]]; rows = [{"الفريم": n, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["tp2"], 2), "هدف 3": round(r["tp3"], 2), "اللوت": r["lot"], "RSI": round(r["rsi"], 0), "سبب الدخول": r["reason"]} for (n, p, i), r in zip([("30m", "5d", "30m"), ("1h", "5d", "1h"), ("4h", "1mo", "1h")], d)]; st.dataframe(pd.DataFrame(rows), use_container_width=True)
if st.button("حساب جدول الطويل", use_container_width=True): st.session_state.show3 = True
if st.session_state.get("show3", False): st.subheader("جدول 3 - طويل"); d = [analyze_tf(p, i) for n, p, i in [("1d", "3mo", "1d"), ("1wk", "1y", "1wk"), ("1mo", "5y", "1mo")]]; rows = [{"الفريم": n, "الاتجاه": r["direction"], "السعر": round(r["last"], 2), "الستوب": round(r["sl"], 2), "هدف 1": round(r["tp1"], 2), "هدف 2": round(r["

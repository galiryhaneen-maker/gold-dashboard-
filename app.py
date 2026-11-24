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

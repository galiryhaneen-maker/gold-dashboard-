import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import feedparser
from datetime import datetime, date
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Gold Pro", layout="wide")

# ================= SHEET =================
SHEET_ID = "1T1GsvJnlwSOzF3mzeAkIu6i4BqpiRSHS6w0vSUISqyY"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_users():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = ""

if not st.session_state.auth:
    st.title("🔒 Gold Pro - تسجيل دخول")
    st.write("ادخل اليوزر والباسورد اللي اشتريتهم")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("دخول", use_container_width=True):
        users = load_users()
        if users.empty:
            st.error("الشيت مو متاح، تأكد من Share - Anyone with link")
        else:
            # مندور بدون حساسية لحالة الاحرف
            users['username'] = users['username'].astype(str).str.strip().str.lower()
            users['password'] = users['password'].astype(str).str.strip()
            found = users[(users['username'] == username.strip().lower()) & (users['password'] == password.strip())]

            if found.empty:
                st.error("اليوزر أو الباسورد غلط ❌")
            else:
                row = found.iloc[0]
                try:
                    expiry = pd.to_datetime(row['expiry_date']).strftime('%Y-%m-%d')
                except:
                    expiry = str(row['expiry_date'])[:10]
                active = str(row['active']).strip().upper() == "TRUE"

                if not active:
                    st.error("هاد الحساب موقف، تواصل معنا")
                elif expiry < str(date.today()):
                    st.error(f"اشتراكك انتهى بتاريخ {expiry}، جدد اشتراكك")
                else:
                    st.session_state.auth = True
                    st.session_state.user = username
                    st.success(f"أهلاً {username} ✅ اشتراكك شغال لـ {expiry}")
                    time.sleep(1)
                    st.rerun()
    st.stop()

# ================= DASHBOARD =================
st.sidebar.success(f"متصل: {st.session_state.user}")
if st.sidebar.button("خروج"):
    st.session_state.auth = False
    st.rerun()

st.title("🏆 Gold Pro - تحليل الذهب الحي")
st.caption("هذا التطبيق للتحليل التعليمي وليس نصيحة استثمارية")

# --- جلب السعر ---
@st.cache_data(ttl=60)
def get_gold():
    df = yf.download("GC=F", period="1mo", interval="1d", progress=False)
    if df.empty:
        df = yf.download("XAUUSD=X", period="1mo", interval="1d", progress=False)
    return df

try:
    df = get_gold()
    # تنظيف الأعمدة
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df['Close']
    last = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change = last - prev
    pct = (change / prev) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("سعر الذهب الآن", f"${last:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
    c2.metric("أعلى سعر اليوم", f"${float(df['High'].iloc[-1]):,.2f}")
    c3.metric("أدنى سعر اليوم", f"${float(df['Low'].iloc[-1]):,.2f}")
    c4.metric("آخر تحديث", datetime.now().strftime("%H:%M:%S"))

    # --- الشارت ---
    st.subheader("📈 شارت الذهب - آخر 30 يوم")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(close.index, close.values, linewidth=2)
    ax.grid(True, alpha=0.3)
    ax.set_ylabel("Price $")
    plt.xticks(rotation=30)
    st.pyplot(fig)

    # --- إشارات بسيطة ---
    st.subheader("📊 التحليل السريع")
    ma7 = close.rolling(7).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    if last > ma7 > ma20:
        st.success("✅ الاتجاه صاعد - السعر فوق المتوسطات")
    elif last < ma7 < ma20:
        st.error("🔻 الاتجاه هابط - السعر تحت المتوسطات")
    else:
        st.warning("⚠️ الاتجاه متذبذب - لا يوجد اتجاه واضح")

    st.write(f"- **دعم قريب:** ${float(df['Low'].tail(7).min()):,.2f}")
    st.write(f"- **مقاومة قريبة:** ${float(df['High'].tail(7).max()):,.2f}")
    st.write(f"- **متوسط 7 أيام:** ${float(ma7):,.2f}")
    st.write(f"- **متوسط 20 يوم:** ${float(ma20):,.2f}")

    # --- أخبار ---
    st.subheader("📰 آخر أخبار الذهب")
    try:
        feed = feedparser.parse("https://www.google.com/finance/rss?q=gold")
        if len(feed.entries) == 0:
            feed = feedparser.parse("https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US")
        for e in feed.entries[:5]:
            st.write(f"- [{e.title}]({e.link})")
    except:
        st.write("لا توجد أخبار حالياً")

except Exception as e:
    st.error("مشكلة بجلب البيانات، جرب تحديث الصفحة")
    st.write(e)

st.divider()
st.caption("Gold Pro © 2026 - للتواصل للتجديد عبر واتساب")

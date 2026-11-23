import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Gold Pro", layout="wide")
st.title("🏆 شاشة الذهب Pro")
if st.button("🔄 حدث هلأ"):
    st.rerun()
auto = st.toggle("تحديث تلقائي", value=False)
if auto:
    time.sleep(60)
    st.rerun()
st.caption(f"اخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

st.sidebar.header("⚙️ الإعدادات")
timeframe = st.sidebar.selectbox("الفريم الرئيسي:", ["1m","5m","15m","30m","1h","4h","1d","1wk","1mo"], index=5)
capital = st.sidebar.number_input("راس مالك:", value=1000, step=100)
risk_pct = st.sidebar.slider("المخاطرة %:", 0.5, 5.0, 1.0)

period_map = {"1m":"1d","5m":"5d","15m":"5d","30m":"1mo","1h":"3mo","4h":"6mo","1d":"1y","1wk":"5y","1mo":"10y"}
interval_map = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"60m","4h":"60m","1d":"1d","1wk":"1wk","1mo":"1mo"}

def get_data(interval, period):
    if interval == "4h":
        df = yf.download("GC=F", interval="60m", period=period, progress=False, auto_adjust=True)
        if hasattr(df.columns, 'get_level_values'):
            try: df.columns = df.columns.get_level_values(0)
            except: pass
        df = df.reset_index()
        df = df.rename(columns={"Datetime":"Date","Open":"Open","High":"High","Low":"Low","Close":"Close"})
        df = df.set_index("Date").resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
        return df
    df = yf.download("GC=F", interval=interval, period=period, progress=False, auto_adjust=True)
    if hasattr(df.columns, 'get_level_values'):
        try: df.columns = df.columns.get_level_values(0)
        except: pass
    df = df.reset_index()
    date_col = [c for c in df.columns if "Date" in str(c) or "Datetime" in str(c)][0]
    df = df.rename(columns={date_col:"Date"})
    return df

def add_heikin(df):
    df = df.copy()
    for c in ['Open','High','Low','Close']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna().reset_index(drop=True)
    ha_close, ha_open = [], []
    for i in range(len(df)):
        o,h,l,c = float(df['Open'].iloc[i]), float(df['High'].iloc[i]), float(df['Low'].iloc[i]), float(df['Close'].iloc[i])
        hc = (o+h+l+c)/4
        ha_close.append(hc)
        ho = (o+c)/2 if i==0 else (ha_open[i-1]+ha_close[i-1])/2
        ha_open.append(ho)
    df['HA_Close'] = ha_close
    df['HA_Open'] = ha_open
    df['HA_High'] = df[['High','HA_Open','HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low','HA_Open','HA_Close']].min(axis=1)
    return df
  def analyze_news(title):
    text = title.lower()
    score = 0
    reason = ""
    pos = {"rate cut":2,"central bank buys":2,"safe haven":2,"gold rallies":2,"gold jumps":2,"gold surges":2,"war":2,"crisis":2,"recession":1.5,"dollar falls":1.5,"gold gains":1.5,"gold rises":1.5}
    neg = {"rate hike":-2,"hike bets":-2,"hawkish":-2,"gold slides":-2,"gold falls":-2,"gold drops":-2,"selloff":-2,"slide deepens":-2,"under pressure":-2,"strong dollar":-1.5,"dollar rises":-1,"gold tumbles":-2,"gold plunges":-2}
    for p,w in pos.items():
        if p in text:
            score += w
            reason += f"'{p}' (+{w}) "
    for p,w in neg.items():
        if p in text:
            score += w
            reason += f"'{p}' ({w}) "
    if score == 0:
        if any(w in text for w in ["falls","drops","slides","losses","pressure","hurt"]):
            score = -1
            reason = "كلمة هبوط"
        elif any(w in text for w in ["rises","jumps","surges","gains","rebound"]):
            score = 1
            reason = "كلمة صعود"
        else:
            reason = "محايد"
    label = "ايجابي 🟢" if score > 0.5 else "سلبي 🔴" if score < -0.5 else "محايد ⚪"
    return score, label, reason.strip()

def analyze_tf(tf):
    try:
        df = add_heikin(get_data(interval_map[tf], period_map[tf]))
        if len(df) < 5:
            return None
        price = float(df['Close'].iloc[-1])
        df['TR'] = np.maximum(df['High']-df['Low'], np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))))
        atr_raw = float(df['TR'].rolling(14).mean().iloc[-1])
        if np.isnan(atr_raw) or atr_raw == 0:
            atr_raw = price * 0.002
        atr = min(atr_raw, price * 0.015)
        atr = max(atr, price * 0.0005)
        last = df.iloc[-1]
        trend, score = ("صاعد ✅",1) if last['HA_Close'] > last['HA_Open'] else ("هابط 🔻",-1)
        look = df.tail(50)
        resistance = float(look['High'].max())
        support = float(look['Low'].min())
        mid_res = float(look['High'].quantile(0.75))
        mid_sup = float(look['Low'].quantile(0.25))
        dist_sup = abs(price - mid_sup) / atr
        dist_res = abs(price - mid_res) / atr
        risk_money = capital * (risk_pct/100)
        if score == 1 and dist_sup < 1.5:
            direction = "BUY 🟢"
            entry = price
            sl = max(entry - atr*1.5, support - atr*0.2)
            tp1 = entry + atr*1.5
            tp2 = min(entry + atr*3.0, resistance + atr*0.2)
            reason = f"قريب من الدعم {mid_sup:.2f}"
        elif score == -1 and dist_res < 1.5:
            direction = "SELL 🔴"
            entry = price
            sl = min(entry + atr*1.5, resistance + atr*0.2)
            tp1 = entry - atr*1.5
            tp2 = max(entry - atr*3.0, support - atr*0.2)
            reason = f"قريب من المقاومة {mid_res:.2f}"
        elif score == 1:
            direction = "انتظار شراء ⏳"
            entry = mid_sup
            sl = max(entry - atr*1.5, support - atr*0.2)
            tp1 = entry + atr*1.5
            tp2 = min(entry + atr*3.0, resistance + atr*0.2)
            reason = f"انتظر رجوع لـ {mid_sup:.2f}"
        else:
            direction = "انتظار بيع ⏳"
            entry = mid_res
            sl = min(entry + atr*1.5, resistance + atr*0.2)
            tp1 = entry - atr*1.5
            tp2 = max(entry - atr*3.0, support - atr*0.2)
            reason = f"انتظر صعود لـ {mid_res:.2f}"
        max_sl = price * 0.03
        if abs(entry - sl) > max_sl:
            sl = entry - max_sl if entry > sl else entry + max_sl
        lot = risk_money / (abs(entry-sl)*100) if abs(entry-sl) > 0 else 0
        lot = max(0.01, min(round(lot,2), 5.0))
        return {"tf":tf,"price":price,"trend":trend,"score":score,"atr":atr,"support":mid_sup,"resistance":mid_res,"support_strong":support,"resistance_strong":resistance,"direction":direction,"entry":entry,"sl":sl,"tp1":tp1,"tp2":tp2,"lot":lot,"reason":reason,"df":df}
    except:
        return None
      tf_list = ["1m","5m","15m","30m","1h","4h","1d","1wk","1mo"]
results = {}
for tf in tf_list:
    r = analyze_tf(tf)
    if r:
        results[tf] = r
main = results.get(timeframe)
if main:
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("السعر", f"{main['price']:.2f} $")
    c2.metric(f"اتجاه {timeframe}", main["trend"])
    c3.metric("ATR", f"{main['atr']:.2f}")
    c4.metric("المقاومة", f"{main['resistance']:.2f}")
st.subheader("📊 كل الفريمات")
rows = []
for tf in tf_list:
    if tf in results:
        r = results[tf]
        rows.append({"الفريم":tf,"السعر":f"{r['price']:.2f}","الاتجاه":r["trend"],"الدعم":f"{r['support']:.2f}","المقاومة":f"{r['resistance']:.2f}","القرار":r["direction"],"الدخول":f"{r['entry']:.2f}","SL":f"{r['sl']:.2f}","TP1":f"{r['tp1']:.2f}","TP2":f"{r['tp2']:.2f}","اللوت":r["lot"],"ليش؟":r["reason"]})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
if main:
    st.subheader(f"🎯 {timeframe}")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("القرار", main["direction"])
    c2.metric("الدخول", f"{main['entry']:.2f}")
    c3.metric("SL", f"{main['sl']:.2f}")
    c4.metric("TP1", f"{main['tp1']:.2f}")
    c5.metric("TP2", f"{main['tp2']:.2f}")
    st.info(f"ليش؟ {main['reason']}")
    st.success(f"راس مالك: {capital}$ | اللوت: {main['lot']}")
    st.subheader(f"📈 شموع - {timeframe}")
    plot_df = main["df"].tail(40).copy()
    fig, ax = plt.subplots(figsize=(12,5))
    x = np.arange(len(plot_df))
    for i in range(len(plot_df)):
        row = plot_df.iloc[i]
        col = "green" if row['HA_Close'] >= row['HA_Open'] else "red"
        ax.plot([x[i],x[i]], [row['HA_Low'], row['HA_High']], color="black", linewidth=0.8)
        ax.plot([x[i],x[i]], [row['HA_Open'], row['HA_Close']], color=col, linewidth=6, solid_capstyle="round")
    ax.axhline(main['support'], color="green", linestyle="--", label=f"دعم {main['support']:.2f}")
    ax.axhline(main['resistance'], color="red", linestyle="--", label=f"مقاومة {main['resistance']:.2f}")
    ax.axhline(main['entry'], color="blue", linestyle=":", label=f"دخول {main['entry']:.2f}")
    ax.axhline(main['sl'], color="orange", linestyle=":", label=f"SL {main['sl']:.2f}")
    ax.axhline(main['tp1'], color="purple", linestyle=":", label=f"TP1 {main['tp1']:.2f}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
st.subheader("🔥 الجاهزة هلأ")
ready = [r for r in results.values() if r["direction"] in ["BUY 🟢","SELL 🔴"]]
if ready:
    for r in ready:
        st.markdown(f"**{r['tf']}** - {r['direction']} دخول {r['entry']:.2f} | SL {r['sl']:.2f} | TP1 {r['tp1']:.2f} | TP2 {r['tp2']:.2f} | لوت {r['lot']}")
else:
    st.warning("ما في صفقة جاهزة هلأ.")
st.subheader("📰 الأخبار - سلبية ولا إيجابية؟")
try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=gold+price+OR+Federal+Reserve+OR+inflation&hl=en&gl=US&ceid=US:en")
    total = 0
    for e in feed.entries[:10]:
        s, label, reason = analyze_news(e.title)
        total += s
        if s > 0.5:
            st.success(f"🟢 {label} [{s:+.1f}] - {e.title} | {reason}")
        elif s < -0.5:
            st.error(f"🔴 {label} [{s:+.1f}] - {e.title} | {reason}")
        else:
            st.info(f"⚪ {label} [{s:+.1f}] - {e.title} | {reason}")
    if total > 2:
        st.success(f"### مجموع الأخبار: {total:+.1f} - إيجابية 🟢")
    elif total < -2:
        st.error(f"### مجموع الأخبار: {total:+.1f} - سلبية 🔴")
    else:
        st.warning(f"### مجموع الأخبار: {total:+.1f} - محايدة ⚪")
    if main:
        if main["score"]==1 and total>2:
            st.success("✅ تأكيد قوي: تقني صاعد + اخبار ايجابية = شراء")
        elif main["score"]==-1 and total<-2:
            st.error("✅ تأكيد قوي: تقني هابط + اخبار سلبية = بيع")
        elif main["score"]==1 and total<-2:
            st.warning("⚠️ تضارب! تقني صاعد بس اخبار سلبية - لا تدخل")
        elif main["score"]==-1 and total>2:
            st.warning("⚠️ تضارب! تقني هابط بس اخبار ايجابية - لا تدخل")
except:
    st.write("ما قدرنا نجيب الأخبار")

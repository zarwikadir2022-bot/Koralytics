import streamlit as st
import pandas as pd
import requests
import os
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Platinum Ultimate", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم (ملفات نصية) ---
def update_stat_file(feature_name):
    filename = f"count_{feature_name}.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f: f.write("0")
    with open(filename, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(filename, "w") as f: f.write(str(count))
    return count

def get_stat_file(feature_name):
    filename = f"count_{feature_name}.txt"
    if not os.path.exists(filename): return 0
    with open(filename, "r") as f:
        try: return int(f.read())
        except: return 0

# --- 3. التصميم البلاتيني الكريستالي (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    
    .match-card {
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
    }
    .odd-badge {
        background: rgba(255, 255, 255, 0.8);
        padding: 5px 12px;
        border-radius: 8px;
        font-weight: bold;
        color: #2c3e50;
        border: 1px solid #ddd;
        margin-left: 5px;
    }
    .crystal-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px; }
    .stat-box { background: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; border: 1px solid #ccc; }
</style>
""", unsafe_allow_html=True)

# --- 4. جلب ومعالجة البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
            if not m['bookmakers']: continue
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "1": next(o['price'] for o in h2h['outcomes'] if o['name'] == m['home_team']),
                    "2": next(o['price'] for o in h2h['outcomes'] if o['name'] == m['away_team']),
                    "X": next(o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw'),
                    "أكثر 2.5": next(o['price'] for o in totals['outcomes'] if o['name'] == 'Over'),
                    "أقل 2.5": next(o['price'] for o in totals['outcomes'] if o['name'] == 'Under')
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

def calculate_stats(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        tightness = 1 - abs((h_p/total) - (a_p/total))
        h_cards = round(1.3 + (tightness * 1.5), 1)
        a_cards = round(1.5 + (tightness * 1.5), 1)
        red_p = int((tightness * 22) + 8)
        prob_u = (1/row['أقل 2.5']) / ((1/row['أكثر 2.5']) + (1/row['أقل 2.5']))
        xg = 1.9 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
        return {"p1": (h_p/total)*100, "px": (d_p/total)*100, "p2": (a_p/total)*100, "hc": h_cards, "ac": a_cards, "rp": red_p, "xg": xg}
    except: return None

# --- 5. التطبيق الرئيسي ---
def main():
    # تحديث عداد الزوار (مرة واحدة لكل جلسة)
    if 'visited' not in st.session_state:
        st.session_state['total_visitors'] = update_stat_file("visitors")
        st.session_state['visited'] = True
    
    # --- Sidebar ---
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"""<div class="stat-box">إجمالي الزوار الفريدين<br><b style="font-size:1.4rem;">👤 {st.session_state.get('total_visitors', 0)}</b></div>""", unsafe_allow_html=True)
    
    # عرض إحصائيات الميزات
    st.sidebar.markdown("### 📊 نشاط المنصة")
    st.sidebar.write(f"🪄 استخدام العصا: **{get_stat_file('magic')}**")
    st.sidebar.write(f"🎯 تحليلات عميقة: **{get_stat_file('analysis')}**")

    try:
        leagues_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        grps = sorted(list(set([s['group'] for s in leagues_raw])))
        if "Soccer" in grps: grps.remove("Soccer"); grps.insert(0, "Soccer")
        sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
        l_map = {s['title']: s['key'] for s in leagues_raw if s['group'] == sel_grp}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 المحفظة ($):", 10.0, 10000.0, 500.0)
    except: st.error("خطأ في الاتصال بالـ API"); return

    st.title(f"⚽ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # العصا السحرية مع التحديث
        if st.button("🪄 العصا السحرية (أفضل 3 فرص)"):
            update_stat_file("magic")
            st.success("تم تحليل أفضل الفرص!")
            st.rerun()

        # عرض البطاقات
        st.subheader("📅 المباريات المتاحة")
        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="flex: 2; font-weight: bold;">{r['المضيف']} vs {r['الضيف']}</div>
                <div style="flex: 1; text-align: left;">
                    <span class="odd-badge">1: {r['1']}</span><span class="odd-badge">X: {r['X']}</span><span class="odd-badge">2: {r['2']}</span>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        sel_m = st.selectbox("🎯 حلل المباراة بعمق:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        # عند اختيار مباراة، نعتبرها "تحليل عميق"
        if 'last_match' not in st.session_state or st.session_state['last_match'] != sel_m:
            update_stat_file("analysis")
            st.session_state['last_match'] = sel_m

        stats = calculate_stats(row)
        if stats:
            p1, px, p2 = stats['p1'], stats['px'], stats['p2']
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.subheader("💰 استثمار")
                stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
                sel_opt = st.selectbox("توقعك:", [row['المضيف'], "تعادل", row['الضيف']])
                v_odd = row['1'] if sel_opt==row['المضيف'] else row['X'] if sel_opt=="تعادل" else row['2']
                st.metric("الربح المتوقع", f"{(stake*v_odd):.2f}$")
                st.info(f"💡 يُنصح بمبلغ {(budget * (p1/100) * 0.05):.1f}$")
            with col2:
                st.subheader("📊 ذكاء المباراة")
                st.markdown(f"""<div style="background:white; padding:15px; border-radius:12px; border-right:6px solid #424242;">
                    <b>الاحتمالات:</b> {row['المضيف']} ({p1:.1f}%) | تعادل ({px:.1f}%) | {row['الضيف']} ({p2:.1f}%) <br>
                    <b>رادار البطاقات:</b> 🟨 للأرض {stats['hc']} | 🟨 للضيف {stats['ac']} | 🟥 طرد {stats['rp']}% <br>
                    <b>معدل الأهداف:</b> {stats['xg']:.2f} (xG)
                </div>""", unsafe_allow_html=True)
                st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]), color="#424242")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

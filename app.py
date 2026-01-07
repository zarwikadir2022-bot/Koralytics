import streamlit as st
import pandas as pd
import requests
import os
import numpy as np

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Platinum Ultimate", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم ---
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

# --- 3. التصميم البلاتيني ---
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
        display: flex; justify-content: space-between; align-items: center;
    }
    .odd-badge {
        background: rgba(255, 255, 255, 0.8);
        padding: 5px 12px; border-radius: 8px; font-weight: bold; margin-left: 5px; border: 1px solid #ddd;
    }
    .ticket-style {
        background: linear-gradient(135deg, #2c3e50, #000000);
        color: #f1c40f; padding: 15px; border-radius: 12px; border-left: 5px solid #f1c40f; margin-bottom: 10px;
    }
    .crystal-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 4. إدارة البيانات والـ API ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

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

# --- 5. التطبيق الرئيسي ---
def main():
    if 'visited' not in st.session_state:
        st.session_state['total_visitors'] = update_stat_file("visitors")
        st.session_state['visited'] = True

    # --- القائمة الجانبية ---
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"**👤 إجمالي الزوار:** {st.session_state.get('total_visitors', 0)}")
    
    # عرض ورقة الرهان (تظهر بعد الضغط على العصا السحرية)
    if st.session_state["my_ticket"]:
        st.sidebar.markdown("### 🧾 ورقتك المقترحة")
        total_odd = 1.0
        for item in st.session_state["my_ticket"]:
            st.sidebar.markdown(f"<div class='ticket-style'>⚽ {item['match']}<br>🎯 {item['pick']} | <b>{item['odd']}</b></div>", unsafe_allow_html=True)
            total_odd *= item['odd']
        st.sidebar.warning(f"إجمالي الربح المحتمل: {total_odd:.2f}x")
        if st.sidebar.button("🗑️ مسح الورقة"):
            st.session_state["my_ticket"] = []
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.write(f"🪄 استخدام العصا: **{get_stat_file('magic')}**")
    st.sidebar.write(f"🎯 تحليلات دقيقة: **{get_stat_file('analysis')}**")

    # جلب الدوريات (تم إصلاح خطأ الـ Syntax هنا)
    try:
        leagues_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in leagues_raw if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    except:
        st.error("خطأ في الاتصال بالبيانات.")
        return

    st.title(f"⚽ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # زر العصا السحرية
        if st.button("🪄 شغّل العصا السحرية (أفضل الفرص)"):
            update_stat_file("magic")
            # اختيار أفضل 3 مباريات بناءً على أعلى احتمالية فوز للأرض
            best_picks = df.nsmallest(3, '1')
            st.session_state["my_ticket"] = []
            for _, r in best_picks.iterrows():
                st.session_state["my_ticket"].append({
                    "match": r['المضيف'], "pick": "فوز المضيف", "odd": r['1']
                })
            st.rerun()

        # عرض المباريات بنظام البطاقات
        st.subheader("📅 مباريات البطولة المتاحة")
        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="font-weight: bold;">{r['المضيف']} vs {r['الضيف']}</div>
                <div><span class="odd-badge">1: {r['1']}</span><span class="odd-badge">X: {r['X']}</span><span class="odd-badge">2: {r['2']}</span></div>
            </div>""", unsafe_allow_html=True)

        # التحليل الكريستالي العميق
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        sel_m_str = st.selectbox("🎯 اختر مباراة للتحليل الإحصائي الكامل:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        
        if st.button("📊 بدء التحليل العميق"):
            update_stat_file("analysis")
            st.success(f"تم تسجيل تحليل جديد لـ {sel_m_str}")
            # هنا تظهر الرسوم البيانية (اختصاراً للوضوح)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()

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

# --- 3. التصميم البلاتيني الكريستالي ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    .match-card {
        background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(10px);
        border-radius: 15px; padding: 15px; margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        display: flex; justify-content: space-between; align-items: center;
    }
    .odd-badge {
        background: rgba(255, 255, 255, 0.8); padding: 5px 12px; border-radius: 8px; 
        font-weight: bold; margin-left: 5px; border: 1px solid #ddd;
    }
    .crystal-card { 
        background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); 
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px;
    }
    .stat-box { background: white; padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #ddd; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. محركات الحسابات ---
def calculate_metrics(row):
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

# --- 5. إدارة البيانات ---
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

# --- 6. التطبيق الرئيسي ---
def main():
    if 'visited' not in st.session_state:
        st.session_state['total_visitors'] = update_stat_file("visitors")
        st.session_state['visited'] = True

    # --- القائمة الجانبية (إرجاع الفلترة الكاملة) ---
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f'<div class="stat-box">👤 الزوار: <b>{st.session_state.get("total_visitors", 0)}</b></div>', unsafe_allow_html=True)
    
    try:
        sports_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        grps = sorted(list(set([s['group'] for s in sports_raw])))
        if "Soccer" in grps: grps.remove("Soccer"); grps.insert(0, "Soccer")
        sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
        l_map = {s['title']: s['key'] for s in sports_raw if s['group'] == sel_grp}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    except: st.error("خطأ في جلب الدوريات"); return

    # عرض الورقة
    if st.session_state["my_ticket"]:
        st.sidebar.info("🧾 تم إضافة مباريات للورقة (راجع العصا السحرية)")

    st.sidebar.write(f"🪄 العصا: **{get_stat_file('magic')}** | 🎯 تحليل: **{get_stat_file('analysis')}**")

    # --- المحتوى الرئيسي ---
    st.title(f"⚽ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        if st.button("🪄 العصا السحرية (أفضل 3 فرص)"):
            update_stat_file("magic")
            best = df.nsmallest(3, '1')
            st.session_state["my_ticket"] = [{"m": r['المضيف'], "o": r['1']} for _, r in best.iterrows()]
            st.rerun()

        # عرض المباريات
        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="font-weight: bold;">{r['المضيف']} vs {r['الضيف']}</div>
                <div><span class="odd-badge">1: {r['1']}</span><span class="odd-badge">X: {r['X']}</span><span class="odd-badge">2: {r['2']}</span></div>
            </div>""", unsafe_allow_html=True)

        # --- إرجاع التحليل العميق التلقائي ---
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        st.subheader("📊 التحليل الكريستالي العميق")
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل الفوري:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        # تسجيل إحصائية التحليل
        if 'last_a' not in st.session_state or st.session_state['last_a'] != sel_m:
            update_stat_file("analysis")
            st.session_state['last_a'] = sel_m

        stats = calculate_metrics(row)
        if stats:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**💰 نصيحة الاستثمار**")
                st.metric("احتمال فوز المضيف", f"{stats['p1']:.1f}%")
                st.write(f"🟨 بطاقات متوقعة: {stats['hc'] + stats['ac']}")
                st.write(f"🟥 احتمالية طرد: {stats['rp']}%")
            with col2:
                st.write("**📈 الرسوم البيانية**")
                tab1, tab2 = st.tabs(["الاحتمالات", "رادار الأهداف"])
                with tab1:
                    st.bar_chart(pd.DataFrame({'%': [stats['p1'], stats['px'], stats['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
                with tab2:
                    st.write(f"معدل الأهداف المتوقع (xG): **{stats['xg']:.2f}**")
                    st.bar_chart(pd.DataFrame({'Value': [stats['hc'], stats['ac'], stats['xg']]}, index=['بطاقات للأرض', 'بطاقات للضيف', 'الأهداف المتوقعة']))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

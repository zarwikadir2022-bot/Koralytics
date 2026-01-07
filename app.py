import streamlit as st
import pandas as pd
import requests
import os
import numpy as np

# --- 1. إعدادات الصفحة الفاخرة ---
st.set_page_config(page_title="Koralytics AI | Platinum", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم ---
def update_stat_file(feature_name):
    filename = f"stat_{feature_name}.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f: f.write("0")
    with open(filename, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(filename, "w") as f: f.write(str(count))
    return count

def get_stat_file(feature_name):
    filename = f"stat_{feature_name}.txt"
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
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
    }
    .odd-badge {
        background: rgba(255, 255, 255, 0.8); padding: 5px 12px; border-radius: 8px; 
        font-weight: bold; margin-left: 5px; border: 1px solid #ddd;
    }
    .magic-box {
        background: linear-gradient(135deg, #2c3e50 0%, #000000 100%);
        color: #f1c40f; padding: 20px; border-radius: 15px; margin-bottom: 20px;
        border-right: 8px solid #f1c40f; box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .crystal-card { 
        background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); 
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px;
    }
    .confidence-meter {
        text-align:center; background:linear-gradient(90deg, #2ecc71, #27ae60); 
        color:white; padding:10px; border-radius:10px; margin-top:15px; font-weight:bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. محرك الحسابات الإحصائية (التحليل العميق) ---
def calculate_all_stats(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        tightness = 1 - abs((h_p/total) - (a_p/total))
        h_cards = round(1.3 + (tightness * 1.5), 1)
        a_cards = round(1.5 + (tightness * 1.5), 1)
        red_p = int((tightness * 22) + 8)
        prob_u = (1/row['أقل 2.5']) / ((1/row['أكثر 2.5']) + (1/row['أقل 2.5']))
        xg = 1.9 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
        conf = int((h_p/total)*100 + (20 if xg > 2.5 else 10))
        return {"p1": (h_p/total)*100, "px": (d_p/total)*100, "p2": (a_p/total)*100, 
                "hc": h_cards, "ac": a_cards, "rp": red_p, "xg": xg, "conf": min(conf, 94)}
    except: return None

# --- 5. جلب البيانات ---
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

# --- 6. التطبيق الرئيسي ---
def main():
    if 'is_counted' not in st.session_state:
        st.session_state['visitor_num'] = update_stat_file("unique_visitors")
        st.session_state['is_counted'] = True
    
    # القائمة الجانبية
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f'<div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #ddd;">الزوار الفريدون 👤 <b>{get_stat_file("unique_visitors")}</b></div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"**🪄 العصا:** {get_stat_file('magic_wand')} | **🎯 التحليل:** {get_stat_file('deep_analysis')}")
    st.sidebar.markdown("---")

    try:
        sports_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        grps = sorted(list(set([s['group'] for s in sports_raw])))
        if "Soccer" in grps: grps.remove("Soccer"); grps.insert(0, "Soccer")
        sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
        l_map = {s['title']: s['key'] for s in sports_raw if s['group'] == sel_grp}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 الميزانية ($):", 10, 5000, 500)
    except: st.error("خطأ في البيانات"); return

    st.title(f"⚽ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        if st.button("🪄 تفعيل العصا السحرية"):
            update_stat_file("magic_wand")
            st.session_state['show_magic'] = True
            st.rerun()
        
        if st.session_state.get('show_magic'):
            best = df.nsmallest(3, '1')
            st.markdown('<div class="magic-box"><h3>🪄 تذكرة العصا السحرية المقترحة:</h3>', unsafe_allow_html=True)
            for _, r in best.iterrows():
                st.write(f"🔹 **{r['المضيف']}** أودز: {r['1']}")
            st.markdown('</div>', unsafe_allow_html=True)

        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="font-weight: bold;">{r['المضيف']} vs {r['الضيف']}</div>
                <div><span class="odd-badge">1: {r['1']}</span><span class="odd-badge">X: {r['X']}</span><span class="odd-badge">2: {r['2']}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        st.subheader("📊 التحليل الإحصائي العميق")
        sel_m = st.selectbox("🎯 اختر مباراة:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
            update_stat_file("deep_analysis")
            st.session_state['last_m'] = sel_m

        stats = calculate_all_stats(row)
        if stats:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("💰 استثمار")
                stake = st.number_input("الرهان ($):", 1, 1000, 10)
                st.metric("الربح الصافي", f"{(stake*row['1'] - stake):.2f}$")
                st.info(f"💡 استثمر: **{(budget * 0.05):.1f}$**")
            with c2:
                st.subheader("📊 الذكاء الاصطناعي")
                st.write(f"✅ احتمالية الفوز: **{stats['p1']:.1f}%**")
                st.write(f"🟨 بطاقات: **{stats['hc'] + stats['ac']}** | 🟥 طرد: **{stats['rp']}%**")
                st.write(f"🥅 الأهداف المتوقعة (xG): **{stats['xg']:.2f}**")
                st.markdown(f'<div class="confidence-meter">🎯 مؤشر الثقة: {stats["conf"]}%</div>', unsafe_allow_html=True)
                st.bar_chart(pd.DataFrame({'%': [stats['p1'], stats['px'], stats['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Platinum Tunisia", page_icon="💎", layout="wide")

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

# --- 3. محرك توقيت تونس والنتائج المتوقعة ---
def get_tn_time(utc_time_str):
    try:
        dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        return (dt + timedelta(hours=1)).strftime("%d/%m | %H:%M")
    except: return "قريباً"

def predict_exact_score(p1, px, p2, xg):
    # محرك منطقي لتوقع النتيجة الرقمية بناءً على الاحتمالات والأهداف المتوقعة
    if px > 35: # احتمالية تعادل عالية
        return "1 - 1" if xg > 2.0 else "0 - 0"
    if p1 > p2: # المضيف أقرب للفوز
        if p1 > 60: return "3 - 0" if xg > 3.0 else "2 - 0"
        return "2 - 1" if xg > 2.2 else "1 - 0"
    else: # الضيف أقرب للفوز
        if p2 > 60: return "0 - 3" if xg > 3.0 else "0 - 2"
        return "1 - 2" if xg > 2.2 else "0 - 1"

# --- 4. التصميم البلاتيني ---
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
    .score-box {
        background: linear-gradient(135deg, #2c3e50, #000000);
        color: #f1c40f; padding: 15px; border-radius: 12px;
        text-align: center; border: 2px solid #f1c40f; margin-bottom: 15px;
    }
    .ai-box { background: white; padding: 12px; border-radius: 10px; border-right: 5px solid #2c3e50; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'], "التوقيت": get_tn_time(m['commence_time']),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'],
                    "أكثر 2.5": totals['outcomes'][0]['price'], "أقل 2.5": totals['outcomes'][1]['price']
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        st.session_state['v_num'] = update_stat_file("unique_visitors")
        st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"👤 الزوار: **{get_stat_file('unique_visitors')}** | 🎯 التحليلات: **{get_stat_file('deep_analysis')}**")

    try:
        sports = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in sports if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 المحفظة ($):", 10, 5000, 500)
    except: st.error("خطأ بيانات"); return

    st.title(f"🏟️ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # زر العصا السحرية
        if st.button("🪄 تفعيل العصا السحرية"):
            update_stat_file("magic_wand")
            st.session_state['magic'] = True
        
        if st.session_state.get('magic'):
            best = df.nsmallest(3, '1')
            st.markdown('<div style="background:black; color:gold; padding:15px; border-radius:10px;">🪄 أفضل 3 مباريات بنسبة فوز عالية للمضيف</div>', unsafe_allow_html=True)
            for _, r in best.iterrows(): st.write(f"✅ **{r['المضيف']}**")

        st.markdown("---")
        # عرض المباريات
        for _, r in df.iterrows():
            st.markdown(f'<div class="match-card"><div>🕒 {r["التوقيت"]}<br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div>{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

        # --- قسم التحليل العميق مع النتيجة المتوقعة ---
        st.markdown("<div style='background:rgba(255,255,255,0.6); padding:20px; border-radius:20px; margin-top:20px;'>", unsafe_allow_html=True)
        st.header("📊 المختبر الإحصائي الذكي")
        sel_m = st.selectbox("🎯 اختر مباراة لتحليل نتيجتها:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        # حسابات التحليل
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > 0.5 else 3.2
        exact_score = predict_exact_score(p1, px, p2, xg)

        if 'last_a' not in st.session_state or st.session_state['last_a'] != sel_m:
            update_stat_file("deep_analysis")
            st.session_state['last_a'] = sel_m

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""<div class="score-box">
                <span style="font-size:1rem;">النتيجة المتوقعة</span><br>
                <b style="font-size:2.5rem;">{exact_score}</b>
            </div>""", unsafe_allow_html=True)
            st.info(f"💡 ينصح باستثمار: **{(budget * 0.05):.1f}$**")
        with col2:
            st.markdown(f'<div class="ai-box">فوز الأرض: {p1:.1f}% | تعادل: {px:.1f}% | فوز الضيف: {p2:.1f}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ai-box">البطاقات المتوقعة: 🟨 {round(1.5+p1/100, 1)} | الأهداف المتوقعة: 🥅 {xg}</div>', unsafe_allow_html=True)
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

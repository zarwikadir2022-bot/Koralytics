import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Official", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم ---
def update_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        with open(fn, "w") as f: f.write("0")
    with open(fn, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(fn, "w") as f: f.write(str(count))
    return count

def get_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn): return 0
    with open(fn, "r") as f:
        try: return int(f.read())
        except: return 0

# --- 3. محرك توقيت تونس والنتائج الرقمية ---
def get_tn_time(utc_str):
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
        return (dt + timedelta(hours=1)).strftime("%d/%m | %H:%M")
    except: return "قريباً"

def predict_exact_score(p1, px, p2, xg):
    if px > 34: return "1 - 1" if xg > 2.0 else "0 - 0"
    if p1 > p2:
        if p1 > 60: return "3 - 0" if xg > 3.0 else "2 - 0"
        return "2 - 1" if xg > 2.2 else "1 - 0"
    else:
        if p2 > 60: return "0 - 3" if xg > 3.0 else "0 - 2"
        return "1 - 2" if xg > 2.2 else "0 - 1"

# --- 4. التصميم الإمبراطوري المحسن ---
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
    .score-banner {
        background: linear-gradient(90deg, #1e3799, #000000);
        color: #f1c40f; padding: 25px; border-radius: 15px;
        text-align: center; border: 2px solid #f1c40f; margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .feature-box { background: white; padding: 12px; border-radius: 10px; border-right: 5px solid #1e3799; margin-bottom: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

@st.cache_data(ttl=3600)
def fetch_data(l_key):
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
        st.session_state['v_num'] = update_stat("unique_visitors")
        st.session_state['v'] = True

    # القائمة الجانبية الإحصائية
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"""
    <div style="background:white; padding:15px; border-radius:12px; border:1px solid #ddd; text-align:center;">
        <span style="font-size:0.9rem;">👤 الزوار: <b>{get_stat('unique_visitors')}</b></span><br>
        <span style="font-size:0.9rem;">🎯 التحليلات: <b>{get_stat('deep_analysis')}</b></span>
    </div>
    """, unsafe_allow_html=True)

    try:
        sports = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in sports if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 ميزانية المحفظة ($):", 10, 5000, 500)
    except: st.error("خطأ في الاتصال بالسيرفر"); return

    st.title(f"🏟️ {sel_l}")
    df = fetch_data(l_map[sel_l])
    
    if not df.empty:
        # العصا السحرية
        if st.button("🪄 تفعيل العصا السحرية للفرص الذهبية"):
            update_stat("magic_wand")
            st.session_state['magic'] = True
        
        if st.session_state.get('magic'):
            best = df.nsmallest(3, '1')
            st.warning("🪄 أفضل 3 مباريات بنسبة فوز عالية للمضيف حالياً:")
            for _, r in best.iterrows(): st.write(f"✅ **{r['المضيف']}** (الأودز: {r['1']})")

        # عرض قائمة المباريات
        for _, r in df.iterrows():
            st.markdown(f'<div class="match-card"><div>🕒 {r["التوقيت"]}<br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div>{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

        # المختبر الإحصائي العميق (الميزات المثبتة)
        st.markdown("<div style='background:rgba(255,255,255,0.7); padding:30px; border-radius:25px; margin-top:20px; border:1px solid rgba(255,255,255,0.9);'>", unsafe_allow_html=True)
        st.header("🔬 المختبر الإحصائي الذكي")
        sel_m = st.selectbox("🎯 اختر مباراة لتحليل كافة جوانبها:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_a' not in st.session_state or st.session_state['last_a'] != sel_m:
            update_stat("deep_analysis")
            st.session_state['last_a'] = sel_m

        # محرك الحسابات
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > 0.5 else 3.2
        exact_score = predict_exact_score(p1, px, p2, xg)
        tight = 1 - abs((p1/100) - (p2/100))

        # عرض النتيجة المتوقعة (بشكل بارز)
        st.markdown(f"""<div class="score-banner">
            <span style="font-size:1.2rem; opacity:0.8;">النتيجة الرقمية المتوقعة</span><br>
            <span style="font-size:3.5rem;">{exact_score}</span>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="feature-box">📈 احتمالية فوز المضيف: {p1:.1f}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="feature-box">🟨 البطاقات: {round(1.5+tight*2,1)} | 🟥 طرد: {int(tight*20)}%</div>', unsafe_allow_html=True)
            st.success(f"💰 المبلغ المقترح للمراهنة: **{(budget * 0.05):.1f}$**")
        with col2:
            st.markdown(f'<div class="feature-box">🥅 الأهداف المتوقعة (xG): {xg}</div>', unsafe_allow_html=True)
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

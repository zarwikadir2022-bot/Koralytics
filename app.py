import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Official", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات ---
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

# --- 3. محرك التوقيت والنتائج ---
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

# --- 4. التصميم الفاخر (CSS) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .stApp {{ background: #f0f4f8; }}
    
    /* الشريط المتحرك */
    .ticker-wrap {{ width: 100%; overflow: hidden; background: #fbbf24; padding: 10px 0; border-bottom: 2px solid #000; margin-bottom: 20px; }}
    .ticker {{ display: inline-block; white-space: nowrap; animation: ticker 25s linear infinite; font-weight: bold; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .ticker-item {{ display: inline-block; padding: 0 40px; font-size: 1.1rem; color: #000; }}

    .match-card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    .score-banner {{ background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 30px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px; }}
    .card-detail {{ padding: 12px; border-radius: 10px; margin-bottom: 10px; font-weight: bold; border: 1px solid #ddd; background: white; }}
    .yellow-card {{ border-right: 6px solid #f1c40f; color: #856404; }}
    .red-card {{ border-right: 6px solid #e74c3c; color: #721c24; }}
</style>
""", unsafe_allow_html=True)

# --- 5. الشريط المتحرك العلوي ---
st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span class="ticker-item">🚀 Koralytics AI: تم تحليل {get_stat('deep_analysis')} مباراة اليوم بنجاح</span>
    <span class="ticker-item">👤 عدد الزوار الكلي: {get_stat('unique_visitors')}</span>
    <span class="ticker-item">🏟️ تغطية كاملة لجميع الرياضات والدوريات العالمية بتوقيت تونس</span>
</div></div>
""", unsafe_allow_html=True)

# --- 6. جلب البيانات ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=3600)
def fetch_data(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}).json()
        res = []
        for m in r:
            mkts = m.get('bookmakers', [{}])[0].get('markets', [])
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'], "التوقيت": get_tn_time(m['commence_time']),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'],
                    "X": h2h['outcomes'][2]['price'] if len(h2h['outcomes']) > 2 else 1.0,
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 7. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        update_stat("unique_visitors"); st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.info(f"👤 الزوار: {get_stat('unique_visitors')} | 🎯 التحليلات: {get_stat('deep_analysis')}")

    try:
        sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        sport_groups = sorted(list(set([s['group'] for s in sports_data])))
        sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=sport_groups.index('Soccer') if 'Soccer' in sport_groups else 0)
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        sel_l_name = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 المحفظة ($):", 10, 5000, 500)
    except: st.error("خطأ في البيانات"); return

    st.title(f"🏟️ {sel_l_name}")
    df = fetch_data(l_map[sel_l_name])
    
    if not df.empty:
        # عرض الجدول
        for _, r in df.iterrows():
            st.markdown(f'<div class="match-card"><div>🕒 <small>{r["التوقيت"]}</small><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div>{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.header("🔬 المختبر الإحصائي التفصيلي")
        sel_m = st.selectbox("🎯 اختر مباراة لتحليل الأوراق والنتائج:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
            update_stat("deep_analysis"); st.session_state['last_m'] = sel_m

        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > (1/row['أكثر 2.5']) else 3.1
        score = predict_exact_score(p1, px, p2, xg)
        tight = 1 - abs((p1/100) - (p2/100))

        st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:3.5rem;">{score}</span></div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 نسب الفوز")
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        with c2:
            st.subheader("🎴 رادار الانضباط والأهداف")
            yellows = round(2.5 + tight * 3, 1)
            st.markdown(f'<div class="card-detail yellow-card">🟨 عدد البطاقات الصفراء المتوقع: {yellows}</div>', unsafe_allow_html=True)
            red_prob = int(tight * 35)
            st.markdown(f'<div class="card-detail red-card">🟥 احتمالية الكرت الأحمر: {red_prob}%</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-detail" style="border-right: 6px solid #2ecc71;">🥅 الأهداف المتوقعة (xG): {xg}</div>', unsafe_allow_html=True)
            st.success(f"💰 رهان مقترح: {(budget*0.05):.1f}$")
    else: st.info("لا توجد مباريات.")

if __name__ == '__main__': main()

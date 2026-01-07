import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Master", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات (حفظ دائم) ---
def get_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        with open(fn, "w") as f: f.write("0")
        return 0
    with open(fn, "r") as f:
        try:
            content = f.read().strip()
            return int(content) if content else 0
        except: return 0

def update_stat(feat):
    current = get_stat(feat)
    new_val = current + 1
    with open(f"stat_{feat}.txt", "w") as f:
        f.write(str(new_val))
    return new_val

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

# --- 4. التصميم البلاتيني ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .stApp {{ background: #f1f5f9; }}
    .ticker-wrap {{ width: 100%; overflow: hidden; background: #fbbf24; padding: 10px 0; border-bottom: 2px solid #000; margin-bottom: 20px; }}
    .ticker {{ display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; }}
    @keyframes ticker {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
    .match-card {{ background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .score-banner {{ background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 30px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
    .stat-item {{ background: white; padding: 10px; border-radius: 8px; border-right: 5px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# --- 5. تسجيل الزيارة ---
if 'visited' not in st.session_state:
    update_stat("unique_visitors")
    st.session_state['visited'] = True

# --- 6. الشريط المتحرك العلوي ---
st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding: 0 30px;">🔥 مرحباً بزوار تونيزيا سات في Koralytics AI</span>
    <span style="padding: 0 30px;">🎯 إجمالي التحليلات الذكية اليوم: {get_stat('deep_analysis')} </span>
    <span style="padding: 0 30px;">👤 عدد المستخدمين الكلي للمنصة: {get_stat('unique_visitors')}</span>
    <span style="padding: 0 30px;">⚽ توقعات دقيقة للأهداف والبطاقات لجميع الدوريات</span>
</div></div>
""", unsafe_allow_html=True)

# --- 7. جلب البيانات من API ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=600)
def fetch_odds_data(l_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
        r = requests.get(url, params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}).json()
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

# --- 8. القائمة الجانبية ---
st.sidebar.title("💎 Koralytics AI")
st.sidebar.write(f"👤 الزوار: **{get_stat('unique_visitors')}** | 🎯 التحليلات: **{get_stat('deep_analysis')}**")

try:
    sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    sport_groups = sorted(list(set([s['group'] for s in sports_data])))
    sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=sport_groups.index('Soccer') if 'Soccer' in sport_groups else 0)
    l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
    sel_l_name = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    budget = st.sidebar.number_input("💵 الميزانية ($):", 10, 5000, 500)
except: st.error("فشل الاتصال"); st.stop()

# --- 9. العرض الرئيسي ---
df = fetch_odds_data(l_map[sel_l_name])
if not df.empty:
    st.subheader(f"📅 مباريات {sel_l_name}")
    for _, r in df.iterrows():
        st.markdown(f'<div class="match-card"><div>🕒 <small>{r["التوقيت"]}</small><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div>{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي الذكي")
    sel_m = st.selectbox("🎯 اختر مباراة لتحليلها بالكامل:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
    row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
    
    if st.button("🚀 ابدأ التحليل الفني الآن"):
        update_stat("deep_analysis")
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > (1/row['أكثر 2.5']) else 3.2
        score = predict_exact_score(p1, px, p2, xg)
        tight = 1 - abs((p1/100) - (p2/100))

        st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:3.5rem;">{score}</span></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 نسب الفوز")
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
            st.success(f"💰 الرهان المقترح: **{(budget * 0.05):.1f}$**")
        with c2:
            st.subheader("📝 الرؤية الفنية")
            st.markdown(f'<div class="stat-item">🥅 الأهداف المتوقعة (xG): {xg}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-item">🟨 البطاقات الصفراء: {round(2.5+tight*3,1)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-item">🟥 احتمالية الطرد: {int(tight*35)}%</div>', unsafe_allow_html=True)
            st.info(f"🎯 مؤشر ثقة التوقع: {int(max(p1,p2,px)+12)}%")

if __name__ == '__main__': pass

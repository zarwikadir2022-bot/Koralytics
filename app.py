import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Financial Elite", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات (تثبيت العدادات) ---
def get_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        with open(fn, "w") as f: f.write("0")
        return 0
    with open(fn, "r") as f:
        try: content = f.read().strip(); return int(content) if content else 0
        except: return 0

def update_stat(feat):
    current = get_stat(feat)
    new_val = current + 1
    with open(f"stat_{feat}.txt", "w") as f: f.write(str(new_val))
    return new_val

if 'counted' not in st.session_state:
    update_stat("unique_visitors")
    st.session_state['counted'] = True

# --- 3. محرك المستشار المالي الذكي ---
def get_financial_plan(conf, budget):
    if conf > 85:
        return {"msg": "🚀 فرصة ذهبية: ثقة عالية جداً", "risk": "منخفضة", "bet": budget * 0.15, "color": "#064e3b"}
    elif conf > 70:
        return {"msg": "⚖️ استثمار متوازن: حظوظ جيدة", "risk": "متوسطة", "bet": budget * 0.08, "color": "#1e3a8a"}
    else:
        return {"msg": "⚠️ مخاطرة عالية: لا ينصح بالمخاطرة", "risk": "عالية", "bet": budget * 0.02, "color": "#991b1b"}

# --- 4. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f1f5f9; }
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 10px 0; border-bottom: 2px solid #000; margin-bottom: 20px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; }
    .stat-box { background: white; padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; }
    .advisor-card { background: white; border-radius: 15px; padding: 20px; border: 2px solid #10b981; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- 5. الواجهة العلوية ---
v_count = get_stat('unique_visitors')
a_count = get_stat('deep_analysis')

st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 30px;">📊 المستشار المالي نشط الآن | الزوار: {v_count} | التحليلات: {a_count}</span>
    <span style="padding:0 30px;">🏆 كأس أمم أفريقيا: تحليل شامل لمباريات الجزائر، مصر، والمغرب</span>
</div></div>
""", unsafe_allow_html=True)

# --- 6. جلب البيانات ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=600)
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
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "التوقيت": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)).strftime("%H:%M"),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'],
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 7. القائمة الجانبية ---
st.sidebar.title("💎 Koralytics AI")
budget = st.sidebar.number_input("💰 ميزانية الاستثمار ($):", 10, 10000, 500)

try:
    sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    l_map = {s['title']: s['key'] for s in sports_data if s['group'] == 'Soccer'}
    sel_l_name = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()), index=0)
except: st.stop()

# --- 8. العرض الرئيسي ---
df = fetch_data(l_map[sel_l_name])

if not df.empty:
    st.header(f"🔬 تحليل {sel_l_name}")
    sel_m = st.selectbox("🎯 اختر مباراة للتحليل:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
    row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]

    if 'last' not in st.session_state or st.session_state['last'] != sel_m:
        update_stat("deep_analysis")
        st.session_state['last'] = sel_m

    # الحسابات
    p1 = (1/row['1'])/(1/row['1']+1/row['2']+1/row['X'])*100
    p2 = (1/row['2'])/(1/row['1']+1/row['2']+1/row['X'])*100
    px = (1/row['X'])/(1/row['1']+1/row['2']+1/row['X'])*100
    conf = int(max(p1, p2, px) + 10)
    plan = get_financial_plan(conf, budget)

    # عرض البانر
    st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:3.5rem;">{int(p1/30)} - {int(p2/35)}</span></div>', unsafe_allow_html=True)

    # قسم المستشار المالي
    st.write("")
    st.markdown(f"""
    <div class="advisor-card" style="border-color: {plan['color']}">
        <h3 style="color: {plan['color']};">{plan['msg']}</h3>
        <p>📊 مؤشر الثقة: <b>{conf}%</b> | 🛡️ مستوى المخاطرة: <b>{plan['risk']}</b></p>
        <hr>
        <p style="font-size: 1.2rem;">💵 المبلغ المقترح للاستثمار: <b style="color: #10b981;">{plan['bet']:.2f}$</b></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 رادار البطاقات والأهداف")
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["المضيف"]}: {round(p1/40,1)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["الضيف"]}: {round(p2/40,1)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color: gold;">🟨 بطاقات {row["المضيف"]}: {round(2+p2/100,1)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color: gold;">🟨 بطاقات {row["الضيف"]}: {round(2+p1/100,1)}</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 احتمالات الفوز")
        st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))

else:
    st.warning("⚠️ لا توجد مباريات نشطة حالياً في هذه البطولة. يرجى اختيار 'Africa Cup of Nations' أو 'Premier League' من القائمة الجانبية.")

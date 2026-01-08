import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Financial & Analytics Pro", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات (عداد حقيقي) ---
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

def track_league(league_name):
    with open("stat_leagues.txt", "a", encoding="utf-8") as f: f.write(league_name + "\n")

# --- 3. محرك التوقعات والذكاء المالي ---
def financial_advice(confidence, p1, px, p2):
    if confidence > 85: return "💰 فرصة ذهبية: ثقة عالية جداً. استثمار آمن."
    if confidence > 70: return "⚖️ استثمار متوسط: حظوظ قوية، لكن التزم بالحذر."
    return "⚠️ مخاطرة عالية: لا تنصح بالاستثمار المالي في هذه المباراة."

# --- 4. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f8fafc; }
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 10px 0; border-bottom: 2px solid #000; margin-bottom: 20px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-right: 5px solid #1e3a8a; }
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .stat-box { background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 8px; font-weight: bold; font-size: 0.9rem; }
    .advisor-box { background: #ecfdf5; border: 1px solid #10b981; padding: 15px; border-radius: 12px; color: #064e3b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 5. الواجهة العلوية ---
v_count = get_stat('unique_visitors')
a_count = get_stat('deep_analysis')

st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 30px;">🌍 كأس أمم أفريقيا: تحليل قمم اليوم ⚽</span>
    <span style="padding:0 30px;">👤 الزوار: {v_count}</span>
    <span style="padding:0 30px;">🎯 إجمالي التحليلات: {a_count}</span>
    <span style="padding:0 30px;">💎 Koralytics AI: المستشار المالي والرياضي الأول</span>
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
            if h2h and len(h2h['outcomes']) >= 3:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "التوقيت": (datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)).strftime("%d/%m | %H:%M"),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'],
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 7. القائمة الجانبية ---
st.sidebar.title("💎 Koralytics AI")
st.sidebar.write(f"👤 الزوار: **{v_count}**")
st.sidebar.write(f"🎯 التحليلات: **{a_count}**")

try:
    sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    sport_groups = sorted(list(set([s['group'] for s in sports_data])))
    sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=0)
    l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
    sel_l_name = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
except: st.stop()

# --- 8. العرض الرئيسي ---
df = fetch_data(l_map[sel_l_name])

if not df.empty:
    st.subheader(f"📅 مباريات {sel_l_name}")
    for _, r in df.iterrows():
        st.markdown(f'<div class="match-card"><div>🕒 {r["التوقيت"]}<br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div>{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي والمستشار المالي")
    
    sel_m = st.selectbox("🎯 اختر مباراة لتحليلها تفصيلياً:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
    row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]

    if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
        update_stat("deep_analysis")
        st.session_state['last_m'] = sel_m

    # حسابات الذكاء الاصطناعي
    p1 = (1/row['1'])/(1/row['1']+1/row['2']+1/row['X'])*100
    p2 = (1/row['2'])/(1/row['1']+1/row['2']+1/row['X'])*100
    px = (1/row['X'])/(1/row['1']+1/row['2']+1/row['X'])*100
    xg_total = 1.8 if row['أقل 2.5'] > row['أكثر 2.5'] else 3.1
    conf = int(max(p1, p2, px) + 10)
    
    # تفصيل الأهداف والبطاقات
    xg_h = round(xg_total * (p1/100) + 0.5, 1)
    xg_a = round(xg_total * (p2/100) + 0.3, 1)
    cards_h = round(2.1 + (p2/100), 1)
    cards_a = round(2.3 + (p1/100), 1)

    # 1. البانر الرئيسي
    st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:3.5rem;">{int(xg_h)} - {int(xg_a)}</span></div>', unsafe_allow_html=True)

    # 2. المستشار المالي
    st.markdown(f'<div class="advisor-box">{financial_advice(conf, p1, px, p2)} (مؤشر الثقة: {conf}%)</div>', unsafe_allow_html=True)
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 فرص الفوز")
        st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
    
    with col2:
        st.subheader("📋 رادار المباراة التفصيلي")
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["المضيف"]} المتوقعة: {xg_h}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["الضيف"]} المتوقعة: {xg_a}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right: 5px solid gold;">🟨 بطاقات {row["المضيف"]}: {cards_h}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right: 5px solid gold;">🟨 بطاقات {row["الضيف"]}: {cards_a}</div>', unsafe_allow_html=True)
        st.error(f"🟥 احتمالية طرد في المباراة: {int((1-(abs(p1-p2)/100))*30)}%")

else:
    st.info("ننتظر توفر بيانات المباريات لهذه البطولة...")

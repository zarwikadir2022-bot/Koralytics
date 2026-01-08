import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Pro Lab", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الذكي ---
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

# الحماية من تكرار العداد عند الـ Refresh
if 'v_counted' not in st.session_state:
    update_stat("unique_visitors")
    st.session_state['v_counted'] = True

def track_league(league_name):
    with open("stat_leagues.txt", "a", encoding="utf-8") as f: f.write(league_name + "\n")

def get_popular_leagues():
    fn = "stat_leagues.txt"
    if not os.path.exists(fn): return {}
    try:
        with open(fn, "r", encoding="utf-8") as f: leagues = f.read().splitlines()
        if not leagues: return {}
        return pd.Series([l for l in leagues if l]).value_counts().head(3).to_dict()
    except: return {}

# --- 3. التصميم البصري المطور (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f1f5f9; }
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 10px 0; border-bottom: 2px solid #000; margin-bottom: 20px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-right: 6px solid #1e3a8a; }
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 25px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stat-box { background: white; padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e3a8a; }
    .advisor-box { background: #ecfdf5; border: 2px solid #10b981; padding: 15px; border-radius: 12px; color: #064e3b; font-weight: bold; text-align: center; }
    .popular-tag { background: #1e3a8a; color: white; padding: 4px 10px; border-radius: 8px; margin-bottom: 5px; display: inline-block; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 4. الشريط العلوي ---
v_count = get_stat('unique_visitors')
a_count = get_stat('deep_analysis')
st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 30px;">🌍 كأس أمم أفريقيا: تحليل الجزائر ومصر والمغرب بتوقيت تونس 🇹🇳</span>
    <span style="padding:0 30px;">👤 الزوار: {v_count} | 🎯 إجمالي التحليلات: {a_count}</span>
</div></div>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات ---
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
                dt = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "التاريخ": dt.strftime("%d/%m"), "الوقت": dt.strftime("%H:%M"),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'] if len(h2h['outcomes'])>2 else 1.0,
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. القائمة الجانبية ---
st.sidebar.title("💎 Koralytics AI")
invest_cap = st.sidebar.number_input("💰 ميزانية الاستثمار ($):", 10, 5000, 500)

try:
    sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    sport_groups = sorted(list(set([s['group'] for s in sports_data])))
    sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=sport_groups.index('Soccer') if 'Soccer' in sport_groups else 0)
    l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
    sel_l_name = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    
    st.sidebar.markdown("---")
    pop_leagues = get_popular_leagues()
    if pop_leagues:
        st.sidebar.subheader("🔥 الأكثر طلباً")
        for league, count in pop_leagues.items():
            st.sidebar.markdown(f'<div class="popular-tag">{count} - {league}</div>', unsafe_allow_html=True)
except: st.stop()

# --- 7. العرض والمختبر ---
df = fetch_data(l_map[sel_l_name])

if not df.empty:
    st.subheader(f"📅 مباريات {sel_l_name} (توقيت تونس)")
    for _, r in df.iterrows():
        st.markdown(f'<div class="match-card"><div><span style="background:#1e3a8a; color:white; padding:2px 8px; border-radius:5px;">{r["التاريخ"]}</span> <b>{r["الوقت"]}</b><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div style="font-weight:bold; color:#1e3a8a;">{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي")
    match_list = [f"{r['التاريخ']} | {r['الوقت']} | {r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()]
    sel_match = st.selectbox("🎯 اختر مباراة لتحليلها بالذكاء الاصطناعي:", match_list)
    
    match_name = sel_match.split(" | ")[2].split(" ضد ")[0]
    row = df[df['المضيف'] == match_name].iloc[0]

    if 'current_m' not in st.session_state or st.session_state['current_m'] != sel_match:
        update_stat("deep_analysis")
        track_league(sel_l_name)
        st.session_state['current_m'] = sel_match

    # الحسابات الفنية المتقدمة
    p1, p2, px = (1/row['1']), (1/row['2']), (1/row['X'])
    total_prob = p1 + p2 + px
    prob1, probx, prob2 = (p1/total_prob)*100, (px/total_prob)*100, (p2/total_prob)*100
    confidence = int(max(prob1, probx, prob2) + 12)
    
    xg_base = 1.9 if row['أقل 2.5'] > row['أكثر 2.5'] else 3.2
    xh, xa = round(xg_base*(prob1/100)+0.4, 1), round(xg_base*(prob2/100)+0.2, 1)
    ch, ca = round(2.1+(prob2/100), 1), round(2.3+(prob1/100), 1)

    # عرض النتائج
    st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:3.5rem;">{int(xh)} - {int(xa)}</span></div>', unsafe_allow_html=True)
    
    advice_text = "🚀 فرصة ذهبية" if confidence > 80 else "⚖️ استثمار متوازن" if confidence > 65 else "⚠️ مخاطرة عالية"
    st.markdown(f'<div class="advisor-box">💰 المستشار المالي: {advice_text} | المبلغ المقترح: {invest_cap*(confidence/200):.1f}$ (ثقة: {confidence}%)</div>', unsafe_allow_html=True)
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 رادار التفاصيل")
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["المضيف"]} (xG): {xh}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["الضيف"]} (xG): {xa}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color:gold;">🟨 بطاقات {row["المضيف"]}: {ch}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color:gold;">🟨 بطاقات {row["الضيف"]}: {ca}</div>', unsafe_allow_html=True)
    with col2:
        st.subheader("📊 نسب الفوز")
        st.bar_chart(pd.DataFrame({'%': [prob1, probx, prob2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
else:
    st.info("اختر بطولة نشطة من القائمة الجانبية.")

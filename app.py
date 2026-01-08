import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Final Fix", page_icon="⚽", layout="wide")

# --- 2. محرك الإحصائيات (مصحح التنسيق) ---
def safe_stat_update(feat):
    fn = f"stat_{feat}.txt"
    try:
        if not os.path.exists(fn):
            with open(fn, "w") as f:
                f.write("0")
            current = 0
        else:
            with open(fn, "r") as f:
                content = f.read().strip()
                current = int(content) if content else 0
        
        new_val = current + 1
        with open(fn, "w") as f:
            f.write(str(new_val))
        return new_val
    except:
        return 0

def get_stat_only(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        return 0
    try:
        with open(fn, "r") as f:
            return int(f.read().strip())
    except:
        return 0

if 'session_tracked' not in st.session_state:
    safe_stat_update("unique_visitors")
    st.session_state['session_tracked'] = True

# --- 3. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f8fafc; }
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 12px 0; border-bottom: 3px solid #000; margin-bottom: 25px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; }
    @keyframes ticker { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-right: 6px solid #1e3a8a; transition: 0.3s; }
    .match-card:hover { transform: scale(1.01); border-right-width: 10px; }
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 30px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .stat-box { background: white; padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e3a8a; }
    .advisor-card { padding: 20px; border-radius: 15px; text-align: center; font-weight: bold; border: 2px solid; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. العرض العلوي ---
v_total = get_stat_only('unique_visitors')
a_total = get_stat_only('deep_analysis')
st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 50px;">🌍 Koralytics AI: التحليل الذكي لمباريات كرة القدم ⚽</span>
    <span style="padding:0 50px;">👤 الزوار: {v_total} | 🎯 التحليلات: {a_total}</span>
    <span style="padding:0 50px;">🇹🇳 توقيت تونس (GMT+1) | تغطية حصرية لكأس أمم أفريقيا</span>
</div></div>
""", unsafe_allow_html=True)

# --- 5. محرك البيانات ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

def fetch_data(l_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200: return pd.DataFrame()
            
        r = response.json()
        res = []
        for m in r:
            if not m.get('bookmakers'): continue
            mkts = m['bookmakers'][0].get('markets', [])
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            
            if h2h:
                dt = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                
                over_price = 1.85
                under_price = 1.85
                if totals and len(totals['outcomes']) > 1:
                    over_price = totals['outcomes'][0]['price']
                    under_price = totals['outcomes'][1]['price']
                
                outcomes = h2h['outcomes']
                p1 = outcomes[0]['price']
                p2 = outcomes[1]['price']
                px = 1.0
                if len(outcomes) > 2:
                    px = outcomes[2]['price']

                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "التاريخ": dt.strftime("%d/%m"), "الوقت": dt.strftime("%H:%M"),
                    "1": p1, "2": p2, "X": px,
                    "أكثر 2.5": over_price, "أقل 2.5": under_price
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. القائمة الجانبية (الأولوية لكرة القدم) ---
st.sidebar.title("💎 Koralytics AI")
budget = st.sidebar.number_input("💰 ميزانية الاستثمار ($):", 10, 5000, 500)

try:
    s_req = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}', timeout=10)
    if s_req.status_code == 200:
        sports_data = s_req.json()
        sport_groups = sorted(list(set([s['group'] for s in sports_data])))
        
        if 'Soccer' in sport_groups:
            sport_groups.remove('Soccer')
            sport_groups.insert(0, 'Soccer')
        
        sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=0)
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        
        # اختيار ذكي للبطولة
        l_keys = list(l_map.keys())
        default_idx = 0
        for i, k in enumerate(l_keys):
            if "Africa" in k or "Premier League" in k:
                default_idx = i
                break
        
        sel_l_name = st.sidebar.selectbox("🏆 البطولة", l_keys, index=default_idx)
    else:
        st.sidebar.error("خطأ في الاتصال")
        st.stop()
except:
    st.sidebar.warning("جاري التحميل...")
    st.stop()

# --- 7. التحليل والعرض ---
df = fetch_data(l_map[sel_l_name])

if not df.empty:
    st.subheader(f"📅 جدول مباريات {sel_l_name}")
    for _, r in df.iterrows():
        st.markdown(f'<div class="match-card"><div><span style="background:#1e3a8a; color:white; padding:2px 8px; border-radius:5px; font-size:0.8rem;">{r["التاريخ"]}</span> <b>{r["الوقت"]}</b><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div style="font-weight:bold; color:#1e3a8a;">{r["1"]} | {r["X"]} | {r["2"]}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي")
    match_options = [f"{r['التاريخ']} | {r['الوقت']} | {r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()]
    sel_match = st.selectbox("🎯 اختر مباراة للتحليل:", match_options)
    
    if 'curr_match' not in st.session_state or st.session_state['curr_match'] != sel_match:
        safe_stat_update("deep_analysis")
        st.session_state['curr_match'] = sel_match

    match_name = sel_match.split(" | ")[2].split(" ضد ")[0]
    row = df[df['المضيف'] == match_name].iloc[0]

    # الحسابات
    p1, p2, px = (1/row['1']), (1/row['2']), (1/row['X'])
    total_p = p1 + p2 + px
    prob1, probx, prob2 = (p1/total_p)*100, (px/total_p)*100, (p2/total_p)*100
    conf = min(int(max(prob1, probx, prob2) + 12), 95)
    
    xg_base = 1.9 if row['أقل 2.5'] > row['أكثر 2.5'] else 3.1
    xh, xa = round(xg_base*(prob1/100)+0.4, 1), round(xg_base*(prob2/100)+0.2, 1)
    ch, ca = round(2.1+(prob2/100), 1), round(2.3+(prob1/100), 1)

    # ألوان المستشار المالي
    if conf > 80: advice, color, bg = "🚀 فرصة ذهبية", "#16a34a", "#f0fdf4"
    elif conf > 65: advice, color, bg = "⚖️ استثمار متوازن", "#2563eb", "#eff6ff"
    else: advice, color, bg = "⚠️ مخاطرة عالية", "#dc2626", "#fef2f2"

    st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:4rem;">{int(xh)} - {int(xa)}</span></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="advisor-card" style="border-color: {color}; background-color: {bg}; color: {color};">
        <h3 style="margin:0;">💰 المستشار المالي: {advice}</h3>
        <p style="margin:5px 0;">مؤشر الثقة: <b>{conf}%</b> | المبلغ المقترح: <b>{budget*(conf/200):.1f}$</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 رادار المباراة")
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["المضيف"]} (xG): {xh}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box">⚽ أهداف {row["الضيف"]} (xG): {xa}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color:gold;">🟨 بطاقات {row["المضيف"]}: {ch}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-right-color:gold;">🟨 بطاقات {row["الضيف"]}: {ca}</div>', unsafe_allow_html=True)
    with col2:
        st.subheader("📊 احتمالات الفوز")
        st.bar_chart(pd.DataFrame({'%': [prob1, probx, prob2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
else:
    st.warning("⚠️ لا توجد مباريات متاحة في هذه البطولة حالياً.")
    st.info("💡 اختر بطولة أخرى من القائمة.")

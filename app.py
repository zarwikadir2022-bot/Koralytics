import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Pro", page_icon="💎", layout="wide")

# ==========================================
# ⚙️ إعدادات واتساب (عدّل الرقم هنا)
# ==========================================
# ضع رقمك مع رمز الدولة (مثال تونس: 216xxxxxxxxx) بدون علامة +
OWNER_PHONE = "21694928912" 
WHATSAPP_MSG = "مرحباً، أرغب في الحصول على كود تفعيل العضوية الذهبية (VIP) 💎"
# تجهيز الرابط
wa_url = f"https://wa.me/{OWNER_PHONE}?text={urllib.parse.quote(WHATSAPP_MSG)}"

# --- 2. محرك الإحصائيات (الثابت) ---
START_VISITORS = 383
START_ANALYSIS = 446

def safe_stat_update(feat):
    fn = f"stat_{feat}.txt"
    try:
        if not os.path.exists(fn):
            with open(fn, "w") as f: f.write("0")
            current = 0
        else:
            with open(fn, "r") as f: current = int(f.read().strip() or 0)
        
        new_val = current + 1
        with open(fn, "w") as f: f.write(str(new_val))
        return new_val
    except: return 0

def get_stat_only(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn): return 0
    try:
        with open(fn, "r") as f: return int(f.read().strip())
    except: return 0

if 'session_tracked' not in st.session_state:
    safe_stat_update("unique_visitors")
    st.session_state['session_tracked'] = True

# --- 3. CSS (التصميم) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f8fafc; }
    
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 12px 0; border-bottom: 3px solid #000; margin-bottom: 25px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 40s linear infinite; font-weight: bold; color: #000; }
    @keyframes ticker { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-right: 6px solid #1e3a8a; transition: 0.3s; }
    .match-card:hover { transform: scale(1.01); border-right-width: 10px; }
    
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 30px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; }
    .stat-box { background: white; padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e3a8a; }
    .advisor-card { padding: 20px; border-radius: 15px; text-align: center; font-weight: bold; border: 2px solid; margin-top: 10px; }
    
    .blurred-content { filter: blur(6px); opacity: 0.7; pointer-events: none; user-select: none; }
    .lock-overlay { position: relative; margin-top: -160px; text-align: center; z-index: 10; background: rgba(255,255,255,0.9); padding: 25px; border-radius: 15px; border: 1px solid #ddd; backdrop-filter: blur(5px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    
    /* زر الواتساب */
    .wa-btn { background:#25D366; color:white !important; padding:12px 25px; text-decoration:none; border-radius:50px; font-weight:bold; display:inline-block; margin-top:10px; box-shadow: 0 4px 6px rgba(37, 211, 102, 0.3); transition: 0.3s; }
    .wa-btn:hover { transform: scale(1.05); box-shadow: 0 6px 8px rgba(37, 211, 102, 0.4); }
</style>
""", unsafe_allow_html=True)

# --- 4. العرض العلوي والعدادات ---
v_total = get_stat_only('unique_visitors') + START_VISITORS
a_total = get_stat_only('deep_analysis') + START_ANALYSIS

st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 40px;">💎 Koralytics AI: الذكاء الاصطناعي في خدمة توقعاتك</span>
    <span style="padding:0 40px;">👤 إجمالي الزوار: {v_total}</span>
    <span style="padding:0 40px;">🎯 تحليلات ناجحة: {a_total}</span>
    <span style="padding:0 40px;">🇹🇳 توقيت تونس (GMT+1)</span>
    <span style="padding:0 40px;">📲 تواصل معنا عبر واتساب للحصول على العضوية</span>
</div></div>
""", unsafe_allow_html=True)

# --- 5. محرك المفاتيح ---
ALL_KEYS = [st.secrets.get(f"KEY{i}") for i in range(1, 11)]
VALID_KEYS = [k for k in ALL_KEYS if k is not None]

def fetch_data_with_rotation(l_key):
    for api_key in VALID_KEYS:
        try:
            url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
            params = {'apiKey': api_key, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            response = requests.get(url, params=params, timeout=6)
            if response.status_code == 200: return process_response(response.json())
            elif response.status_code in [401, 429]: continue
        except: continue
    return pd.DataFrame()

def process_response(r):
    res = []
    for m in r:
        if not m.get('bookmakers'): continue
        mkts = m['bookmakers'][0].get('markets', [])
        h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
        totals = next((i for i in mkts if i['key'] == 'totals'), None)
        
        if h2h:
            dt = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
            over_price = 1.85
            if totals and len(totals['outcomes']) > 1: over_price = totals['outcomes'][0]['price']
            
            outcomes = h2h['outcomes']
            p1 = outcomes[0]['price']
            p2 = outcomes[1]['price']
            px = outcomes[2]['price'] if len(outcomes) > 2 else 1.0

            res.append({
                "المضيف": m['home_team'], "الضيف": m['away_team'],
                "التاريخ": dt.strftime("%d/%m"), "الوقت": dt.strftime("%H:%M"),
                "1": p1, "2": p2, "X": px,
                "أكثر 2.5": over_price
            })
    return pd.DataFrame(res)

# --- 6. القائمة الجانبية ---
st.sidebar.title("💎 إعدادات التحكم")

vip_code_input = st.sidebar.text_input("🔑 كود العضوية (VIP):", type="password")
is_vip = (vip_code_input == st.secrets.get("VIP_ACCESS_CODE", "KORA2025"))

if is_vip:
    st.sidebar.success(f"✅ العضوية مفعلة")
else:
    # زر واتساب في القائمة الجانبية
    st.sidebar.markdown(f"""
    <div style="text-align:center; padding:10px; background:#e0f2fe; border-radius:10px; margin-bottom:10px;">
        <small>ليس لديك كود؟</small><br>
        <a href="{wa_url}" target="_blank" style="color:#0369a1; font-weight:bold; text-decoration:none;">📲 اطلبه عبر واتساب</a>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")
budget = st.sidebar.number_input("💰 ميزانية الاستثمار ($):", 10, 10000, 500)
st.sidebar.markdown("---")

try:
    sports_data = []
    for key in VALID_KEYS:
        try:
            req = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={key}', timeout=5)
            if req.status_code == 200:
                sports_data = req.json()
                break
        except: continue

    if sports_data:
        sport_groups = sorted(list(set([s['group'] for s in sports_data])))
        if 'Soccer' in sport_groups: sport_groups.insert(0, sport_groups.pop(sport_groups.index('Soccer')))
        
        sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=0)
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        
        l_keys = list(l_map.keys())
        default_idx = next((i for i, k in enumerate(l_keys) if "Premier League" in k or "La Liga" in k), 0)
        sel_l_name = st.sidebar.selectbox("🏆 البطولة", l_keys, index=default_idx)
    else: st.stop()
except: st.stop()

# --- 7. التطبيق الرئيسي ---
df = fetch_data_with_rotation(l_map[sel_l_name])

if not df.empty:
    st.subheader(f"📅 جدول مباريات: {sel_l_name}")
    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="match-card">
            <div>
                <span style="background:#1e3a8a; color:white; padding:2px 8px; border-radius:5px; font-size:0.8rem;">{r["التاريخ"]}</span> 
                <b>{r["الوقت"]}</b><br><b>{r["المضيف"]} <span style="color:#fbbf24">VS</span> {r["الضيف"]}</b>
            </div>
            <div style="font-weight:bold; color:#1e3a8a; direction:ltr;">1: {r["1"]} | X: {r["X"]} | 2: {r["2"]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي (VIP)")

    if not is_vip:
        # --- الشاشة المقفلة مع زر واتساب ---
        st.markdown(f"""
        <div class="blurred-content">
            <div class="score-banner"><span style="font-size:3rem;">2 - 1</span></div>
            <div class="advisor-card" style="border-color: #2563eb; background-color: #eff6ff;">
                <h3>💰 المستشار المالي: استثمار متوازن</h3>
            </div>
            <br><div style="display:flex; gap:10px;"><div class="stat-box" style="flex:1">⚽ xG: 1.8</div></div>
        </div>
        
        <div class="lock-overlay">
            <h2 style="color:#1e3a8a;">🚫 المحتوى مغلق (VIP Only)</h2>
            <p>للحصول على التوقعات الدقيقة ونصائح المستشار المالي، يرجى الاشتراك.</p>
            <a href="{wa_url}" target="_blank" class="wa-btn">
                📲 اشترك الآن عبر واتساب
            </a>
            <p style="margin-top:15px; font-size:0.8rem; color:#666;">سيتم تحويلك للمحادثة مباشرة للحصول على الكود.</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # --- المحتوى المفتوح ---
        match_options = [f"{r['التاريخ']} | {r['الوقت']} | {r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()]
        sel_match = st.selectbox("🎯 اختر مباراة للتحليل:", match_options)
        
        if 'curr_match' not in st.session_state or st.session_state['curr_match'] != sel_match:
            safe_stat_update("deep_analysis")
            st.session_state['curr_match'] = sel_match

        match_name = sel_match.split(" | ")[2].split(" ضد ")[0]
        row = df[df['المضيف'] == match_name].iloc[0]

        p1, p2, px = (1/float(row['1'])), (1/float(row['2'])), (1/float(row['X']))
        total_p = p1 + p2 + px
        prob1, probx, prob2 = (p1/total_p)*100, (px/total_p)*100, (p2/total_p)*100
        
        conf = min(int(max(prob1, probx, prob2) + 15), 98)
        xg_base = 1.6 if float(row['أكثر 2.5']) > 2.0 else 2.8
        xh, xa = round(xg_base*(prob1/100)+0.3, 2), round(xg_base*(prob2/100)+0.1, 2)
        
        if conf > 80: advice, color, bg = "🚀 فرصة ذهبية", "#16a34a", "#f0fdf4"
        elif conf > 60: advice, color, bg = "⚖️ استثمار جيد", "#2563eb", "#eff6ff"
        else: advice, color, bg = "⚠️ مباراة خطرة", "#dc2626", "#fef2f2"

        st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة</small><br><span style="font-size:4rem;">{int(round(xh))} - {int(round(xa))}</span></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="advisor-card" style="border-color: {color}; background-color: {bg}; color: {color};">
            <h3 style="margin:0;">💰 {advice}</h3>
            <p style="margin:5px 0;">نسبة الأمان: <b>{conf}%</b> | الاستثمار: <b>{budget*(conf/300):.1f}$</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📋 xG Data")
            st.markdown(f'<div class="stat-box">⚽ {row["المضيف"]}: {xh}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-box">⚽ {row["الضيف"]}: {xa}</div>', unsafe_allow_html=True)
        with col2:
            st.subheader("📊 Win Probability")
            st.bar_chart(pd.DataFrame({'Win %': [prob1, probx, prob2]}, index=[row['المضيف'], 'Draw', row['الضيف']]))

else:
    st.warning("⚠️ لا توجد مباريات متاحة حالياً.")

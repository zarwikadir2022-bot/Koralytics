import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة (تفعيل وضع الهاتف) ---
st.set_page_config(page_title="Koralytics Mobile", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# ⚙️ إعدادات المالك
# ==========================================
OWNER_PHONE = "21600000000"  # ضع رقمك هنا
WHATSAPP_MSG = "مرحباً، أرغب في شراء كود VIP لتطبيق Koralytics 💎"
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

# --- 3. CSS (تصميم خاص للموبايل) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* إعدادات عامة */
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; box-sizing: border-box; }
    .stApp { background-color: #f1f5f9; }
    
    /* إخفاء الهوامش العلوية المزعجة في ستريم ليت للهواتف */
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
    
    /* شريط الأخبار */
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 8px 0; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; font-size: 0.9rem; }
    @keyframes ticker { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    
    /* بطاقة المباراة (متجاوبة للموبايل) */
    .match-card { 
        background: white; border-radius: 15px; padding: 15px; margin-bottom: 12px; 
        border: 1px solid #e2e8f0; border-right: 5px solid #1e3a8a; 
        display: flex; flex-direction: row; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* تعديل البطاقة للشاشات الصغيرة جداً */
    @media (max-width: 480px) {
        .match-card { flex-direction: column; text-align: center; gap: 10px; }
        .match-card > div { width: 100%; }
        .match-info { border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 5px; }
    }
    
    /* الأزرار والبانرات */
    .score-banner { background: #1e3a8a; color: #fbbf24; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(30, 58, 138, 0.3); }
    .stat-box { background: white; padding: 10px; border-radius: 8px; border: 1px solid #ddd; font-size: 0.9rem; text-align: center; font-weight: bold; color: #334155; }
    
    /* زر واتساب الكبير */
    .wa-btn { 
        background: #25D366; color: white !important; width: 100%; display: block;
        padding: 15px; text-align: center; border-radius: 12px; font-weight: bold; 
        text-decoration: none; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(37, 211, 102, 0.4);
        margin-top: 10px;
    }
    
    /* التمويه */
    .blurred-content { filter: blur(5px); opacity: 0.8; pointer-events: none; }
    .lock-overlay { 
        background: rgba(255,255,255,0.95); padding: 20px; border-radius: 20px; 
        text-align: center; border: 1px solid #ccc; margin-top: -160px; position: relative; z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. الشريط العلوي ---
v_total = get_stat_only('unique_visitors') + START_VISITORS
a_total = get_stat_only('deep_analysis') + START_ANALYSIS

st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 20px;">📱 Koralytics Mobile App</span>
    <span style="padding:0 20px;">👤 زوار: {v_total}</span>
    <span style="padding:0 20px;">🎯 تحليلات: {a_total}</span>
    <span style="padding:0 20px;">🇹🇳 {datetime.now().strftime('%H:%M')}</span>
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
            response = requests.get(url, params=params, timeout=4)
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

# --- 6. القائمة الجانبية (Sidebar) ---
st.sidebar.title("⚙️ الإعدادات")

# منطقة تسجيل الدخول VIP
st.sidebar.markdown("### 🔐 منطقة المشتركين")
vip_code_input = st.sidebar.text_input("أدخل كود VIP هنا:", type="password")

# التحقق
admin_code = st.secrets.get("VIP_ACCESS_CODE", "ADMIN")
raw_codes_list = st.secrets.get("VIP_CODES_LIST", "")
valid_codes = [c.strip() for c in raw_codes_list.replace('\n', ',').split(',') if c.strip()]
is_vip = (vip_code_input == admin_code) or (vip_code_input in valid_codes)

if is_vip:
    st.sidebar.success("✅ تم تفعيل العضوية")
else:
    st.sidebar.info("للحصول على الكود، تواصل معنا عبر الزر في الصفحة الرئيسية.")

st.sidebar.markdown("---")
budget = st.sidebar.number_input("💰 رأس المال ($):", 10, 5000, 100)

# اختيار البطولة
try:
    sports_data = []
    for key in VALID_KEYS:
        try:
            req = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={key}', timeout=3)
            if req.status_code == 200:
                sports_data = req.json()
                break
        except: continue

    if sports_data:
        sport_groups = sorted(list(set([s['group'] for s in sports_data])))
        if 'Soccer' in sport_groups: sport_groups.insert(0, sport_groups.pop(sport_groups.index('Soccer')))
        
        sel_group = st.sidebar.selectbox("نوع الرياضة", sport_groups)
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        l_keys = list(l_map.keys())
        # محاولة تحديد بطولة مشهورة افتراضياً
        def_idx = next((i for i, k in enumerate(l_keys) if "Premier League" in k or "La Liga" in k), 0)
        sel_l_name = st.sidebar.selectbox("البطولة", l_keys, index=def_idx)
    else: st.stop()
except: st.stop()

# --- 7. التطبيق الرئيسي ---

# تنبيه للموبايل (يظهر فقط إذا لم يكن VIP)
if not is_vip:
    st.info("👆 اضغط على السهم (>) في الزاوية العلوية لتغيير البطولة أو إدخال كود VIP.")

df = fetch_data_with_rotation(l_map[sel_l_name])

if not df.empty:
    st.markdown(f"### 🔥 مباريات {sel_l_name}")
    
    for _, r in df.iterrows():
        # HTML معدل ليكون متجاوباً (Responsive)
        st.markdown(f"""
        <div class="match-card">
            <div class="match-info">
                <span style="font-size:0.8rem; color:#64748b;">{r["التاريخ"]} {r["الوقت"]}</span><br>
                <b style="font-size:1.1rem; color:#0f172a;">{r["المضيف"]}</b>
                <span style="color:#fbbf24; font-weight:900;"> VS </span>
                <b style="font-size:1.1rem; color:#0f172a;">{r["الضيف"]}</b>
            </div>
            <div style="background:#f8fafc; padding:8px; border-radius:8px; font-weight:bold; font-size:0.9rem; min-width:120px; text-align:center;">
                <span style="color:#16a34a">1: {r["1"]}</span> | 
                <span style="color:#dc2626">2: {r["2"]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("🤖 المختبر الذكي (Pro)")

    if not is_vip:
        # واجهة القفل للموبايل
        st.markdown("""
        <div class="blurred-content">
            <div class="score-banner">3 - 1</div>
            <div class="stat-box">xG Home: 2.45</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="lock-overlay">
            <h3 style="margin:0; color:#1e3a8a;">🔒 المحتوى مغلق</h3>
            <p style="font-size:0.9rem; color:#666;">افتح التحليل الشامل وتوقعات الأهداف.</p>
            <a href="{wa_url}" target="_blank" class="wa-btn">
                واتساب (اشتراك) 📲
            </a>
            <p style="font-size:0.8rem; margin-top:10px; color:#999;">لديك كود؟ اضغط > بالأعلى</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # واجهة التحليل للموبايل
        match_options = [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()]
        sel_match_txt = st.selectbox("اختر المباراة:", match_options)
        
        # ربط الاختيار بالبيانات
        host_team = sel_match_txt.split(" vs ")[0]
        row = df[df['المضيف'] == host_team].iloc[0]

        if 'curr_match' not in st.session_state or st.session_state['curr_match'] != host_team:
            safe_stat_update("deep_analysis")
            st.session_state['curr_match'] = host_team

        # الحسابات
        p1, p2, px = (1/float(row['1'])), (1/float(row['2'])), (1/float(row['X']))
        total_p = p1 + p2 + px
        prob1, probx, prob2 = (p1/total_p)*100, (px/total_p)*100, (p2/total_p)*100
        conf = min(int(max(prob1, probx, prob2) + 18), 99)
        
        xg_base = 1.7 if float(row['أكثر 2.5']) > 1.9 else 2.8
        xh, xa = round(xg_base*(prob1/100)+0.4, 2), round(xg_base*(prob2/100)+0.2, 2)
        
        if conf > 80: color, bg, txt = "#16a34a", "#dcfce7", "فوز مؤكد 🔥"
        elif conf > 60: color, bg, txt = "#2563eb", "#eff6ff", "استثمار جيد ✅"
        else: color, bg, txt = "#dc2626", "#fef2f2", "مخاطرة ⚠️"

        # عرض النتائج بتصميم الموبايل
        st.markdown(f"""
        <div class="score-banner">
            <small>النتيجة المتوقعة</small><br>
            <span style="font-size:3rem; font-weight:bold;">{int(round(xh))} - {int(round(xa))}</span>
        </div>
        <div style="background:{bg}; color:{color}; padding:15px; border-radius:12px; text-align:center; border:2px solid {color}; margin-bottom:15px;">
            <h3 style="margin:0;">{txt}</h3>
            <p style="margin:5px 0 0 0;">نسبة الأمان: <b>{conf}%</b></p>
            <p style="margin:0; font-size:0.9rem;">المبلغ: <b>{budget*(conf/300):.0f}$</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="stat-box">🏠 {row["المضيف"]}<br>{xh} هدف</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-box">✈️ {row["الضيف"]}<br>{xa} هدف</div>', unsafe_allow_html=True)
        
        st.write("")
        st.caption("احتمالات الفوز الرسمية:")
        st.progress(int(prob1))
        st.caption(f"{row['المضيف']} ({int(prob1)}%) - التعادل ({int(probx)}%) - {row['الضيف']} ({int(prob2)}%)")

else:
    st.warning("لا توجد مباريات حالياً.")

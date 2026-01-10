import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة (متجاوبة) ---
st.set_page_config(
    page_title="Koralytics AI", 
    page_icon="💎", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚙️ إعدادات المالك (عدل رقمك هنا)
# ==========================================
OWNER_PHONE = "21694928912" 
WHATSAPP_MSG = "مرحباً، أرغب في شراء كود VIP لتطبيق Koralytics 💎"
wa_url = f"https://wa.me/{OWNER_PHONE}?text={urllib.parse.quote(WHATSAPP_MSG)}"

# --- 2. محرك الإحصائيات ---
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

# --- 3. CSS (إصلاح الظهور للحاسوب والهاتف) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; box-sizing: border-box; }
    .stApp { background-color: #f8fafc; }
    
    /* === 🛠 إصلاح مشكلة اختفاء الشريط === */
    /* في الحاسوب: نزيد المسافة العلوية لكي لا يغطي شريط Streamlit على التصميم */
    .block-container { padding-top: 3.5rem !important; padding-bottom: 5rem !important; }
    
    /* في الهاتف: نقلل المسافة لأن شريط Streamlit يختفي */
    @media (max-width: 768px) {
        .block-container { padding-top: 1rem !important; }
    }
    
    /* تصميم حاوية الشريط */
    .ticker-container {
        background: #fbbf24; padding: 8px 0; border-bottom: 3px solid #000; 
        margin-bottom: 25px; width: 100%; overflow: hidden; white-space: nowrap;
        border-radius: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* === بطاقة المباراة (متجاوبة) === */
    .match-card {
        background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px;
        border: 1px solid #e2e8f0; border-right: 5px solid #1e3a8a;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .match-teams { flex: 2; min-width: 200px; }
    .match-odds { flex: 1; min-width: 180px; }
    
    .odds-badge {
        background: #f1f5f9; padding: 10px; border-radius: 8px;
        font-weight: bold; font-size: 0.9rem; text-align: center;
        display: flex; justify-content: space-between;
        border: 1px solid #cbd5e1;
    }

    /* === شبكة الإحصائيات (Grid) === */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    
    .stat-box {
        background: white; padding: 15px; border-radius: 12px;
        border: 1px solid #e2e8f0; text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        transition: transform 0.2s;
    }
    .stat-box:hover { transform: translateY(-3px); border-color: #fbbf24; }
    
    .stat-title { font-size: 0.85rem; color: #64748b; margin-bottom: 5px; display: block; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #1e3a8a; }

    /* === تعديلات خاصة للموبايل فقط === */
    @media (max-width: 768px) {
        .match-card { flex-direction: column; text-align: center; gap: 10px; }
        .match-teams { width: 100%; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 0; }
        .match-odds { width: 100%; }
        .score-banner span { font-size: 2.5rem !important; }
    }

    /* المستشار والقفل */
    .advisor-box { padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 2px solid; }
    .blurred-content { filter: blur(8px); opacity: 0.6; pointer-events: none; }
    .lock-overlay {
        background: rgba(255,255,255,0.95); padding: 30px; border-radius: 20px;
        text-align: center; border: 1px solid #ccc; margin-top: -280px; position: relative; z-index: 100;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        max-width: 500px; margin-left: auto; margin-right: auto;
    }
    .wa-btn {
        background: #25D366; color: white !important; display: inline-block; width: 100%; max-width: 300px;
        padding: 12px; border-radius: 50px; font-weight: bold; text-decoration: none; margin-top: 15px;
        box-shadow: 0 4px 10px rgba(37, 211, 102, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. الشريط المتحرك (Ticker) ---
v_total = get_stat_only('unique_visitors') + START_VISITORS
a_total = get_stat_only('deep_analysis') + START_ANALYSIS
t_text = f"💎 Koralytics AI • 👤 زوار: {v_total} • 🎯 تحليلات: {a_total} • 🇹🇳 {datetime.now().strftime('%H:%M')} • 🔥 التحليل الذكي للمباريات"

st.markdown(f"""
<div class="ticker-container">
    <marquee direction="right" scrollamount="6" behavior="scroll" 
             style="font-weight:bold; font-size:1rem; color:#000; font-family:'Cairo'; padding-top:4px;">
        {t_text}
    </marquee>
</div>
""", unsafe_allow_html=True)

# --- 5. المنطق الخلفي (Logic) ---
ALL_KEYS = [st.secrets.get(f"KEY{i}") for i in range(1, 11)]
VALID_KEYS = [k for k in ALL_KEYS if k is not None]

def fetch_data(l_key):
    for api_key in VALID_KEYS:
        try:
            url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
            params = {'apiKey': api_key, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
            r = requests.get(url, params=params, timeout=4)
            if r.status_code == 200: return process(r.json())
        except: continue
    return pd.DataFrame()

def process(r):
    res = []
    for m in r:
        if not m.get('bookmakers'): continue
        mkts = m['bookmakers'][0].get('markets', [])
        h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
        totals = next((i for i in mkts if i['key'] == 'totals'), None)
        if h2h:
            dt = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
            over = totals['outcomes'][0]['price'] if totals and len(totals['outcomes']) > 1 else 1.85
            oc = h2h['outcomes']
            # التعامل مع الحالات التي لا يوجد فيها تعادل (مثل السلة)
            px = oc[2]['price'] if len(oc) > 2 else 1.0
            
            res.append({
                "المضيف": m['home_team'], "الضيف": m['away_team'],
                "التاريخ": dt.strftime("%d/%m %H:%M"), 
                "1": oc[0]['price'], "2": oc[1]['price'], 
                "X": px, "أكثر 2.5": over
            })
    return pd.DataFrame(res)

# --- 6. القائمة الجانبية ---
st.sidebar.title("⚙️ الإعدادات")
st.sidebar.markdown("### 🔐 منطقة المشتركين")
vip_in = st.sidebar.text_input("كود التفعيل:", type="password")

# التحقق
admin = st.secrets.get("VIP_ACCESS_CODE", "ADMIN")
codes = [c.strip() for c in st.secrets.get("VIP_CODES_LIST", "").replace('\n', ',').split(',') if c.strip()]
is_vip = (vip_in == admin) or (vip_in in codes)

if is_vip: st.sidebar.success("✅ العضوية مفعلة")
else: st.sidebar.info("تصفح المباريات بالأسفل 👇")

st.sidebar.markdown("---")
budget = st.sidebar.number_input("💰 الميزانية ($):", 10, 10000, 100)

# جلب البطولات
try:
    s_data = []
    for k in VALID_KEYS:
        try:
            req = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={k}', timeout=3)
            if req.status_code == 200: s_data = req.json(); break
        except: continue
    
    if s_data:
        grps = sorted(list(set([s['group'] for s in s_data])))
        if 'Soccer' in grps: grps.insert(0, grps.pop(grps.index('Soccer')))
        s_grp = st.sidebar.selectbox("الرياضة", grps)
        l_map = {s['title']: s['key'] for s in s_data if s['group'] == s_grp}
        def_idx = next((i for i, k in enumerate(l_map.keys()) if "Premier League" in k or "La Liga" in k), 0)
        sel_l = st.sidebar.selectbox("البطولة", list(l_map.keys()), index=def_idx)
    else: st.stop()
except: st.stop()

# --- 7. العرض الرئيسي ---
df = fetch_data(l_map[sel_l])

if not df.empty:
    st.markdown(f"### 🔥 {sel_l}")
    
    # === بطاقات المباريات (متجاوبة) ===
    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="match-card">
            <div class="match-teams">
                <div style="font-size:0.8rem; color:#64748b; margin-bottom:4px;">📅 {r["التاريخ"]}</div>
                <div style="font-size:1.1rem; font-weight:bold; color:#0f172a;">
                    {r["المضيف"]} <span style="color:#fbbf24; padding:0 5px;">VS</span> {r["الضيف"]}
                </div>
            </div>
            <div class="match-odds">
                <div class="odds-badge">
                    <span style="color:#16a34a">1: {r["1"]}</span>
                    <span style="color:#64748b">X: {r["X"]}</span>
                    <span style="color:#dc2626">2: {r["2"]}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("🤖 التحليل الذكي (Pro)")

    # === قسم التحليل ===
    if is_vip:
        opts = [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()]
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل:", opts)
        row = df[df['المضيف'] == sel_m.split(" vs ")[0]].iloc[0]

        if 'curr_m' not in st.session_state or st.session_state['curr_m'] != row['المضيف']:
            safe_stat_update("deep_analysis")
            st.session_state['curr_m'] = row['المضيف']

        # الحسابات
        p1, p2, px = (1/float(row['1'])), (1/float(row['2'])), (1/float(row['X']))
        tot = p1 + p2 + px
        pr1, prx, pr2 = (p1/tot)*100, (px/tot)*100, (p2/tot)*100
        
        xg_b = 1.7 if float(row['أكثر 2.5']) > 1.9 else 2.9
        xh, xa = round(xg_b*(pr1/100)+0.4, 2), round(xg_b*(pr2/100)+0.2, 2)
        ch, ca = round(1.5+(pr2/100)*2.5, 1), round(1.5+(pr1/100)*2.5, 1)
        
        conf = min(int(max(pr1, prx, pr2) + 18), 99)
        if conf > 80: clr, bg, txt = "#16a34a", "#dcfce7", "فرصة ذهبية 🔥"
        elif conf > 60: clr, bg, txt = "#2563eb", "#eff6ff", "استثمار جيد ✅"
        else: clr, bg, txt = "#dc2626", "#fef2f2", "مخاطرة عالية ⚠️"

        # عرض النتائج
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:20px;" class="score-banner">
            <span style="font-size:4rem; font-weight:bold; color:#1e3a8a;">{int(round(xh))} - {int(round(xa))}</span>
            <br><small style="color:#64748b;">النتيجة المتوقعة</small>
        </div>
        <div class="advisor-box" style="border-color:{clr}; background:{bg}; color:{clr};">
            <h3 style="margin:0;">{txt}</h3>
            <p style="margin:5px 0;">نسبة الأمان: <b>{conf}%</b></p>
            <p style="margin:0;">الاستثمار المقترح: <b>{budget*(conf/300):.0f}$</b></p>
        </div>
        """, unsafe_allow_html=True)

        # شبكة الإحصائيات (تتجاوب تلقائياً)
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-box"><span class="stat-title">⚽ أهداف {row['المضيف']}</span><span class="stat-value">{xh}</span></div>
            <div class="stat-box"><span class="stat-title">⚽ أهداف {row['الضيف']}</span><span class="stat-value">{xa}</span></div>
            <div class="stat-box"><span class="stat-title">🟨 بطاقات {row['المضيف']}</span><span class="stat-value">{ch}</span></div>
            <div class="stat-box"><span class="stat-title">🟨 بطاقات {row['الضيف']}</span><span class="stat-value">{ca}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.subheader("📊 نسب الفوز")
        st.bar_chart(pd.DataFrame({'%': [pr1, prx, pr2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]), color="#1e3a8a")

    else:
        # لغير المشتركين (شاشة القفل)
        st.markdown("""
        <div class="blurred-content">
            <div class="advisor-box">💰 استثمار: 50$</div>
            <div class="stat-grid">
                <div class="stat-box">Home: 2.1</div><div class="stat-box">Away: 1.0</div>
                <div class="stat-box">Cards: 3</div><div class="stat-box">Cards: 2</div>
            </div>
        </div>
        <div class="lock-overlay">
            <h2 style="color:#1e3a8a;">💎 محتوى VIP</h2>
            <p style="color:#555;">التحليل الشامل + البطاقات + المستشار المالي</p>
            <a href="{}" target="_blank" class="wa-btn">فتح الاشتراك (واتساب)</a>
        </div>
        """.format(wa_url), unsafe_allow_html=True)

else:
    st.warning("⚠️ لا توجد مباريات متاحة.")

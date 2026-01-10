import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة (مخصص للموبايل) ---
st.set_page_config(page_title="Koralytics Mobile", page_icon="📱", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# ⚙️ إعدادات المالك (هام: عدل رقمك هنا)
# ==========================================
OWNER_PHONE = "21694928912"  # ضع رقمك بدون علامة +
WHATSAPP_MSG = "مرحباً، أرغب في شراء كود VIP لتطبيق Koralytics 💎"
wa_url = f"https://wa.me/{OWNER_PHONE}?text={urllib.parse.quote(WHATSAPP_MSG)}"

# --- 2. محرك الإحصائيات (الثابت) ---
# الأرقام الأساسية لمنع التصفير
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

# تسجيل الزيارة مرة واحدة للجلسة
if 'session_tracked' not in st.session_state:
    safe_stat_update("unique_visitors")
    st.session_state['session_tracked'] = True

# --- 3. CSS (تصميم الموبايل المحسن + Grid) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; box-sizing: border-box; }
    .stApp { background-color: #f8fafc; }
    /* إزالة الحواف الزائدة للموبايل */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 5rem !important; }
    
    /* تصميم حاوية الشريط المتحرك */
    .ticker-container {
        background: #fbbf24; 
        padding: 8px 0; 
        border-bottom: 3px solid #000; 
        margin-bottom: 15px;
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
    }
    
    /* بطاقة المباراة */
    .match-card { 
        background: white; border-radius: 12px; padding: 12px; margin-bottom: 10px; 
        border: 1px solid #e2e8f0; border-right: 5px solid #1e3a8a; 
        display: flex; flex-direction: column; gap:8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* شبكة الإحصائيات (Grid System) - الحل لمشكلة الاختفاء */
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
    
    .stat-box { 
        background: white; padding: 10px; border-radius: 10px; 
        border: 1px solid #e2e8f0; text-align: center; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stat-title { font-size: 0.75rem; color: #64748b; display: block; margin-bottom: 5px; }
    .stat-value { font-size: 1.1rem; font-weight: bold; color: #1e3a8a; }
    
    /* المستشار */
    .advisor-box { padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; border: 2px solid; }
    
    /* القفل والتمويه */
    .blurred-content { filter: blur(6px); opacity: 0.7; pointer-events: none; }
    .lock-overlay { 
        background: rgba(255,255,255,0.95); padding: 20px; border-radius: 20px; 
        text-align: center; border: 1px solid #ccc; margin-top: -220px; position: relative; z-index: 100;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
    }
    
    .wa-btn { 
        background: #25D366; color: white !important; width: 100%; display: block;
        padding: 12px; text-align: center; border-radius: 10px; font-weight: bold; 
        text-decoration: none; margin-top: 10px; font-size: 1rem;
        box-shadow: 0 4px 6px rgba(37, 211, 102, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. الشريط العلوي (Marquee) ---
v_total = get_stat_only('unique_visitors') + START_VISITORS
a_total = get_stat_only('deep_analysis') + START_ANALYSIS

# النصوص
t1 = f"💎 Koralytics Mobile: خيارك الأول للتحليل الذكي"
t2 = f"👤 زوار: {v_total}"
t3 = f"🎯 تحليلات: {a_total}"
t4 = f"🇹🇳 توقيت تونس {datetime.now().strftime('%H:%M')}"
t5 = "🔥 اشترك الآن واحصل على التوقعات كاملة"

# استخدام Marquee بدلاً من CSS Ticker لضمان العمل على الموبايل
st.markdown(f"""
<div class="ticker-container">
    <marquee direction="right" scrollamount="5" behavior="scroll" 
             style="font-weight:bold; font-size:0.9rem; color:#000; font-family:'Cairo'; line-height: 1.5;">
        <span style="margin:0 15px;">{t1}</span> • 
        <span style="margin:0 15px;">{t2}</span> • 
        <span style="margin:0 15px;">{t3}</span> • 
        <span style="margin:0 15px;">{t4}</span> • 
        <span style="margin:0 15px; color:#dc2626;">{t5}</span>
    </marquee>
</div>
""", unsafe_allow_html=True)

# --- 5. محرك المفاتيح (Rotation) ---
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
            # التعامل مع احتمالية عدم وجود تعادل (مثل كرة السلة)
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

# --- 6. القائمة الجانبية (Settings & VIP) ---
st.sidebar.title("⚙️ الإعدادات")

st.sidebar.markdown("### 🔐 منطقة المشتركين")
vip_code_input = st.sidebar.text_input("أدخل كود VIP:", type="password")

# التحقق من الأكواد
admin_code = st.secrets.get("VIP_ACCESS_CODE", "ADMIN")
raw_codes = st.secrets.get("VIP_CODES_LIST", "")
valid_codes = [c.strip() for c in raw_codes.replace('\n', ',').split(',') if c.strip()]
is_vip = (vip_code_input == admin_code) or (vip_code_input in valid_codes)

if is_vip:
    st.sidebar.success("✅ العضوية مفعلة")
else:
    st.sidebar.info("تصفح المباريات، واضغط على القفل للاشتراك.")

st.sidebar.markdown("---")
budget = st.sidebar.number_input("💰 رأس المال ($):", 10, 10000, 100)

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
        
        sel_group = st.sidebar.selectbox("الرياضة", sport_groups)
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        l_keys = list(l_map.keys())
        # تحديد بطولة افتراضية
        idx = next((i for i, k in enumerate(l_keys) if "Premier League" in k or "La Liga" in k), 0)
        sel_l_name = st.sidebar.selectbox("البطولة", l_keys, index=idx)
    else: st.stop()
except: st.stop()

# --- 7. التطبيق الرئيسي ---

# تنبيه للمستخدمين الجدد
if not is_vip:
    st.info("👆 اضغط (>) بالأعلى لتسجيل الدخول أو تغيير البطولة")

df = fetch_data_with_rotation(l_map[sel_l_name])

if not df.empty:
    st.markdown(f"### 🔥 {sel_l_name}")
    
    # عرض البطاريات
    for _, r in df.iterrows():
        st.markdown(f"""
        <div class="match-card">
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:#64748b;">
                <span>{r["التاريخ"]}</span><span>{r["الوقت"]}</span>
            </div>
            <div style="text-align:center; font-weight:bold; font-size:1.1rem;">
                {r["المضيف"]} <span style="color:#fbbf24">VS</span> {r["الضيف"]}
            </div>
            <div style="display:flex; justify-content:space-between; background:#f1f5f9; padding:5px; border-radius:5px; font-size:0.9rem;">
                <span style="color:#16a34a">1: {r["1"]}</span>
                <span style="color:#64748b">X: {r["X"]}</span>
                <span style="color:#dc2626">2: {r["2"]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.header("🤖 التحليل الذكي (Pro)")

    if not is_vip:
        # === واجهة القفل (مموّهة) ===
        st.markdown("""
        <div class="blurred-content">
            <div class="advisor-box">💰 استثمار: 50$</div>
            <div class="stat-grid">
                <div class="stat-box">⚽ Home: 2.1</div>
                <div class="stat-box">🟨 Cards: 3</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="lock-overlay">
            <h3 style="color:#1e3a8a;">🔒 محتوى VIP مغلق</h3>
            <p style="font-size:0.9rem; color:#555;">افتح التوقعات الشاملة + البطاقات + الرسم البياني</p>
            <a href="{wa_url}" target="_blank" class="wa-btn">اشترك الآن عبر واتساب 📲</a>
            <p style="font-size:0.75rem; color:#888; margin-top:10px;">لديك الكود؟ أدخله في القائمة الجانبية</p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # === واجهة التحليل الكاملة (VIP) ===
        match_options = [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()]
        sel_match_txt = st.selectbox("اختر المباراة:", match_options)
        
        # استخراج البيانات
        host_team = sel_match_txt.split(" vs ")[0]
        row = df[df['المضيف'] == host_team].iloc[0]

        # تحديث العداد
        if 'curr_match' not in st.session_state or st.session_state['curr_match'] != host_team:
            safe_stat_update("deep_analysis")
            st.session_state['curr_match'] = host_team

        # الخوارزمية
        p1, p2, px = (1/float(row['1'])), (1/float(row['2'])), (1/float(row['X']))
        total = p1 + p2 + px
        prob1, probx, prob2 = (p1/total)*100, (px/total)*100, (p2/total)*100
        
        xg_base = 1.7 if float(row['أكثر 2.5']) > 1.9 else 2.9
        xh, xa = round(xg_base*(prob1/100)+0.4, 2), round(xg_base*(prob2/100)+0.2, 2)
        
        # خوارزمية البطاقات (كلما زاد احتمال الخسارة، زاد التوتر والبطاقات)
        ch = round(1.5 + (prob2/100)*2.5, 1) # بطاقات المضيف
        ca = round(1.5 + (prob1/100)*2.5, 1) # بطاقات الضيف
        
        conf = min(int(max(prob1, probx, prob2) + 18), 99)
        if conf > 80: color, bg, txt = "#16a34a", "#dcfce7", "فرصة ذهبية 🔥"
        elif conf > 60: color, bg, txt = "#2563eb", "#eff6ff", "استثمار جيد ✅"
        else: color, bg, txt = "#dc2626", "#fef2f2", "مخاطرة عالية ⚠️"

        # 1. النتيجة والمستشار
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:15px;">
            <span style="font-size:3.5rem; font-weight:bold; color:#1e3a8a;">{int(round(xh))} - {int(round(xa))}</span>
            <br><small style="color:#64748b;">النتيجة المتوقعة</small>
        </div>
        <div class="advisor-box" style="border-color:{color}; background:{bg}; color:{color};">
            <h3 style="margin:0;">{txt}</h3>
            <p style="margin:5px 0;">نسبة الأمان: <b>{conf}%</b></p>
            <p style="margin:0;">استثمر: <b>{budget*(conf/300):.0f}$</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. شبكة الإحصائيات (الأهداف والبطاقات)
        st.markdown('<div class="stat-grid">', unsafe_allow_html=True)
        
        # الصف 1: الأهداف
        st.markdown(f"""
        <div class="stat-box">
            <span class="stat-title">⚽ أهداف {row['المضيف']}</span>
            <span class="stat-value">{xh}</span>
        </div>
        <div class="stat-box">
            <span class="stat-title">⚽ أهداف {row['الضيف']}</span>
            <span class="stat-value">{xa}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # الصف 2: البطاقات
        st.markdown(f"""
        <div class="stat-box" style="border-bottom: 3px solid #eab308;">
            <span class="stat-title">🟨 بطاقات {row['المضيف']}</span>
            <span class="stat-value">{ch}</span>
        </div>
        <div class="stat-box" style="border-bottom: 3px solid #eab308;">
            <span class="stat-title">🟨 بطاقات {row['الضيف']}</span>
            <span class="stat-value">{ca}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. الرسم البياني
        st.write("")
        st.subheader("📊 نسب الفوز")
        chart_df = pd.DataFrame(
            {'Percentage': [prob1, probx, prob2]}, 
            index=[row['المضيف'], 'تعادل', row['الضيف']]
        )
        st.bar_chart(chart_df, color="#1e3a8a")

else:
    st.warning("لا توجد مباريات متاحة حالياً.")

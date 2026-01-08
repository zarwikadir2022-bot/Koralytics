import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Diamond Edition", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات (المحصن) ---
def safe_stat_update(feat):
    fn = f"stat_{feat}.txt"
    try:
        # إنشاء الملف إذا لم يكن موجوداً
        if not os.path.exists(fn):
            with open(fn, "w") as f: f.write("0")
            current = 0
        else:
            with open(fn, "r") as f:
                content = f.read().strip()
                current = int(content) if content else 0
        
        new_val = current + 1
        with open(fn, "w") as f: f.write(str(new_val))
        return new_val
    except: return 0 # في حال حدوث خطأ نادر، لا توقف الموقع

def get_stat_only(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn): return 0
    try:
        with open(fn, "r") as f: return int(f.read().strip())
    except: return 0

# تسجيل الزيارة مرة واحدة فقط لكل جلسة متصفح (Session)
if 'session_tracked' not in st.session_state:
    safe_stat_update("unique_visitors")
    st.session_state['session_tracked'] = True

# --- 3. التصميم البصري (CSS متجاوب) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .stApp { background: #f8fafc; }
    
    /* شريط متحرك انسيابي */
    .ticker-wrap { width: 100%; overflow: hidden; background: #fbbf24; padding: 12px 0; border-bottom: 3px solid #000; margin-bottom: 25px; }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; font-weight: bold; color: #000; font-size: 1.1rem; }
    @keyframes ticker { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
    
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; border-right: 6px solid #1e3a8a; transition: 0.3s; }
    .match-card:hover { border-right-width: 10px; background: #f1f5f9; }
    
    .score-banner { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #fbbf24; padding: 30px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .stat-box { background: white; padding: 12px; border-radius: 10px; border-right: 6px solid #1e3a8a; margin-bottom: 10px; border: 1px solid #e2e8f0; font-weight: bold; color: #1e3a8a; }
    
    /* صندوق المستشار المالي الديناميكي */
    .advisor-card { padding: 20px; border-radius: 15px; text-align: center; font-weight: bold; border: 2px solid; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. الشريط العلوي ---
v_total = get_stat_only('unique_visitors')
a_total = get_stat_only('deep_analysis')
st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
    <span style="padding:0 50px;">🇹🇳 توقيت تونس (GMT+1) | الزوار: {v_total} 💎</span>
    <span style="padding:0 50px;">🎯 التحليلات: {a_total} | كأس أمم أفريقيا: متابعة خاصة للقمم العربية</span>
    <span style="padding:0 50px;">🚀 Koralytics AI: الذكاء الاصطناعي في خدمة المشجع التونسي</span>
</div></div>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات (مع معالجة الأخطاء) ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=300)
def fetch_data(l_key):
    try:
        # إضافة timeout لمنع تعليق الموقع
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'},
                         timeout=8).json()
        res = []
        for m in r:
            # حماية من المباريات الفارغة
            if not m.get('bookmakers'): continue
            
            mkts = m['bookmakers'][0].get('markets', [])
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            
            if h2h:
                dt = datetime.strptime(m['commence_time'], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=1)
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "التاريخ": dt.strftime("%d/%m"), "الوقت": dt.strftime("%H:%M"),
                    "1": h2h['outcomes'][0]['price'], 
                    "

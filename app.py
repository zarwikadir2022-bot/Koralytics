import streamlit as st
import pandas as pd
import requests
import os
import numpy as np

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Platinum Pro", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم ---
def update_stat_file(feature_name):
    filename = f"stat_{feature_name}.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f: f.write("0")
    with open(filename, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(filename, "w") as f: f.write(str(count))
    return count

def get_stat_file(feature_name):
    filename = f"stat_{feature_name}.txt"
    if not os.path.exists(filename): return 0
    with open(filename, "r") as f:
        try: return int(f.read())
        except: return 0

# --- 3. التصميم البلاتيني الكريستالي المطور ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    
    /* بطاقة المباراة الاحترافية */
    .match-card {
        background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(15px);
        border-radius: 18px; padding: 20px; margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.7);
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 8px 8px 16px rgba(0,0,0,0.05), -4px -4px 12px rgba(255,255,255,0.5);
    }
    .odd-badge {
        background: linear-gradient(145deg, #ffffff, #e6e6e6);
        padding: 8px 16px; border-radius: 10px; font-weight: bold;
        box-shadow: 4px 4px 8px #d1d1d1, -4px -4px 8px #ffffff;
    }
    /* التحليل العميق الكريستالي */
    .crystal-card { 
        background: rgba(255, 255, 255, 0.5); backdrop-filter: blur(20px); 
        border-radius: 25px; padding: 35px; border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 15px 15px 30px rgba(0, 0, 0, 0.1), inset 0 0 15px rgba(255,255,255,0.5);
        margin-top: 30px;
    }
    .ai-stat-box {
        background: rgba(255, 255, 255, 0.8); border-right: 8px solid #2c3e50;
        padding: 20px; border-radius: 15px; margin-bottom: 15px;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. محرك الحسابات المتقدم (AI Analytics) ---
def get_advanced_metrics(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        # احتمالات الفوز
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        # توقع الأهداف (xG)
        prob_u = (1/row['أقل 2.5']) / ((1/row['أكثر 2.5']) + (1/row['أقل 2.5']))
        xg = 1.8 if prob_u > 0.6 else 3.6 if prob_u < 0.3 else 2.5
        # توقع النتيجة الدقيقة (تبسيطي)
        score = "2-1" if p1 > 50 else "1-1" if px > 30 else "1-2"
        return {"p1": p1, "px": px, "p2": p2, "xg": xg, "score": score, "conf": min(int(p1 + xg*5), 96)}
    except: return None

# --- 5. جلب البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json()[:15]: # أول 15 مباراة لسرعة العرض
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'],
                    "أكثر 2.5": totals['outcomes'][0]['price'], "أقل 2.5": totals['outcomes'][1]['price']
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    if 'init' not in st.session_state:
        st.session_state['v_count'] = update_stat_file("unique_visitors")
        st.session_state['init'] = True
    
    st.sidebar.markdown(f'<div style="text-align:center; padding:20px; background:white; border-radius:20px; box-shadow: 5px 5px 15px #bbb;">الزوار 👥<br><b style="font-size:25px;">{get_stat_file("unique_visitors")}</b></div>', unsafe_allow_html=True)
    st.sidebar.write(f"🪄 عصا سحرية: **{get_stat_file('magic_wand')}**")
    st.sidebar.write(f"🎯 تحليل عميق: **{get_stat_file('deep_analysis')}**")

    try:
        sports_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in sports_raw if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    except: st.error("خطأ في الاتصال"); return

    st.title(f"💎 Koralytics AI: {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # عرض المباريات
        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="font-size: 1.2rem; font-weight: bold;">{r['المضيف']} <span style="color:#888;">vs</span> {r['الضيف']}</div>
                <div><span class="odd-badge">1: {r['1']}</span> <span class="odd-badge">X: {r['X']}</span> <span class="odd-badge">2: {r['2']}</span></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        st.header("🔬 مختبر التحليل البلاتيني")
        sel_m = st.selectbox("🎯 اختر مباراة لتحليلها بالذكاء الاصطناعي:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        # تحديث عداد التحليل
        if 'last_a' not in st.session_state or st.session_state['last_a'] != sel_m:
            update_stat_file("deep_analysis")
            st.session_state['last_a'] = sel_m

        m = get_advanced_metrics(row)
        if m:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="ai-stat-box">📈 احتمالية الفوز<br><b style="font-size:22px;">{m["p1"]:.1f}%</b></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="ai-stat-box">🥅 معدل الأهداف xG<br><b style="font-size:22px;">{m["xg"]:.2f}</b></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="ai-stat-box">🎯 النتيجة المتوقعة<br><b style="font-size:22px;">{m["score"]}</b></div>', unsafe_allow_html=True)
            
            st.progress(m['conf']/100, text=f"مؤشر ثقة الخوارزمية: {m['conf']}%")
            
            st.markdown("---")
            st.subheader("📊 توزيع القوة الهجومية")
            st.bar_chart(pd.DataFrame({'%': [m['p1'], m['px'], m['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

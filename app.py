import streamlit as st
import pandas as pd
import requests
import os
import numpy as np

# --- 1. إعدادات الصفحة الفاخرة ---
st.set_page_config(page_title="Koralytics AI | Ultimate Platinum", page_icon="💎", layout="wide")

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

# --- 3. التصميم الإمبراطوري (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    
    .match-card {
        background: rgba(255, 255, 255, 0.45); backdrop-filter: blur(10px);
        border-radius: 15px; padding: 15px; margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        display: flex; justify-content: space-between; align-items: center;
    }
    .odd-badge {
        background: rgba(255, 255, 255, 0.8); padding: 5px 12px; border-radius: 8px; 
        font-weight: bold; margin-left: 5px; border: 1px solid #ddd;
    }
    .crystal-card { 
        background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); 
        border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px;
    }
    .ai-box { background: white; padding: 15px; border-radius: 12px; border-right: 6px solid #2c3e50; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 4. محرك الحسابات الإحصائية الشامل ---
def calculate_all_metrics(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        
        # ميزات التحليل المفقودة
        tightness = 1 - abs((p1/100) - (p2/100))
        h_cards = round(1.3 + (tightness * 1.5), 1)
        a_cards = round(1.5 + (tightness * 1.5), 1)
        red_p = int((tightness * 22) + 8)
        
        prob_u = (1/row['أقل 2.5']) / ((1/row['أكثر 2.5']) + (1/row['أقل 2.5']))
        xg = 1.9 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
        
        score = "2-1" if p1 > 45 else "0-0" if px > 35 else "1-2"
        conf = min(int(p1 + xg*5), 94)
        
        return {"p1": p1, "px": px, "p2": p2, "hc": h_cards, "ac": a_cards, "rp": red_p, "xg": xg, "score": score, "conf": conf}
    except: return None

# --- 5. جلب البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
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
    if 'is_v' not in st.session_state:
        st.session_state['v_num'] = update_stat_file("unique_visitors")
        st.session_state['is_v'] = True
    
    # القائمة الجانبية المحدثة
    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f'<div style="background:white; padding:10px; border-radius:10px; text-align:center; border:1px solid #ddd;">الزوار الفريدون 👤 <b>{get_stat_file("unique_visitors")}</b></div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"**🪄 العصا:** {get_stat_file('magic_wand')} | **🎯 التحليل:** {get_stat_file('deep_analysis')}")
    st.sidebar.markdown("---")

    try:
        sports_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in sports_raw if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 ميزانية المحفظة ($):", 10, 5000, 500)
    except: st.error("خطأ في البيانات"); return

    st.title(f"🏟️ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # عرض المباريات
        for _, r in df.iterrows():
            st.markdown(f"""<div class="match-card">
                <div style="font-weight: bold;">{r['المضيف']} vs {r['الضيف']}</div>
                <div><span class="odd-badge">1: {r['1']}</span><span class="odd-badge">X: {r['X']}</span><span class="odd-badge">2: {r['2']}</span></div>
            </div>""", unsafe_allow_html=True)

        # التحليل الشامل الموعود
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        st.header("🔬 مختبر التحليل الإحصائي العميق")
        sel_m = st.selectbox("🎯 اختر مباراة لتحليل كافة ميزاتها:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
            update_stat_file("deep_analysis")
            st.session_state['last_m'] = sel_m

        m = calculate_all_metrics(row)
        if m:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("💰 المستشار المالي")
                stake = st.number_input("الرهان ($):", 1, 1000, 10)
                st.metric("الربح الصافي المتوقع", f"{(stake*row['1'] - stake):.2f}$")
                st.info(f"💡 نصيحة الخبراء: استثمر **{(budget * (m['p1']/100) * 0.05):.1f}$**")
                st.markdown(f'<div style="background:#2c3e50; color:#f1c40f; padding:15px; border-radius:10px; text-align:center;">النتيجة المتوقعة<br><b style="font-size:24px;">{m["score"]}</b></div>', unsafe_allow_html=True)

            with col2:
                st.subheader("📊 الذكاء الاصطناعي (Full Metrics)")
                st.markdown(f"""
                <div class="ai-box"><b>الاحتمالات:</b> فوز {row['المضيف']} ({m['p1']:.1f}%) | تعادل ({m['px']:.1f}%) | فوز {row['الضيف']} ({m['p2']:.1f}%)</div>
                <div class="ai-box"><b>رادار البطاقات:</b> 🟨 للأرض {m['hc']} | 🟨 للضيف {m['ac']} | 🟥 احتمالية طرد {m['rp']}%</div>
                <div class="ai-box"><b>الأهداف المتوقعة:</b> معدل {m['xg']:.2f} أهداف (xG)</div>
                """, unsafe_allow_html=True)
                
                st.progress(m['conf']/100, text=f"🎯 مؤشر ثقة التوقع: {m['conf']}%")
                st.bar_chart(pd.DataFrame({'%': [m['p1'], m['px'], m['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

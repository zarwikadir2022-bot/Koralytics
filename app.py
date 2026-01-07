import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Ultimate Tunisia", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات ---
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

# --- 3. محرك توقيت تونس (GMT+1) ---
def get_tn_time(utc_time_str):
    try:
        dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        tn_time = dt + timedelta(hours=1)
        return tn_time.strftime("%d/%m | %H:%M")
    except: return "قريباً"

# --- 4. التصميم البلاتيني ---
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
    .time-badge { background: #2c3e50; color: #f1c40f; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; }
    .magic-box { background: linear-gradient(135deg, #2c3e50 0%, #000000 100%); color: #f1c40f; padding: 20px; border-radius: 15px; margin-bottom: 20px; border-right: 8px solid #f1c40f; }
    .crystal-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-top: 20px; }
    .ai-box { background: white; padding: 12px; border-radius: 10px; border-right: 5px solid #2c3e50; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات والحسابات ---
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
                    "المضيف": m['home_team'], "الضيف": m['away_team'], "التوقيت": get_tn_time(m['commence_time']),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'], "X": h2h['outcomes'][2]['price'],
                    "أكثر 2.5": totals['outcomes'][0]['price'], "أقل 2.5": totals['outcomes'][1]['price']
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

def calculate_all(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        tight = 1 - abs((p1/100) - (p2/100))
        h_c, a_c = round(1.3 + tight*1.5, 1), round(1.5 + tight*1.5, 1)
        xg = 1.9 if (1/row['أقل 2.5']) > 0.5 else 3.1
        score = "2-1" if p1 > 45 else "1-1" if px > 35 else "1-2"
        return {"p1":p1, "px":px, "p2":p2, "hc":h_c, "ac":a_c, "rp":int(tight*25+5), "xg":xg, "score":score}
    except: return None

# --- 6. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        st.session_state['v_num'] = update_stat_file("unique_visitors")
        st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"**👤 الزوار:** {get_stat_file('unique_visitors')} | **🪄 العصا:** {get_stat_file('magic_wand')} | **🎯 التحليل:** {get_stat_file('deep_analysis')}")

    try:
        sports = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        l_map = {s['title']: s['key'] for s in sports if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 المحفظة ($):", 10, 5000, 500)
    except: st.error("خطأ بيانات"); return

    st.title(f"🏟️ {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # زر العصا السحرية
        if st.button("🪄 تفعيل العصا السحرية"):
            update_stat_file("magic_wand")
            st.session_state['magic'] = True
        
        if st.session_state.get('magic'):
            best = df.nsmallest(3, '1')
            st.markdown('<div class="magic-box"><h4>🪄 أفضل التوقعات:</h4>', unsafe_allow_html=True)
            for _, r in best.iterrows(): st.write(f"✅ **{r['المضيف']}** | أودز: {r['1']}")
            st.markdown('</div>', unsafe_allow_html=True)

        for _, r in df.iterrows():
            st.markdown(f'<div class="match-card"><div><span class="time-badge">🕒 {r["التوقيت"]}</span><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div><span class="odd-badge">1: {r["1"]}</span> <span class="odd-badge">X: {r["X"]}</span> <span class="odd-badge">2: {r["2"]}</span></div></div>', unsafe_allow_html=True)

        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        st.header("📊 مركز التحليل العميق")
        sel_m = st.selectbox("🎯 اختر مباراة:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_a' not in st.session_state or st.session_state['last_a'] != sel_m:
            update_stat_file("deep_analysis")
            st.session_state['last_a'] = sel_m

        s = calculate_all(row)
        if s:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("💰 استثمار")
                st.metric("النتيجة المتوقعة", s['score'])
                st.info(f"💡 استثمر: **{(budget * 0.05):.1f}$**")
            with c2:
                st.subheader("📊 الذكاء الاصطناعي")
                st.markdown(f'<div class="ai-box"><b>الاحتمالات:</b> فوز الأرض {s["p1"]:.1f}% | تعادل {s["px"]:.1f}%</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-box"><b>البطاقات:</b> 🟨 للأرض {s["hc"]} | 🟨 للضيف {s["ac"]} | 🟥 طرد {s["rp"]}%</div>', unsafe_allow_html=True)
                st.write(f"🥅 الأهداف المتوقعة (xG): **{s['xg']:.2f}**")
                st.bar_chart(pd.DataFrame({'%': [s['p1'], s['px'], s['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Multi-Sport", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات ---
def update_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        with open(fn, "w") as f: f.write("0")
    with open(fn, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(fn, "w") as f: f.write(str(count))
    return count

def get_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn): return 0
    with open(fn, "r") as f:
        try: return int(f.read())
        except: return 0

# --- 3. محرك توقيت تونس والنتائج ---
def get_tn_time(utc_str):
    try:
        dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ")
        return (dt + timedelta(hours=1)).strftime("%d/%m | %H:%M")
    except: return "قريباً"

def predict_exact_score(p1, px, p2, xg):
    if px > 34: return "1 - 1" if xg > 2.0 else "0 - 0"
    if p1 > p2:
        if p1 > 60: return "3 - 0" if xg > 3.0 else "2 - 0"
        return "2 - 1" if xg > 2.2 else "1 - 0"
    else:
        if p2 > 60: return "0 - 3" if xg > 3.0 else "0 - 2"
        return "1 - 2" if xg > 2.2 else "0 - 1"

# --- 4. التصميم البلاتيني ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: #f4f7f9; }
    .match-card {
        background: white; border-radius: 12px; padding: 15px; margin-bottom: 12px;
        border: 1px solid #e0e6ed; display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .score-banner {
        background: linear-gradient(90deg, #1e3799, #000000);
        color: #f1c40f; padding: 25px; border-radius: 20px;
        text-align: center; border: 2px solid #f1c40f; margin-bottom: 25px;
    }
    .odd-badge { background: #f1f2f6; padding: 4px 8px; border-radius: 5px; font-weight: bold; margin-left: 5px; }
    .insight-item { background: #f8f9fa; border-right: 5px solid #1e3799; padding: 10px; border-radius: 8px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 5. جلب البيانات ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=3600)
def fetch_odds_data(l_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
        r = requests.get(url, params=params).json()
        res = []
        for m in r:
            mkts = m.get('bookmakers', [{}])[0].get('markets', [])
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h:
                entry = {
                    "المضيف": m['home_team'], "الضيف": m['away_team'], "التوقيت": get_tn_time(m['commence_time']),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'],
                    "X": h2h['outcomes'][2]['price'] if len(h2h['outcomes']) > 2 else 1.0,
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                }
                res.append(entry)
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        update_stat("unique_visitors")
        st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"👤 الزوار: **{get_stat('unique_visitors')}** | 🎯 التحليلات: **{get_stat('deep_analysis')}**")
    
    try:
        # جلب قائمة جميع الرياضات المتاحة
        sports_url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
        all_sports = requests.get(sports_url).json()
        
        # 1. خانة اختيار نوع الرياضة (عادت للعمل)
        sport_groups = sorted(list(set([s['group'] for s in all_sports])))
        sel_group = st.sidebar.selectbox("🏀 اختر نوع الرياضة", sport_groups, index=sport_groups.index('Soccer') if 'Soccer' in sport_groups else 0)
        
        # 2. خانة اختيار الدوري/البطولة
        l_map = {s['title']: s['key'] for s in all_sports if s['group'] == sel_group}
        sel_l_name = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()))
        sel_l_key = l_map[sel_l_name]
        
        budget = st.sidebar.number_input("💵 ميزانية المحفظة ($):", 10, 5000, 500)
    except: 
        st.error("خطأ في جلب البيانات من السيرفر.")
        return

    st.title(f"🏟️ {sel_l_name}")
    df = fetch_odds_data(sel_l_key)
    
    if not df.empty:
        # عرض جدول المباريات
        st.subheader("📅 مباريات الجولة")
        for _, r in df.iterrows():
            st.markdown(f"""
            <div class="match-card">
                <div>🕒 <small>{r['التوقيت']}</small><br><b>{r['المضيف']} vs {r['الضيف']}</b></div>
                <div>
                    <span class="odd-badge">1: {r['1']}</span>
                    {"<span class='odd-badge'>X: " + str(r['X']) + "</span>" if r['X'] != 1.0 else ""}
                    <span class="odd-badge">2: {r['2']}</span>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # قسم التحليل العميق
        st.header("🔬 المختبر الإحصائي")
        match_list = [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()]
        sel_m = st.selectbox("🎯 اختر مباراة لتحليلها بالذكاء الاصطناعي:", match_list)
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
            update_stat("deep_analysis")
            st.session_state['last_m'] = sel_m

        # حسابات التحليل
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > (1/row['أكثر 2.5']) else 3.1
        score = predict_exact_score(p1, px, p2, xg)
        tight = 1 - abs((p1/100) - (p2/100))

        st.markdown(f"""<div class="score-banner">
            <span style="font-size:1.2rem; opacity:0.8;">النتيجة المتوقعة</span><br>
            <span style="font-size:3.5rem; font-weight:bold;">{score}</span>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.subheader("📊 الاحتمالات")
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2] if sel_group == 'Soccer' else [p1, p2]}, 
                                      index=[row['المضيف'], 'تعادل', row['الضيف']] if sel_group == 'Soccer' else [row['المضيف'], row['الضيف']]))
        with col2:
            st.subheader("📝 الرؤية الفنية")
            st.markdown(f'<div class="insight-item">🥅 <b>xG:</b> {xg}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight-item">🟨 <b>البطاقات:</b> {round(1.5+tight*2,1)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight-item">🎯 <b>الثقة:</b> {int(max(p1,p2)+12)}%</div>', unsafe_allow_html=True)
            st.info(f"💰 الرهان: **{(budget * 0.05):.1f}$**")
    else:
        st.info("لا توجد مباريات جارية حالياً لهذه البطولة.")

if __name__ == '__main__': main()

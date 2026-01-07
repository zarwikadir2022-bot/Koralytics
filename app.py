import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة الفاخرة ---
st.set_page_config(page_title="Koralytics AI | Ultimate Master", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات الدائم ---
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

# --- 4. محرك الرؤية الفنية التفصيلية ---
def get_detailed_insight(p1, px, p2, xg, row):
    insights = []
    if xg > 2.8: insights.append("🔥 **نزعة هجومية:** توقعات بمباراة مفتوحة جداً وفرص تسجيل محققة.")
    elif xg < 2.0: insights.append("🛡️ **حذر تكتيكي:** سيناريو دفاعي مغلق متوقع، المباراة ستعتمد على الصبر.")
    else: insights.append("⚖️ **توازن ميداني:** صراع كبير في وسط الملعب مع تبادل للهجمات المرتدة.")
    
    diff = abs(p1 - p2)
    if diff > 30:
        fav = row['المضيف'] if p1 > p2 else row['الضيف']
        insights.append(f"👑 **سيطرة واضحة:** الخوارزمية ترجح كفة {fav} بشكل كبير للتحكم في اللقاء.")
    elif diff < 10: insights.append("⚔️ **تكافؤ مطلق:** لا توجد أفضلية واضحة؛ المباراة قد تُحسم بكرة ثابتة أو خطأ دفاعي.")
    
    tight = 1 - abs((p1/100) - (p2/100))
    if tight > 0.75: insights.append("🟨 **اندفاع بدني:** تقارب المستوى قد يؤدي لكثرة الصراعات الثنائية والبطاقات.")
    return insights

# --- 5. التصميم الإمبراطوري (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: #f1f5f9; }
    .match-card { background: white; border-radius: 15px; padding: 18px; margin-bottom: 12px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .score-banner { background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #fbbf24; padding: 35px; border-radius: 20px; text-align: center; border: 2px solid #fbbf24; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); margin-bottom: 30px; }
    .insight-item { background: white; border-right: 6px solid #1e3a8a; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #e2e8f0; font-size: 0.95rem; }
    .sidebar-stat { background: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; text-align: center; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 6. جلب البيانات ---
API_KEY = st.secrets.get("ODDS_API_KEY", "YOUR_KEY")

@st.cache_data(ttl=3600)
def fetch_data(l_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{l_key}/odds'
        r = requests.get(url, params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}).json()
        res = []
        for m in r:
            mkts = m.get('bookmakers', [{}])[0].get('markets', [])
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'], "التوقيت": get_tn_time(m['commence_time']),
                    "1": h2h['outcomes'][0]['price'], "2": h2h['outcomes'][1]['price'],
                    "X": h2h['outcomes'][2]['price'] if len(h2h['outcomes']) > 2 else 1.0,
                    "أكثر 2.5": totals['outcomes'][0]['price'] if totals else 1.8,
                    "أقل 2.5": totals['outcomes'][1]['price'] if totals else 1.8
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 7. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        update_stat("unique_visitors")
        st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.markdown(f"""
    <div class="sidebar-stat">👤 الزوار: <b>{get_stat('unique_visitors')}</b></div>
    <div class="sidebar-stat">🎯 التحليلات: <b>{get_stat('deep_analysis')}</b></div>
    """, unsafe_allow_html=True)

    try:
        sports_data = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        sport_groups = sorted(list(set([s['group'] for s in sports_data])))
        sel_group = st.sidebar.selectbox("🏀 نوع الرياضة", sport_groups, index=sport_groups.index('Soccer') if 'Soccer' in sport_groups else 0)
        
        l_map = {s['title']: s['key'] for s in sports_data if s['group'] == sel_group}
        sel_l_name = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 الميزانية ($):", 10, 5000, 500)
    except: st.error("فشل الاتصال بمزود البيانات."); return

    st.title(f"🏟️ {sel_l_name}")
    df = fetch_data(l_map[sel_l_name])
    
    if not df.empty:
        st.subheader("📅 مباريات الجولة")
        for _, r in df.iterrows():
            st.markdown(f'<div class="match-card"><div>🕒 <small>{r["التوقيت"]}</small><br><b>{r["المضيف"]} vs {r["الضيف"]}</b></div><div><span class="odd-badge">1: {r["1"]}</span> <span class="odd-badge">X: {r["X"]}</span> <span class="odd-badge">2: {r["2"]}</span></div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.header("🔬 المختبر الإحصائي العميق")
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل الفني:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        if 'last_m' not in st.session_state or st.session_state['last_m'] != sel_m:
            update_stat("deep_analysis")
            st.session_state['last_m'] = sel_m

        # الحسابات المتقدمة
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        p1, px, p2 = (h_p/total)*100, (d_p/total)*100, (a_p/total)*100
        xg = 1.9 if (1/row['أقل 2.5']) > (1/row['أكثر 2.5']) else 3.2
        score = predict_exact_score(p1, px, p2, xg)
        insights = get_detailed_insight(p1, px, p2, xg, row)

        st.markdown(f'<div class="score-banner"><small>النتيجة المتوقعة بناءً على xG</small><br><span style="font-size:3.5rem;">{score}</span></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1.3])
        with col1:
            st.subheader("📊 احتمالات الفوز")
            st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]))
            st.success(f"💰 الرهان المقترح: **{(budget * 0.05):.1f}$**")
        with col2:
            st.subheader("📝 الرؤية الفنية المفصلة")
            for ins in insights:
                st.markdown(f'<div class="insight-item">{ins}</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background:#fff; padding:15px; border-radius:10px; border:1px solid #cbd5e1;">
                <b>📋 ملخص الميزات الإحصائية:</b><br>
                • معدل الأهداف المتوقعة (xG): <b>{xg}</b><br>
                • توقع البطاقات: <b>{round(1.5+((1-abs(p1-p2)/100)*2),1)}</b><br>
                • مؤشر ثقة التوقع: <b>{int(max(p1,p2,px)+12)}%</b>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد بيانات حالية لهذه البطولة.")

if __name__ == '__main__': main()

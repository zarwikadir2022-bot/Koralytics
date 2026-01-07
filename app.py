import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | V20 Pro", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

# --- 2. التصميم البلاتيني ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .card-metric { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #eee; min-width: 85px; }
</style>
""", unsafe_allow_html=True)

# --- 3. محرك الحسابات (الأهداف والبطاقات) ---
def calculate_discipline(h_odd, a_odd):
    h_prob = 1/h_odd if h_odd > 0 else 0.5
    a_prob = 1/a_odd if a_odd > 0 else 0.5
    tightness = 1 - abs(h_prob - a_prob)
    h_cards = np.random.uniform(1.2, 2.5) + (tightness * 1.5)
    a_cards = np.random.uniform(1.4, 2.8) + (tightness * 1.5)
    red_prob = int((tightness * 25) + 5)
    return round(h_cards, 1), round(a_cards, 1), red_prob

def calculate_exact_goals(over_odd, under_odd):
    if over_odd == 0 or under_odd == 0: return {}, 2.5
    prob_under = (1 / under_odd) / ((1/over_odd) + (1/under_odd))
    expected = 1.9 if prob_under > 0.55 else 3.3 if prob_under < 0.30 else 2.6
    return {k: poisson.pmf(k, expected) * 100 for k in range(5)}, expected

# --- 4. إعدادات API وجلب القائمة الكاملة للدوريات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_API_KEY"

@st.cache_data(ttl=3600)
def get_all_leagues():
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}')
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(league_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{league_key}/odds'
        params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            matches = []
            for m in data:
                if not m['bookmakers']: continue
                mkts = m['bookmakers'][0]['markets']
                h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
                totals = next((i for i in mkts if i['key'] == 'totals'), None)
                if h2h and totals:
                    matches.append({
                        "التاريخ": m['commence_time'][:10],
                        "المضيف": m['home_team'], "الضيف": m['away_team'],
                        "1": h2h['outcomes'][0]['price'], "X": h2h['outcomes'][2]['price'], "2": h2h['outcomes'][1]['price'],
                        "O 2.5": totals['outcomes'][0]['price'], "U 2.5": totals['outcomes'][1]['price']
                    })
            return pd.DataFrame(matches)
    except: return pd.DataFrame()

# --- 5. التطبيق الرئيسي ---
def main():
    # القائمة الجانبية (Sidebar) لاستعادة كل البطولات
    st.sidebar.title("💎 Koralytics Control")
    all_sports = get_all_leagues()
    
    if not all_sports:
        st.error("❌ فشل جلب الدوريات. تأكد من الـ API KEY.")
        return

    # استرجاع نظام الفلترة بالرياضة والدوري
    groups = sorted(list(set([s['group'] for s in all_sports])))
    selected_group = st.sidebar.selectbox("🏅 اختر الرياضة", groups)
    
    leagues_in_group = {s['title']: s['key'] for s in all_sports if s['group'] == selected_group}
    selected_league_name = st.sidebar.selectbox("🏆 اختر البطولة", list(leagues_in_group.keys()))
    selected_league_key = leagues_in_group[selected_league_name]

    st.title(f"⚽ {selected_league_name}")
    
    # جلب مباريات الدوري المختار
    df = fetch_odds(selected_league_key)
    
    if df.empty:
        st.info("🔄 لا توجد مباريات متاحة حالياً لهذه البطولة.")
    else:
        # عرض جدول المباريات الرئيسي
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        
        # اختيار مباراة محددة للتحليل العميق (مع البطاقات)
        sel_match = st.selectbox("🎯 اختر مباراة للتحليل العبقري (البطاقات والأهداف):", 
                                 [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_match.split(" vs ")[0]].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🛡️ رادار البطاقات (Discipline)")
            h_c, a_c, r_p = calculate_discipline(row['1'], row['2'])
            
            st.markdown(f"""
            <div style="display:flex; gap:10px; justify-content:center; margin-bottom:15px;">
                <div class="card-metric" style="background:#fff3cd; border: 2px solid #f1c40f;">🟨 الأرض<br>{h_c}</div>
                <div class="card-metric" style="background:#fff3cd; border: 2px solid #f1c40f;">🟨 الضيف<br>{a_c}</div>
                <div class="card-metric" style="background:#f8d7da; color:#721c24; border: 2px solid #e74c3c;">🟥 طرد<br>{r_p}%</div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"**إجمالي الإنذارات المتوقع:** {round(h_c + a_c)}")
            st.progress(r_p / 100)

        with col2:
            st.subheader("📊 توقعات الذكاء الاصطناعي")
            probs, xG = calculate_exact_goals(row['O 2.5'], row['U 2.5'])
            
            st.markdown(f"""
            <div class="ai-box">
                <b>الحالة البدنية والخشونة:</b> تتسم المباراة بـ {'ندية مفرطة وتدخلات قوية' if r_p > 22 else 'انضباط تكتيكي ولعب نظيف'}.<br>
                <b>القوة الهجومية:</b> معدل الأهداف المتوقع هو {xG:.2f} (xG).
            </div>
            """, unsafe_allow_html=True)
            
            tab_g, tab_c = st.tabs(["⚽ الأهداف المحتملة", "🟨 توزيع الإنذارات"])
            with tab_g:
                st.bar_chart(pd.DataFrame(list(probs.items()), columns=['Goals', 'Prob']).set_index('Goals'))
            with tab_c:
                st.bar_chart(pd.DataFrame({'الفريق': [row['المضيف'], row['الضيف']], 'البطاقات': [h_c, a_c]}).set_index('الفريق'), color="#f1c40f")

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()

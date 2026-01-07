import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | V20 Pro", page_icon="⚽", layout="wide")

# --- 2. التصميم البلاتيني ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); border: 1px solid #ffffff; }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .card-metric { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #eee; min-width: 80px; }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال الأساسية (الذكاء الاصطناعي والبطاقات) ---
def calculate_discipline(h_odd, a_odd):
    h_prob = 1/h_odd if h_odd > 0 else 0.5
    a_prob = 1/a_odd if a_odd > 0 else 0.5
    tightness = 1 - abs(h_prob - a_prob)
    h_cards = np.random.uniform(1.2, 2.8) + (tightness * 1.2)
    a_cards = np.random.uniform(1.5, 3.2) + (tightness * 1.2)
    red_prob = int((tightness * 22) + 5)
    return round(h_cards, 1), round(a_cards, 1), red_prob

def calculate_exact_goals(over_odd, under_odd):
    if over_odd == 0 or under_odd == 0: return {}, 2.5
    prob_under = (1 / under_odd) / ((1/over_odd) + (1/under_odd))
    expected = 1.9 if prob_under > 0.55 else 3.3 if prob_under < 0.30 else 2.6
    return {k: poisson.pmf(k, expected) * 100 for k in range(5)}, expected

def get_team_logo(team_name):
    # دالة مبسطة للشعارات (يمكنك توسيعها)
    return "https://cdn-icons-png.flaticon.com/512/10542/10542547.png"

# --- 4. جلب البيانات من API ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_API_KEY_HERE"

@st.cache_data(ttl=3600)
def fetch_data(league_key):
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
                        "المضيف": m['home_team'], "الضيف": m['away_team'],
                        "1": h2h['outcomes'][0]['price'], "X": h2h['outcomes'][2]['price'], "2": h2h['outcomes'][1]['price'],
                        "O 2.5": totals['outcomes'][0]['price'], "U 2.5": totals['outcomes'][1]['price'],
                        "H_Logo": get_team_logo(m['home_team']), "A_Logo": get_team_logo(m['away_team'])
                    })
            return pd.DataFrame(matches)
    except: return pd.DataFrame()

# --- 5. التطبيق الرئيسي ---
def main():
    st.title("💎 Koralytics AI - Platinum V20")
    
    # اختيار الدوري (مثال: الدوري الإنجليزي)
    league = st.sidebar.selectbox("🏆 اختر البطولة", ["soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a"])
    
    df = fetch_data(league)
    
    if df.empty:
        st.warning("⚠️ يرجى التأكد من مفتاح API_KEY في الإعدادات.")
    else:
        st.dataframe(df[["المضيف", "1", "X", "2", "الضيف"]], use_container_width=True)
        
        st.markdown("---")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        
        sel_match = st.selectbox("🎯 اختر مباراة للتحليل العميق:", [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_match.split(" vs ")[0]].iloc[0]
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("🛡️ رادار الانضباط")
            h_c, a_c, r_p = calculate_discipline(row['1'], row['2'])
            
            st.markdown(f"""
            <div style="display:flex; gap:10px; justify-content:center;">
                <div class="card-metric" style="background:#fff3cd;">🟨 الأرض<br>{h_c}</div>
                <div class="card-metric" style="background:#fff3cd;">🟨 الضيف<br>{a_c}</div>
                <div class="card-metric" style="background:#f8d7da; color:#721c24;">🟥 طرد<br>{r_p}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info(f"المجموع المتوقع للإنذارات: {round(h_c + a_c)}")

        with c2:
            st.subheader("📊 تحليل الذكاء الاصطناعي")
            probs, xG = calculate_exact_goals(row['O 2.5'], row['U 2.5'])
            
            st.markdown(f"""
            <div class="ai-box">
                <b>القراءة الفنية:</b> مباراة تتسم بـ {'ندية عالية وخشونة' if r_p > 20 else 'لعب مفتوح وهادئ'}.<br>
                <b>توقع الأهداف:</b> {xG:.2f} هدف متوقع.<br>
                <b>النتيجة الأقرب:</b> {'2-1 أو 1-1' if xG < 3 else '3-1 أو 2-2'}
            </div>
            """, unsafe_allow_html=True)
            
            t_goals, t_cards = st.tabs(["⚽ توزيع الأهداف", "🟨 رادار البطاقات"])
            with t_goals:
                st.bar_chart(pd.DataFrame(list(probs.items()), columns=['Goals', 'Prob']).set_index('Goals'))
            with t_cards:
                st.bar_chart(pd.DataFrame({'الفريق': [row['المضيف'], row['الضيف']], 'البطاقات': [h_c, a_c]}).set_index('الفريق'), color="#f1c40f")

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()

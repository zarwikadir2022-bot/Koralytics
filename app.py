import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="Koralytics AI | V20 Pro", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .profit-box {background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 10px;}
    .advisor-box {background-color: #fef9e7; border: 1px solid #f1c40f; color: #d35400; padding: 10px; border-radius: 8px; font-size: 0.9em; margin-top: 10px;}
    .card-metric { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #eee; min-width: 85px; }
</style>
""", unsafe_allow_html=True)

# --- 2. محركات الحسابات الذكية ---
def calculate_metrics(h_odd, a_odd, d_odd):
    h_prob = (1/h_odd * 100) if h_odd > 0 else 33.3
    a_prob = (1/a_odd * 100) if a_odd > 0 else 33.3
    d_prob = (1/d_odd * 100) if d_odd > 0 else 33.3
    # تطبيع النسب لتصل لـ 100%
    total = h_prob + a_prob + d_prob
    return (h_prob/total)*100, (a_prob/total)*100, (d_prob/total)*100

def calculate_discipline(h_odd, a_odd):
    h_p = 1/h_odd if h_odd > 0 else 0.5
    a_p = 1/a_odd if a_odd > 0 else 0.5
    tightness = 1 - abs(h_p - a_p)
    h_cards = np.random.uniform(1.2, 2.4) + (tightness * 1.3)
    a_cards = np.random.uniform(1.4, 2.7) + (tightness * 1.3)
    red_prob = int((tightness * 22) + 7)
    return round(h_cards, 1), round(a_cards, 1), red_prob

# --- 3. جلب البيانات ---
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
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{league_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        if r.status_code == 200:
            matches = []
            for m in r.json():
                if not m['bookmakers']: continue
                mkts = m['bookmakers'][0]['markets']
                h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
                totals = next((i for i in mkts if i['key'] == 'totals'), None)
                if h2h and totals:
                    matches.append({
                        "المضيف": m['home_team'], "الضيف": m['away_team'],
                        "1": h2h['outcomes'][0]['price'], "X": h2h['outcomes'][2]['price'], "2": h2h['outcomes'][1]['price'],
                        "O 2.5": totals['outcomes'][0]['price'], "U 2.5": totals['outcomes'][1]['price']
                    })
            return pd.DataFrame(matches)
    except: return pd.DataFrame()

# --- 4. واجهة التطبيق ---
def main():
    st.sidebar.title("💎 Koralytics AI")
    all_sports = get_all_leagues()
    if not all_sports: st.error("API Key Error"); return

    groups = sorted(list(set([s['group'] for s in all_sports])))
    selected_group = st.sidebar.selectbox("🏅 الرياضة", groups)
    leagues_dict = {s['title']: s['key'] for s in all_sports if s['group'] == selected_group}
    selected_league_name = st.sidebar.selectbox("🏆 البطولة", list(leagues_dict.keys()))
    
    budget = st.sidebar.number_input("💵 ميزانيتك ($):", 10.0, 10000.0, 500.0)

    df = fetch_odds(leagues_dict[selected_league_name])
    
    if not df.empty:
        st.dataframe(df[["المضيف", "1", "X", "2", "الضيف"]], use_container_width=True, hide_index=True)
        st.markdown("---")
        
        sel_match = st.selectbox("🎯 اختر مباراة للتحليل العميق:", [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_match.split(" vs ")[0]].iloc[0]
        
        # حساب النسب والبطاقات
        p1, px, p2 = calculate_metrics(row['1'], row['2'], row['X'])
        h_c, a_c, r_p = calculate_discipline(row['1'], row['2'])
        
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.subheader("💰 حاسبة الأرباح")
            stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
            sel_odd = st.selectbox("النتيجة المتوقعة:", ["فوز الأرض", "تعادل", "فوز الضيف"])
            odd_val = row['1'] if sel_odd == "فوز الأرض" else row['X'] if sel_odd == "تعادل" else row['2']
            
            st.markdown(f"<div class='profit-box'>الربح المتوقع: {(stake * odd_val):.2f}$</div>", unsafe_allow_html=True)
            
            # المستشار المالي
            safe_score = p1 if sel_odd == "فوز الأرض" else p2 if sel_odd == "فوز الضيف" else px
            advice = "✅ فرصة قوية" if safe_score > 60 else "⚠️ رهان مخاطرة" if safe_score < 40 else "⚖️ فرصة متوازنة"
            rec_bet = budget * (safe_score/100) * 0.1
            st.markdown(f"<div class='advisor-box'>💡 <b>المستشار:</b> {advice}<br>المبلغ المقترح: {rec_bet:.1f}$</div>", unsafe_allow_html=True)

        with col2:
            st.subheader("📊 نسب الفوز والبطاقات")
            t1, t2 = st.tabs(["📈 احتمالات النتيجة", "🟨 رادار الانضباط"])
            
            with t1:
                prob_df = pd.DataFrame({'الفريق': [row['المضيف'], 'تعادل', row['الضيف']], 'النسبة %': [p1, px, p2]}).set_index('الفريق')
                st.bar_chart(prob_df, color="#2980b9")
                st.write(f"**نسبة فوز {row['المضيف']}:** {p1:.1f}%")
                st.write(f"**نسبة فوز {row['الضيف']}:** {p2:.1f}%")

            with t2:
                st.markdown(f"""
                <div style="display:flex; gap:10px; justify-content:center; margin-bottom:15px;">
                    <div class="card-metric" style="background:#fff3cd; border: 2px solid #f1c40f;">🟨 {row['المضيف']}<br>{h_c}</div>
                    <div class="card-metric" style="background:#fff3cd; border: 2px solid #f1c40f;">🟨 {row['الضيف']}<br>{a_c}</div>
                    <div class="card-metric" style="background:#f8d7da; border: 2px solid #e74c3c;">🟥 طرد<br>{r_p}%</div>
                </div>
                """, unsafe_allow_html=True)
                st.bar_chart(pd.DataFrame({'الفريق': [row['المضيف'], row['الضيف']], 'البطاقات': [h_c, a_c]}).set_index('الفريق'), color="#f1c40f")

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

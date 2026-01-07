import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Ultimate V20", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

# --- 2. التصميم البلاتيني الكامل (CSS) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .ticket-box { background: linear-gradient(45deg, #2c3e50, #4ca1af); color: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    .profit-box {background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold;}
    .advisor-box {background-color: #fef9e7; border: 1px solid #f1c40f; color: #d35400; padding: 10px; border-radius: 8px; font-size: 0.9em;}
    .card-metric { padding: 8px; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #eee; min-width: 70px; }
</style>
""", unsafe_allow_html=True)

# --- 3. إدارة الجلسة والمفاتيح ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

# --- 4. محرك الحسابات (أهداف، فوز، بطاقات) ---
def get_analysis_metrics(row):
    h_odd, a_odd, d_odd = row['1'], row['2'], row['X']
    # احتمالات الفوز
    h_p = (1/h_odd); a_p = (1/a_odd); d_p = (1/d_odd)
    total = h_p + a_p + d_p
    # توقع البطاقات
    tightness = 1 - abs((h_p/total) - (a_p/total))
    h_cards = round(np.random.uniform(1.2, 2.4) + (tightness * 1.5), 1)
    a_cards = round(np.random.uniform(1.4, 2.7) + (tightness * 1.5), 1)
    red_p = int((tightness * 25) + 5)
    # توقع الأهداف (Poisson)
    prob_under = (1/row['U 2.5']) / ((1/row['O 2.5']) + (1/row['U 2.5']))
    exp_g = 1.9 if prob_under > 0.55 else 3.3 if prob_under < 0.30 else 2.6
    return (h_p/total)*100, (px := (d_p/total)*100), (a_p/total)*100, h_cards, a_cards, red_p, exp_g

# --- 5. جلب البيانات ---
@st.cache_data(ttl=3600)
def get_leagues():
    try: return requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
            if not m['bookmakers']: continue
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "1": h2h['outcomes'][0]['price'], "X": h2h['outcomes'][2]['price'], "2": h2h['outcomes'][1]['price'],
                    "O 2.5": totals['outcomes'][0]['price'], "U 2.5": totals['outcomes'][1]['price'],
                    "التاريخ": m['commence_time'][:10], "H_Logo": "⚽", "A_Logo": "⚽"
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    # --- Sidebar ---
    st.sidebar.title("💎 Koralytics Control")
    sports_data = get_leagues()
    if not sports_data: st.error("API Error"); return
    
    groups = sorted(list(set([s['group'] for s in sports_data])))
    grp = st.sidebar.selectbox("🏅 الرياضة", groups)
    leagues = {s['title']: s['key'] for s in sports_data if s['group'] == grp}
    l_name = st.sidebar.selectbox("🏆 البطولة", list(leagues.keys()))
    
    budget = st.sidebar.number_input("💵 ميزانيتك ($):", 10.0, 10000.0, 500.0)
    
    # --- ورقتي ---
    if st.session_state["my_ticket"]:
        st.sidebar.markdown('<div class="ticket-box">#### 🧾 ورقتي', unsafe_allow_html=True)
        total_o = 1.0
        for itm in st.session_state["my_ticket"]:
            st.sidebar.write(f"✅ {itm['pick']} | {itm['odd']}")
            total_o *= itm['odd']
        st.sidebar.write(f"**Total Odd: {total_o:.2f}**")
        if st.sidebar.button("🗑️ مسح"): st.session_state["my_ticket"] = []; st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # --- Main Content ---
    st.title(f"⚽ {l_name}")
    df = fetch_odds(leagues[l_name])
    
    if not df.empty:
        # العصا السحرية
        if st.button("🪄 العصا السحرية (أفضل 3 مباريات)"):
            candidates = []
            for _, r in df.iterrows():
                if 1/r['1'] > 0.65: candidates.append({"pick": f"Win {r['المضيف']}", "odd": r['1'], "prob": 1/r['1']})
            st.session_state["my_ticket"] = sorted(candidates, key=lambda x: x['prob'], reverse=True)[:3]
            st.rerun()

        st.dataframe(df[["المضيف", "1", "X", "2", "الضيف", "التاريخ"]], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🎯 التحليل العميق والبطاقات")
        sel_m = st.selectbox("اختر مباراة:", [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" vs ")[0]].iloc[0]
        
        # استخراج كافة الحسابات
        p1, px, p2, h_c, a_c, red_p, xG = get_analysis_metrics(row)
        
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            st.write(f"**{row['المضيف']} vs {row['الضيف']}**")
            st.markdown(f"""
                <div style="display:flex; gap:5px; margin-bottom:10px;">
                    <div class="card-metric" style="background:#fff3cd;">🟨 {h_c}</div>
                    <div class="card-metric" style="background:#fff3cd;">🟨 {a_c}</div>
                    <div class="card-metric" style="background:#f8d7da;">🟥 {red_p}%</div>
                </div>
            """, unsafe_allow_html=True)
            
            stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
            sel_o = st.selectbox("النتيجة:", ["الأرض", "تعادل", "الضيف"])
            v_odd = row['1'] if sel_o=="الأرض" else row['X'] if sel_o=="تعادل" else row['2']
            
            if st.button(f"➕ أضف للورقة (@ {v_odd})"):
                st.session_state["my_ticket"].append({"pick": f"{sel_o} ({row['المضيف']})", "odd": v_odd})
                st.rerun()
            
            st.markdown(f"<div class='profit-box'>الربح: {(stake*v_odd):.2f}$</div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""<div class='ai-box'>
                <b>🤖 تحليل Koralytics:</b> المباراة {'عنيفة' if red_p > 20 else 'هادئة'}. <br>
                <b>الاحتمالات:</b> الأرض {p1:.0f}% | تعادل {px:.0f}% | الضيف {p2:.0f}% <br>
                <b>الأهداف المتوقعة:</b> {xG:.2f}
            </div>""", unsafe_allow_html=True)
            
            # الرسوم البيانية
            tab1, tab2 = st.tabs(["📈 احتمالات الفوز", "⚽ الأهداف والبطاقات"])
            with tab1:
                st.bar_chart(pd.DataFrame({'Prob': [p1, px, p2]}, index=[row['المضيف'], 'Draw', row['الضيف']]))
            with tab2:
                st.bar_chart(pd.DataFrame({'Value': [h_c, a_c, xG]}, index=['Cards Home', 'Cards Away', 'xG Total']))
                
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Ultimate V20", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

# --- 2. محرك عداد الزوار (بدون Supabase) ---
def update_counter():
    count_file = "visit_count.txt"
    # إذا لم يكن الملف موجوداً، نقوم بإنشائه
    if not os.path.exists(count_file):
        with open(count_file, "w") as f:
            f.write("0")
    
    # قراءة العدد الحالي
    with open(count_file, "r") as f:
        try:
            current_count = int(f.read())
        except:
            current_count = 0
            
    # زيادة العدد وإعادة حفظه
    new_count = current_count + 1
    with open(count_file, "w") as f:
        f.write(str(new_count))
    return new_count

# --- 3. التصميم البلاتيني الكامل (CSS) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; color: #333333; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .ticket-box { background: linear-gradient(45deg, #2c3e50, #4ca1af); color: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
    .profit-box {background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold;}
    .visitor-badge { text-align:center; padding:15px; background:white; border-radius:12px; border:1px solid #d1d5db; margin-top:20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 4. إعدادات المفاتيح وإدارة الجلسة ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

# --- 5. محرك الحسابات (أهداف، فوز، بطاقات) ---
def get_analysis_metrics(row):
    h_odd, a_odd, d_odd = row['1'], row['2'], row['X']
    h_p, a_p, d_p = (1/h_odd), (1/a_odd), (1/d_odd)
    total = h_p + a_p + d_p
    tightness = 1 - abs((h_p/total) - (a_p/total))
    h_cards = round(1.4 + (tightness * 1.6), 1)
    a_cards = round(1.6 + (tightness * 1.6), 1)
    red_p = int((tightness * 24) + 6)
    prob_u = (1/row['U 2.5']) / ((1/row['O 2.5']) + (1/row['U 2.5']))
    exp_g = 1.8 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
    return (h_p/total)*100, (d_p/total)*100, (a_p/total)*100, h_cards, a_cards, red_p, exp_g

# --- 6. جلب البيانات من الـ API ---
@st.cache_data(ttl=3600)
def get_leagues_list():
    try: return requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds_data(l_key):
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
                    "O 2.5": totals['outcomes'][0]['price'], "U 2.5": totals['outcomes'][1]['price']
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 7. التطبيق الرئيسي ---
def main():
    # تحديث عداد الزوار
    visitors = update_counter()

    # --- Sidebar ---
    st.sidebar.title("💎 Koralytics V20")
    
    # عرض عداد الزوار في الـ Sidebar بشكل أنيق
    st.sidebar.markdown(f"""
        <div class="visitor-badge">
            <span style="color:#7f8c8d; font-size:0.8rem; font-weight:bold;">عدد الزيارات الإجمالي</span><br>
            <span style="color:#2c3e50; font-size:1.6rem; font-weight:bold;">👤 {visitors}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    sports_list = get_leagues_list()
    if not sports_list: st.sidebar.error("تأكد من الـ API KEY"); return
    
    grps = sorted(list(set([s['group'] for s in sports_list])))
    sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
    leagues_map = {s['title']: s['key'] for s in sports_list if s['group'] == sel_grp}
    sel_l = st.sidebar.selectbox("🏆 البطولة", list(leagues_map.keys()))
    
    budget = st.sidebar.number_input("💵 ميزانيتك ($):", 10.0, 10000.0, 500.0)

    # --- Main ---
    st.title(f"⚽ {sel_l}")
    df = fetch_odds_data(leagues_map[sel_l])
    
    if not df.empty:
        # العصا السحرية
        if st.button("🪄 العصا السحرية (أفضل 3 مباريات)"):
            best = df.sort_values(by="1", ascending=True).head(3)
            st.session_state["my_ticket"] = [{"pick": f"Win {r['المضيف']}", "odd": r['1']} for _, r in best.iterrows()]
            st.rerun()

        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل والبطاقات:", [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" vs ")[0]].iloc[0]
        
        p1, px, p2, hc, ac, rp, xg = get_analysis_metrics(row)
        
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.subheader("🛡️ الانضباط")
            st.markdown(f"""
                <div style="display:flex; gap:10px; margin-bottom:15px;">
                    <div style="padding:10px; background:#fff3cd; border-radius:8px; flex:1; text-align:center;">🟨 {hc}</div>
                    <div style="padding:10px; background:#fff3cd; border-radius:8px; flex:1; text-align:center;">🟨 {ac}</div>
                    <div style="padding:10px; background:#f8d7da; border-radius:8px; flex:1; text-align:center; color:#721c24;">🟥 {rp}%</div>
                </div>
            """, unsafe_allow_html=True)
            
            stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
            sel_res = st.selectbox("النتيجة المتوقعة:", ["فوز الأرض", "تعادل", "فوز الضيف"])
            v_odd = row['1'] if sel_res=="فوز الأرض" else row['X'] if sel_res=="تعادل" else row['2']
            
            if st.button(f"➕ أضف للورقة (@ {v_odd})"):
                st.session_state["my_ticket"].append({"pick": f"{sel_res} ({row['المضيف']})", "odd": v_odd})
                st.rerun()
            
            st.markdown(f"<div class='profit-box'>الربح: {(stake*v_odd):.2f}$</div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""<div class='ai-box'>
                <b>🤖 تحليل الذكاء الاصطناعي:</b> الأرض {p1:.1f}% | تعادل {px:.1f}% | الضيف {p2:.1f}% <br>
                <b>الأهداف المتوقعة:</b> {xg:.2f} (xG) | <b>الحالة:</b> {'مباراة مشحونة' if rp > 20 else 'هادئة'}
            </div>""", unsafe_allow_html=True)
            
            # الرسوم البيانية
            tab1, tab2 = st.tabs(["📈 احتمالات النتيجة", "📊 البطاقات"])
            with tab1:
                st.bar_chart(pd.DataFrame({'Prob': [p1, px, p2]}, index=[row['المضيف'], 'Draw', row['الضيف']]))
            with tab2:
                st.bar_chart(pd.DataFrame({'Yellow Cards': [hc, ac]}, index=[row['المضيف'], row['الضيف']]), color="#f1c40f")

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

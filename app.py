import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | النسخة البلاتينية",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. محرك عداد الزوار الذكي (مرة واحدة لكل جلسة) ---
def get_unique_visitors():
    count_file = "visit_count.txt"
    if 'visited' not in st.session_state:
        if not os.path.exists(count_file):
            with open(count_file, "w") as f: f.write("0")
        with open(count_file, "r") as f:
            try: current_count = int(f.read())
            except: current_count = 0
        new_count = current_count + 1
        with open(count_file, "w") as f: f.write(str(new_count))
        st.session_state['visited'] = True
        st.session_state['total_visitors'] = new_count
    return st.session_state.get('total_visitors', 0)

# --- 3. التصميم البلاتيني الكريستالي (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif; }

    /* الخلفية المعدنية */
    .stApp {
        background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e);
        background-attachment: fixed;
        color: #1a1a1a;
    }

    /* القائمة الجانبية الزجاجية */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.5);
    }

    /* بطاقات الكريستال */
    .crystal-card {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.8);
        box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1), 
                    -5px -5px 15px rgba(255, 255, 255, 0.7);
        direction: rtl;
    }

    /* صندوق الذكاء الاصطناعي */
    .ai-box {
        background: linear-gradient(145deg, #ffffff, #e6e6e6);
        border-right: 6px solid #424242;
        padding: 20px;
        border-radius: 12px;
        color: #212121;
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.05), 4px 4px 10px rgba(0,0,0,0.1);
        direction: rtl;
    }

    .visitor-badge {
        text-align:center; 
        padding:15px; 
        background: #e0e0e0;
        border-radius: 15px;
        box-shadow: 6px 6px 12px #bebebe, -6px -6px 12px #ffffff;
        margin-bottom: 20px;
    }

    div.stButton > button {
        background: linear-gradient(145deg, #757575, #424242);
        color: white;
        border: none;
        border-radius: 10px;
        width: 100%;
        font-weight: bold;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background: #212121;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. المحركات الإحصائية ---
def get_match_metrics(row):
    try:
        h_odd, a_odd, d_odd = row['1'], row['2'], row['X']
        h_p, a_p, d_p = (1/h_odd), (1/a_odd), (1/d_odd)
        total = h_p + a_p + d_p
        tightness = 1 - abs((h_p/total) - (a_p/total))
        
        # توقع البطاقات
        h_cards = round(1.3 + (tightness * 1.4), 1)
        a_cards = round(1.5 + (tightness * 1.4), 1)
        red_p = int((tightness * 22) + 8)
        
        # توقع الأهداف بناءً على "أكثر/أقل"
        o_25 = row['أكثر 2.5']
        u_25 = row['أقل 2.5']
        prob_u = (1/u_25) / ((1/o_25) + (1/u_25))
        xg = 1.9 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
        
        return (h_p/total)*100, (d_p/total)*100, (a_p/total)*100, h_cards, a_cards, red_p, xg
    except Exception as e:
        return 0, 0, 0, 0, 0, 0, 0

# --- 5. جلب البيانات ---
@st.cache_data(ttl=3600)
def fetch_leagues():
    try:
        API_KEY = st.secrets["ODDS_API_KEY"]
        return requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(l_key):
    try:
        API_KEY = st.secrets["ODDS_API_KEY"]
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
            if not m['bookmakers']: continue
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                # ترتيب التوقعات h2h: قد يختلف ترتيب النتائج (فوز، تعادل، خسارة) حسب الـ API
                # لذا نبحث عن الاسم الصحيح للمضيف والضيف
                outcomes = h2h['outcomes']
                h_odd = next(o['price'] for o in outcomes if o['name'] == m['home_team'])
                a_odd = next(o['price'] for o in outcomes if o['name'] == m['away_team'])
                d_odd = next(o['price'] for o in outcomes if o['name'] == 'Draw')
                
                # ترتيب التوقعات totals
                t_outcomes = totals['outcomes']
                o_25 = next(o['price'] for o in t_outcomes if o['name'] == 'Over' and o['point'] == 2.5)
                u_25 = next(o['price'] for o in t_outcomes if o['name'] == 'Under' and o['point'] == 2.5)
                
                res.append({
                    "المضيف": m['home_team'], "الضيف": m['away_team'],
                    "1": h_odd, "X": d_odd, "2": a_odd,
                    "أكثر 2.5": o_25, "أقل 2.5": u_25
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    visitors = get_unique_visitors()

    # --- القائمة الجانبية ---
    st.sidebar.markdown(f"""
        <div class="visitor-badge">
            <span style="color:#616161; font-size:0.85rem; font-weight:bold;">إجمالي الزوار</span><br>
            <span style="color:#212121; font-size:1.8rem; font-weight:bold;">👤 {visitors}</span>
        </div>
    """, unsafe_allow_html=True)

    sports = fetch_leagues()
    if not sports:
        st.sidebar.error("يرجى التأكد من مفتاح API في Secrets")
        return
    
    # جعل كرة القدم في المقدمة
    grps = sorted(list(set([s['group'] for s in sports])))
    if "Soccer" in grps:
        grps.remove("Soccer")
        grps.insert(0, "Soccer")
    
    sel_grp = st.sidebar.selectbox("🏅 اختر الرياضة", grps)
    l_map = {s['title']: s['key'] for s in sports if s['group'] == sel_grp}
    sel_l = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()))
    
    budget = st.sidebar.number_input("💵 ميزانية المحفظة ($):", 10.0, 10000.0, 500.0)

    # --- المحتوى الرئيسي ---
    st.title(f"💎 Koralytics AI: {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        if st.button("🪄 العصا السحرية (أفضل 3 فرص لليوم)"):
            best = df.sort_values(by="1", ascending=True).head(3)
            st.session_state["my_ticket"] = [{"pick": f"فوز {r['المضيف']}", "odd": r['1']} for _, r in best.iterrows()]
            st.success("تم اختيار أفضل المباريات بناءً على القوة الإحصائية!")

        st.dataframe(df[["المضيف", "الضيف", "1", "X", "2", "أكثر 2.5", "أقل 2.5"]], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل البلاتيني:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        p1, px, p2, hc, ac, rp, xg = get_match_metrics(row)
        
        col_a, col_b = st.columns([1, 1.5])
        with col_a:
            st.subheader("💰 حاسبة الاستثمار")
            stake = st.number_input("مبلغ الرهان ($):", 1.0, 1000.0, 10.0)
            pick_res = st.selectbox("توقعك الشخصي:", [row['المضيف'], "تعادل", row['الضيف']])
            v_odd = row['1'] if pick_res==row['المضيف'] else row['X'] if pick_res=="تعادل" else row['2']
            
            st.markdown(f"<div style='background:#f5f5f5; padding:15px; border-radius:10px; text-align:center; border:1px solid #ddd;'>الربح الممكن: <b>{(stake*v_odd):.2f}$</b></div>", unsafe_allow_html=True)
            st.info(f"💡 نصيحة المستشار: يفضل دخول المباراة بمبلغ {(budget * (p1/100) * 0.05):.1f}$")

        with col_b:
            st.subheader("📊 تحليل قلب البيانات")
            st.markdown(f"""<div class='ai-box'>
                <b>احتمالات الفوز:</b> {row['المضيف']} ({p1:.1f}%) | تعادل ({px:.1f}%) | {row['الضيف']} ({p2:.1f}%) <br>
                <b>رادار البطاقات:</b> 🟨 للأرض {hc} | 🟨 للضيف {ac} | 🟥 احتمالية طرد {rp}% <br>
                <b>معدل الأهداف المتوقع (xG):</b> {xg:.2f}
            </div>""", unsafe_allow_html=True)
            
            tabs = st.tabs(["📈 قوة الفريقين", "🟨 مؤشر الخشونة"])
            with tabs[0]: 
                st.bar_chart(pd.DataFrame({'الاحتمالية %': [p1, px, p2]}, index=[row['المضيف'], 'تعادل', row['الضيف']]), color="#424242")
            with tabs[1]: 
                st.bar_chart(pd.DataFrame({'البطاقات المتوقعة': [hc, ac]}, index=[row['المضيف'], row['الضيف']]), color="#757575")

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()

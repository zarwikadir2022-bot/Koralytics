import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | النسخة البلاتينية", page_icon="💎", layout="wide", initial_sidebar_state="expanded")

# --- 2. محرك عداد الزوار الذكي ---
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
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    
    .crystal-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }
    .ai-box { background: linear-gradient(145deg, #ffffff, #e6e6e6); border-right: 6px solid #424242; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 4px 4px 10px rgba(0,0,0,0.1); }
    .visitor-badge { text-align:center; padding:15px; background: #e0e0e0; border-radius: 15px; box-shadow: 6px 6px 12px #bebebe, -6px -6px 12px #ffffff; margin-bottom: 20px; }
    .ticket-box { background: linear-gradient(45deg, #2c3e50, #4ca1af); color: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    .profit-box { background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }
    .advisor-box { background-color: rgba(254, 249, 231, 0.8); border: 1px solid #f1c40f; color: #d35400; padding: 15px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 4. المحركات الإحصائية والتحليلية ---
def calculate_all_stats(row):
    try:
        h_p, a_p, d_p = (1/row['1']), (1/row['2']), (1/row['X'])
        total = h_p + a_p + d_p
        tightness = 1 - abs((h_p/total) - (a_p/total))
        h_cards = round(1.3 + (tightness * 1.5), 1)
        a_cards = round(1.5 + (tightness * 1.5), 1)
        red_p = int((tightness * 22) + 8)
        prob_u = (1/row['أقل 2.5']) / ((1/row['أكثر 2.5']) + (1/row['أقل 2.5']))
        xg = 1.9 if prob_u > 0.55 else 3.4 if prob_u < 0.30 else 2.6
        return {"p1": (h_p/total)*100, "px": (d_p/total)*100, "p2": (a_p/total)*100, "hc": h_cards, "ac": a_cards, "rp": red_p, "xg": xg}
    except: return None

# --- 5. إدارة البيانات ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

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
                    "1": next(o['price'] for o in h2h['outcomes'] if o['name'] == m['home_team']),
                    "2": next(o['price'] for o in h2h['outcomes'] if o['name'] == m['away_team']),
                    "X": next(o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw'),
                    "أكثر 2.5": next(o['price'] for o in totals['outcomes'] if o['name'] == 'Over'),
                    "أقل 2.5": next(o['price'] for o in totals['outcomes'] if o['name'] == 'Under')
                })
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 6. التطبيق الرئيسي ---
def main():
    visitors = get_unique_visitors()
    
    # --- Sidebar ---
    st.sidebar.markdown(f'<div class="visitor-badge">إجمالي الزوار الفريدين<br><b>👤 {visitors}</b></div>', unsafe_allow_html=True)
    
    try:
        leagues_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        grps = sorted(list(set([s['group'] for s in leagues_raw])))
        if "Soccer" in grps: grps.remove("Soccer"); grps.insert(0, "Soccer")
        sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
        l_map = {s['title']: s['key'] for s in leagues_raw if s['group'] == sel_grp}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
        budget = st.sidebar.number_input("💵 المحفظة ($):", 10.0, 10000.0, 500.0)
    except: st.sidebar.error("خطأ في الاتصال"); return

    # نظام الورقة (Ticket Box)
    if st.session_state["my_ticket"]:
        st.sidebar.markdown('<div class="ticket-box">#### 🧾 ورقتي الحالية', unsafe_allow_html=True)
        t_odd = 1.0
        for itm in st.session_state["my_ticket"]:
            st.sidebar.write(f"✅ {itm['pick']} | {itm['odd']}")
            t_odd *= itm['odd']
        st.sidebar.write(f"**إجمالي الأودز: {t_odd:.2f}**")
        if st.sidebar.button("🗑️ مسح"): st.session_state["my_ticket"] = []; st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # --- Main Content ---
    st.title(f"💎 {sel_l}")
    df = fetch_odds(l_map[sel_l])
    
    if not df.empty:
        # العصا السحرية
        if st.button("🪄 العصا السحرية (أفضل 3 فرص لليوم)"):
            best = df.sort_values(by="1", ascending=True).head(3)
            st.session_state["my_ticket"] = [{"pick": f"فوز {r['المضيف']}", "odd": r['1']} for _, r in best.iterrows()]
            st.rerun()

        # الجدول الكامل (حل مشكلة العرض)
        st.dataframe(df[["المضيف", "الضيف", "1", "X", "2"]], use_container_width=True, hide_index=True,
                    column_config={
                        "المضيف": st.column_config.TextColumn("🏠 الأرض", width="large"),
                        "الضيف": st.column_config.TextColumn("✈️ الضيف", width="large"),
                        "1": st.column_config.NumberColumn("1", width="small", format="%.2f"),
                        "X": st.column_config.NumberColumn("X", width="small", format="%.2f"),
                        "2": st.column_config.NumberColumn("2", width="small", format="%.2f")
                    })
        
        st.markdown("---")
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل الإحصائي الكامل:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        stats = calculate_all_stats(row)
        if stats:
            col1, col2 = st.columns([1, 1.5])
            with col1:
                st.subheader("💰 استثمار")
                stake = st.number_input("مبلغ الرهان ($):", 1.0, 1000.0, 10.0)
                sel_opt = st.selectbox("توقعك الشخصي:", [row['المضيف'], "تعادل", row['الضيف']])
                v_odd = row['1'] if sel_opt==row['المضيف'] else row['X'] if sel_opt=="تعادل" else row['2']
                
                if st.button(f"➕ أضف للورقة (@ {v_odd})"):
                    st.session_state["my_ticket"].append({"pick": f"{sel_opt} ({row['المضيف']})", "odd": v_odd})
                    st.rerun()
                
                st.markdown(f"<div class='profit-box'>الربح: {(stake*v_odd):.2f}$</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='advisor-box'>💡 <b>المستشار:</b> المبلغ المقترح لهذا الرهان هو {(budget * (stats['p1']/100) * 0.05):.1f}$</div>", unsafe_allow_html=True)

            with col2:
                st.subheader("📊 ذكاء المباراة")
                st.markdown(f"""<div class='ai-box'>
                    <b>احتمالات الفوز:</b> {row['المضيف']} ({stats['p1']:.1f}%) | تعادل ({stats['px']:.1f}%) | {row['الضيف']} ({stats['p2']:.1f}%) <br>
                    <b>رادار البطاقات:</b> 🟨 الأرض {stats['hc']} | 🟨 الضيف {stats['ac']} | 🟥 طرد {stats['rp']}% <br>
                    <b>معدل الأهداف (xG):</b> {stats['xg']:.2f}
                </div>""", unsafe_allow_html=True)
                
                t_1, t_2 = st.tabs(["📈 قوة الفريقين", "🟨 رادار الخشونة"])
                with t_1: st.bar_chart(pd.DataFrame({'%': [stats['p1'], stats['px'], stats['p2']]}, index=[row['المضيف'], 'تعادل', row['الضيف']]), color="#424242")
                with t_2: st.bar_chart(pd.DataFrame({'🟨': [stats['hc'], stats['ac']]}, index=[row['المضيف'], row['الضيف']]), color="#f1c40f")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

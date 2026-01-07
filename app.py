import streamlit as st
import pandas as pd
import requests
import os
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="Koralytics AI | Platinum", page_icon="💎", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: radial-gradient(circle at top right, #e0e0e0, #bdbdbd, #9e9e9e); background-attachment: fixed; }
    .crystal-card { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(12px); border-radius: 20px; padding: 25px; border: 1px solid rgba(255, 255, 255, 0.8); box-shadow: 10px 10px 20px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }
    .ai-box { background: linear-gradient(145deg, #ffffff, #e6e6e6); border-right: 6px solid #424242; padding: 20px; border-radius: 12px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. إدارة الزوار والـ API ---
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

try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_KEY"

# --- 3. محرك الحسابات ---
def calculate_all_stats(row):
    try:
        h_odd, a_odd, d_odd = row['1'], row['2'], row['X']
        h_p, a_p, d_p = (1/h_odd), (1/a_odd), (1/d_odd)
        total = h_p + a_p + d_p
        tightness = 1 - abs((h_p/total) - (a_p/total))
        h_cards = round(1.2 + (tightness * 1.5), 1)
        a_cards = round(1.4 + (tightness * 1.5), 1)
        red_p = int((tightness * 25) + 5)
        o_25, u_25 = row['أكثر 2.5'], row['أقل 2.5']
        prob_u = (1/u_25) / ((1/o_25) + (1/u_25))
        xg = 1.9 if prob_u > 0.55 else 3.5 if prob_u < 0.30 else 2.7
        return {"p1": (h_p/total)*100, "px": (d_p/total)*100, "p2": (a_p/total)*100, "hc": h_cards, "ac": a_cards, "rp": red_p, "xg": xg}
    except: return None

# --- 4. جلب ومعالجة البيانات ---
@st.cache_data(ttl=3600)
def fetch_data(l_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{l_key}/odds', params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        res = []
        for m in r.json():
            if not m['bookmakers']: continue
            mkts = m['bookmakers'][0]['markets']
            h2h = next((i for i in mkts if i['key'] == 'h2h'), None)
            totals = next((i for i in mkts if i['key'] == 'totals'), None)
            if h2h and totals:
                h_odd = next(o['price'] for o in h2h['outcomes'] if o['name'] == m['home_team'])
                a_odd = next(o['price'] for o in h2h['outcomes'] if o['name'] == m['away_team'])
                d_odd = next(o['price'] for o in h2h['outcomes'] if o['name'] == 'Draw')
                o_25 = next(o['price'] for o in totals['outcomes'] if o['name'] == 'Over')
                u_25 = next(o['price'] for o in totals['outcomes'] if o['name'] == 'Under')
                res.append({"المضيف": m['home_team'], "الضيف": m['away_team'], "1": h_odd, "X": d_odd, "2": a_odd, "أكثر 2.5": o_25, "أقل 2.5": u_25})
        return pd.DataFrame(res)
    except: return pd.DataFrame()

# --- 5. واجهة التطبيق الرئيسية ---
def main():
    visitors = get_unique_visitors()
    st.sidebar.markdown(f'<div style="text-align:center; padding:10px; background:#e0e0e0; border-radius:15px; box-shadow:4px 4px 8px #bebebe;">الزوار الفريدون<br><b>👤 {visitors}</b></div>', unsafe_allow_html=True)
    
    try:
        leagues_raw = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}').json()
        grps = sorted(list(set([s['group'] for s in leagues_raw])))
        if "Soccer" in grps: grps.remove("Soccer"); grps.insert(0, "Soccer")
        sel_grp = st.sidebar.selectbox("🏅 الرياضة", grps)
        l_map = {s['title']: s['key'] for s in leagues_raw if s['group'] == sel_grp}
        sel_l = st.sidebar.selectbox("🏆 البطولة", list(l_map.keys()))
    except: st.error("تأكد من الـ API KEY"); return

    st.title(f"💎 {sel_l}")
    df = fetch_data(l_map[sel_l])
    
    if not df.empty:
        st.subheader("📅 جدول المباريات")
        
        # --- الحل الجذري: إعدادات الأعمدة اليدوية ---
        st.dataframe(
            df[["المضيف", "الضيف", "1", "X", "2"]], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "المضيف": st.column_config.TextColumn("🏠 الفريق المضيف", width="large"),
                "الضيف": st.column_config.TextColumn("✈️ الفريق الضيف", width="large"),
                "1": st.column_config.NumberColumn("1", width="small", format="%.2f"),
                "X": st.column_config.NumberColumn("X", width="small", format="%.2f"),
                "2": st.column_config.NumberColumn("2", width="small", format="%.2f"),
            }
        )
        
        st.markdown("---")
        st.markdown("<div class='crystal-card'>", unsafe_allow_html=True)
        sel_m = st.selectbox("🎯 اختر مباراة للتحليل الإحصائي:", [f"{r['المضيف']} ضد {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_m.split(" ضد ")[0]].iloc[0]
        
        stats = calculate_all_stats(row)
        if stats:
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.subheader("💰 استثمار")
                stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
                sel_opt = st.selectbox("توقعك:", [row['المضيف'], "تعادل", row['الضيف']])
                v_odd = row['1'] if sel_opt==row['المضيف'] else row['X'] if sel_opt=="تعادل" else row['2']
                st.markdown(f"<div style='background:#f5f5f5; padding:10px; border-radius:10px; text-align:center;'>العائد: <b>{(stake*v_odd):.2f}$</b></div>", unsafe_allow_html=True)
            with c2:
                st.subheader("📊 ذكاء المباراة")
                st.markdown(f"""<div class='ai-box'>
                    <b>احتمالات الفوز:</b> {row['المضيف']} ({stats['p1']:.1f}%) | تعادل ({stats['px']:.1f}%) | {row['الضيف']} ({stats['p2']:.1f}%) <br>
                    <b>رادار البطاقات:</b> 🟨 للأرض {stats['hc']} | 🟨 للضيف {stats['ac']} | 🟥 طرد {stats['rp']}% <br>
                    <b>معدل الأهداف (xG):</b> {stats['xg']:.2f}
                </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

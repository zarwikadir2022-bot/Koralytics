import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | Ultimate Visual",
    page_icon="⚽",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .ai-box {background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 6px solid #0083B8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .ticket-box {background-color: #2b313e; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;}
    .ticket-item {border-bottom: 1px solid #555; padding-bottom: 5px; margin-bottom: 5px; font-size: 0.9em;}
    .profit-box {background-color: #d1e7dd; padding: 15px; border-radius: 10px; border: 1px solid #badbcc; color: #0f5132; margin-top: 10px;}
    .advisor-box {background-color: #fff3cd; padding: 10px; border-radius: 8px; border: 1px solid #ffecb5; color: #856404; margin-top: 10px; font-size: 0.9em;}
    a[href*="wa.me"] button {background-color: #25D366 !important; border-color: #25D366 !important; color: white !important;}
    .magic-btn button {background: linear-gradient(45deg, #833ab4, #fd1d1d, #fcb045); color: white !important; border: none; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات المفاتيح ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
    RAPID_KEY = st.secrets["RAPID_API_KEY"]
except:
    API_KEY = "YOUR_ODDS_KEY"
    RAPID_KEY = "YOUR_RAPID_KEY"

MY_PHONE_NUMBER = "21600000000"

# --- 3. إدارة الجلسات ---
@st.cache_resource
def get_active_sessions(): return {}

def manage_session_lock(key):
    active_sessions = get_active_sessions()
    current_time = time.time()
    TIMEOUT = 60 
    keys_to_remove = [k for k, t in active_sessions.items() if current_time - t > TIMEOUT]
    for k in keys_to_remove: del active_sessions[k]

    if key in active_sessions:
        if current_time - active_sessions[key] < TIMEOUT:
            if st.session_state.get("current_key") == key:
                active_sessions[key] = current_time 
                return True, ""
            else: return False, "⚠️ المفتاح مشغول."
    active_sessions[key] = current_time
    return True, ""

def logout_user():
    st.session_state["password_correct"] = False
    st.session_state["current_key"] = None
    st.session_state["my_ticket"] = [] 
    st.rerun()

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

# --- 4. جلب الشعارات (Cache 7 days) ---
@st.cache_data(ttl=604800, show_spinner=False)
def get_team_logo(team_name):
    if RAPID_KEY == "YOUR_RAPID_KEY": return None
    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
    querystring = {"search": team_name}
    headers = {"X-RapidAPI-Key": RAPID_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        if data['results'] > 0: return data['response'][0]['team']['logo']
        return "https://cdn-icons-png.flaticon.com/512/10542/10542547.png"
    except: return "https://cdn-icons-png.flaticon.com/512/10542/10542547.png"

# --- 5. محرك الذكاء الاصطناعي ---
def calculate_exact_goals(over_odd, under_odd):
    if over_odd == 0 or under_odd == 0: return {}, None
    prob_over = 1 / over_odd
    prob_under = 1 / under_odd
    margin = prob_over + prob_under
    fair_prob_under = prob_under / margin
    if fair_prob_under > 0.55: expected_goals = 1.9
    elif fair_prob_under > 0.45: expected_goals = 2.4
    elif fair_prob_under < 0.30: expected_goals = 3.3
    else: expected_goals = 2.8
    goals_probs = {}
    for k in range(5): goals_probs[k] = poisson.pmf(k, expected_goals) * 100
    return goals_probs, expected_goals

def ai_analyst_report(match_row, expected_goals):
    home = match_row['المضيف']
    away = match_row['الضيف']
    h_odd = match_row['1']
    a_odd = match_row['2']
    h_prob = (1/h_odd * 100) if h_odd > 0 else 0
    a_prob = (1/a_odd * 100) if a_odd > 0 else 0
    
    report = f"#### 🤖 تقرير التحليل الاستراتيجي\n\n"
    report += "**1️⃣ ميزان القوى:**\n"
    risk = 5 
    if h_prob > 60: risk = 9; report += f"• **هيمنة:** {home}.\n"
    elif a_prob > 60: risk = 9; report += f"• **هيمنة:** {away}.\n"
    elif abs(h_prob - a_prob) < 10: risk = 4; report += f"• **متكافئة جداً.**\n"
    else: risk = 7; report += f"• **أفضلية:** {home if h_prob > a_prob else away}.\n"

    report += "\n**2️⃣ الأهداف:**\n"
    score_pred = "غير متوفر"
    if expected_goals:
        if expected_goals >= 2.8: report += "• نمط مفتوح (Over).\n"; score_pred = "2-1 / 3-1"
        elif expected_goals <= 2.1: report += "• نمط مغلق (Under).\n"; score_pred = "1-0 / 0-1"
        else: report += "• نمط متوازن.\n"; score_pred = "1-1 / 2-1"
    
    report += f"\n**3️⃣ الأمان:** {risk}/10"
    return report, risk

# --- 6. الحماية ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2: 
        st.title("🏆 Koralytics Pro")
        with st.form("login_form"):
            password_input = st.text_input("مفتاح الدخول:", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                if "passwords" in st.secrets and password_input in st.secrets["passwords"].values():
                    is_allowed, msg = manage_session_lock(password_input)
                    if is_allowed:
                        st.session_state["password_correct"] = True
                        st.session_state["current_key"] = password_input
                        st.rerun()
                    else: st.error(msg)
                else: st.error("❌ خطأ Secrets أو كلمة المرور")
    return False

# --- 7. جلب البيانات والمعالجة ---
@st.cache_data(ttl=3600)
def fetch_odds(sport_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        return (r.json(), None) if r.status_code == 200 else (None, str(r.status_code))
    except Exception as e: return None, str(e)

def process_data_with_logos(raw_data):
    matches = []
    for match in raw_data:
        if not match['bookmakers']: continue
        raw_date = match['commence_time'].replace('T', ' ')[:16]
        mkts = match['bookmakers'][0]['markets']
        
        h2h = next((m for m in mkts if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)
        
        totals = next((m for m in mkts if m['key'] == 'totals'), None)
        over_25 = under_25 = 0.0
        if totals:
            outcomes = totals['outcomes']
            over_25 = next((x['price'] for x in outcomes if x['name'] == 'Over' and x['point'] == 2.5), 0)
            under_25 = next((x['price'] for x in outcomes if x['name'] == 'Under' and x['point'] == 2.5), 0)
        
        # جلب الشعارات
        h_logo = get_team_logo(match['home_team'])
        a_logo = get_team_logo(match['away_team'])
        
        matches.append({
            "التوقيت": raw_date,
            "H_Logo": h_logo, "المضيف": match['home_team'], 
            "A_Logo": a_logo, "الضيف": match['away_team'],
            "1": h_odd, "X": d_odd, "2": a_odd,
            "O 2.5": over_25, "U 2.5": under_25
        })
    return pd.DataFrame(matches)

# --- 8. التطبيق الرئيسي ---
def main():
    if not check_password(): return

    # --- القائمة الجانبية ---
    with st.sidebar:
        st.header("💎 لوحة التحكم")
        if st.button("🔴 خروج"): logout_user()
        
        # Ticket Section
        st.subheader("🧾 ورقتي")
        if st.session_state["my_ticket"]:
            total_odd = 1.0
            ticket_txt = "🚀 *Koralytics Ticket:*\n"
            st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
            for item in st.session_state["my_ticket"]:
                st.markdown(f"<div class='ticket-item'>✅ {item['pick']} <b style='float:right'>{item['odd']}</b></div>", unsafe_allow_html=True)
                total_odd *= item['odd']
                ticket_txt += f"✅ {item['pick']} @ {item['odd']}\n"
            st.markdown('</div>', unsafe_allow_html=True)
            st.metric("Total Odds", f"{total_odd:.2f}")
            
            wa_url = f"https://wa.me/?text={urllib.parse.quote(ticket_txt)}"
            st.link_button("📲 واتساب", wa_url, use_container_width=True)
            if st.button("🗑️ مسح"): st.session_state["my_ticket"] = []; st.rerun()
            
        st.divider()
        # API Data
        try:
            r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}')
            active = r.json()
            groups = sorted(list(set([s['group'] for s in active])))
            grp = st.selectbox("الرياضة", groups)
            leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
            lname = st.selectbox("البطولة", list(leagues.keys()))
            lkey = leagues[lname]
        except: st.error("API Error"); return

        st.divider()
        # Magic Wand & Settings
        st.markdown('<div class="magic-btn">', unsafe_allow_html=True)
        if st.button("🪄 العصا السحرية (Auto-Pick)"): st.session_state["magic_trigger"] = True
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        budget = st.number_input("💵 ميزانيتك ($):", 100.0, 50000.0, 500.0, step=50.0)
        show_gold = st.checkbox("🔥 عرض الفرص الذهبية فقط") # (تمت إعادتها)

    # --- المحتوى الرئيسي ---
    st.subheader(f"⚽ {lname}")
    data, error = fetch_odds(lkey)
    
    if data:
        df = process_data_with_logos(data)
        
        # Gold Filter Logic (تمت إعادتها)
        if show_gold and not df.empty:
            df = df[((1/df['1']) > 0.65) | ((1/df['2']) > 0.65)]
            if df.empty: st.warning("لا توجد فرص ذهبية.")

        # Magic Wand Logic
        if st.session_state.get("magic_trigger") and not df.empty:
            st.session_state["my_ticket"] = []
            candidates = []
            for i, row in df.iterrows():
                if row['1'] > 1.05 and (1/row['1']) > 0.60:
                    candidates.append({"pick": f"Win {row['المضيف']}", "odd": row['1'], "prob": 1/row['1']})
                if row['2'] > 1.05 and (1/row['2']) > 0.60:
                    candidates.append({"pick": f"Win {row['الضيف']}", "odd": row['2'], "prob": 1/row['2']})
            candidates.sort(key=lambda x: x['prob'], reverse=True)
            st.session_state["my_ticket"] = candidates[:3]
            st.session_state["magic_trigger"] = False
            st.rerun()

        # Display Table with Logos
        if not df.empty:
            st.dataframe(
                df,
                column_config={
                    "H_Logo": st.column_config.ImageColumn("شعار", width="small"),
                    "A_Logo": st.column_config.ImageColumn("شعار", width="small"),
                    "1": st.column_config.NumberColumn("1 (Home)", format="%.2f"),
                    "X": st.column_config.NumberColumn("X (Draw)", format="%.2f"),
                    "2": st.column_config.NumberColumn("2 (Away)", format="%.2f"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            # Analysis Area
            c1, c2 = st.columns([1, 1.5])
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel = st.selectbox("اختر المباراة للتحليل:", matches_txt)
                host = sel.split(" vs ")[0]
                row = df[df['المضيف'] == host].iloc[0]
                
                # Big Logos
                col_img1, col_vs, col_img2 = st.columns([1,1,1])
                with col_img1: st.image(row['H_Logo'], width=80)
                with col_img2: st.image(row['A_Logo'], width=80)
                
                # Betting & Advisor
                st.markdown("### 💰 حاسبة الربح")
                bet_type = st.radio("نوع الرهان", ["فوز (1X2)", "أهداف (O/U)"], horizontal=True)
                if bet_type == "فوز (1X2)":
                    opts = {f"فوز {row['المضيف']}": row['1'], "تعادل": row['X'], f"فوز {row['الضيف']}": row['2']}
                else:
                    opts = {"Over 2.5": row['O 2.5'], "Under 2.5": row['U 2.5']}
                
                sel_opt = st.selectbox("النتيجة", list(opts.keys()))
                val_odd = opts[sel_opt]
                
                # زر الإضافة للورقة
                if st.button(f"➕ أضف للورقة (@ {val_odd})", use_container_width=True):
                    st.session_state["my_ticket"].append({"pick": sel_opt, "odd": val_odd})
                    st.toast("✅ تمت الإضافة")
                    time.sleep(0.5); st.rerun()
                
                # حاسبة فردية (تمت إعادتها)
                stake = st.number_input("رهان فردي ($):", 1.0, 1000.0, 10.0)
                st.markdown(f"<div class='profit-box'>الربح المتوقع: <b>{(stake * val_odd):.2f}$</b></div>", unsafe_allow_html=True)

            with c2:
                # AI Report & Kelly Advisor (تم دمج المستشار هنا)
                probs, exp_goals = calculate_exact_goals(row['O 2.5'], row['U 2.5'])
                report, risk = ai_analyst_report(row, exp_goals)
                
                st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)

                # Kelly Advisor Logic (تمت إعادتها)
                rec_msg = "مغامرة!" if risk < 5 else "آمنة."
                rec_amount = budget * (3 if risk > 7 else 1) / 100
                st.markdown(f"""<div class="advisor-box">💡 <b>المستشار المالي:</b><br>هذه الفرصة {rec_msg} ({risk}/10).<br>المبلغ المقترح: {rec_amount:.1f}$</div>""", unsafe_allow_html=True)

if __name__ == '__main__': main()

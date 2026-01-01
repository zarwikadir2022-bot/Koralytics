import streamlit as st
import pandas as pd
import requests
import time
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | Pro Analyst",
    page_icon="🧠",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .ai-box {
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 6px solid #0083B8; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .profit-box {background-color: #d1e7dd; padding: 15px; border-radius: 10px; border: 1px solid #badbcc; color: #0f5132; margin-top: 10px;}
    a[href*="wa.me"] button {background-color: #25D366 !important; border-color: #25D366 !important; color: white !important;}
    .stButton>button {border-radius: 8px;}
    h4 {color: #0083B8;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات المطور ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY"

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
            else: return False, "⚠️ المفتاح مشغول. انتظر دقيقة."
    active_sessions[key] = current_time
    return True, ""

def logout_user():
    key = st.session_state.get("current_key")
    if key and key in get_active_sessions(): del get_active_sessions()[key]
    st.session_state["password_correct"] = False
    st.session_state["current_key"] = None
    st.rerun()

# --- 4. محرك الذكاء الاصطناعي المطور (Advanced AI Engine) ---

def calculate_exact_goals(over_odd, under_odd):
    prob_over = 1 / over_odd
    prob_under = 1 / under_odd
    margin = prob_over + prob_under
    fair_prob_under = prob_under / margin
    
    if fair_prob_under > 0.55: expected_goals = 1.9  # دفاعية جداً
    elif fair_prob_under > 0.45: expected_goals = 2.4 # متوسطة
    elif fair_prob_under < 0.30: expected_goals = 3.3 # هجومية جداً
    else: expected_goals = 2.8
        
    goals_probs = {}
    for k in range(5):
        goals_probs[k] = poisson.pmf(k, expected_goals) * 100
    return goals_probs, expected_goals

def ai_analyst_report(match_row, expected_goals):
    """
    النسخة المطورة: تحليل عميق وتوقعات دقيقة
    """
    home = match_row['المضيف']
    away = match_row['الضيف']
    h_odd = match_row['فوز المضيف (1)']
    d_odd = match_row['تعادل (X)']
    a_odd = match_row['فوز الضيف (2)']
    
    # 1. حساب الاحتمالات الضمنية
    h_prob = (1/h_odd) * 100
    a_prob = (1/a_odd) * 100
    d_prob = (1/d_odd) * 100
    
    # 2. تحديد السيناريو (Logic)
    report = f"#### 🤖 تقرير التحليل الاستراتيجي\n\n"
    
    # -- القسم 1: ميزان القوى --
    report += "**1️⃣ ميزان القوى:**\n"
    if h_prob > 60:
        report += f"• **هيمنة مطلقة:** البيانات تشير لسيطرة كاملة لفريق **{home}**. احتمال المفاجأة ضعيف جداً.\n"
        risk = 9 # آمن جداً
    elif a_prob > 60:
        report += f"• **هيمنة مطلقة:** البيانات تشير لسيطرة كاملة لفريق **{away}** خارج الديار.\n"
        risk = 9
    elif abs(h_prob - a_prob) < 10:
        report += f"• **معركة تكتيكية:** الفريقان متقاربان جداً في المستوى. التعادل هو الخطر الأكبر هنا.\n"
        risk = 4 # خطر
    else:
        fav = home if h_prob > a_prob else away
        report += f"• **أفضلية واضحة:** الكفة تميل لصالح **{fav}** ولكن الخصم ليس سهلاً.\n"
        risk = 7

    # -- القسم 2: سيناريو الأهداف --
    report += "\n**2️⃣ سيناريو الأهداف:**\n"
    report += f"• **المعدل المتوقع:** حوالي {expected_goals:.1f} هدف.\n"
    
    score_pred = ""
    if expected_goals >= 2.8:
        report += "• **النمط:** مباراة مفتوحة (Open Game). الدفاعات ستعاني. خيار (BTTS - كلا الفريقين يسجل) وارد بقوة.\n"
        # توزيع الأهداف للتوقع
        if h_prob > a_prob: score_pred = "2-1 أو 3-1"
        else: score_pred = "1-2 أو 1-3"
    elif expected_goals <= 2.1:
        report += "• **النمط:** مباراة شحيحة الفرص (Park the Bus). هدف واحد قد يحسم اللقاء.\n"
        if h_prob > a_prob: score_pred = "1-0 أو 2-0"
        elif a_prob > h_prob: score_pred = "0-1 أو 0-2"
        else: score_pred = "0-0 أو 1-1"
    else:
        report += "• **النمط:** مباراة متوازنة. غالباً ستشهد بين 2 إلى 3 أهداف.\n"
        if h_prob > a_prob: score_pred = "2-0 أو 2-1"
        else: score_pred = "0-2 أو 1-2"

    # -- القسم 3: التوصية النهائية --
    report += "\n**3️⃣ توصية الخوارزمية:**\n"
    if risk >= 8:
        report += f"✅ **خيار آمن (Banker):** فوز {home if h_prob > a_prob else away}.\n"
    elif risk <= 4:
        report += f"⚠️ **مخاطرة:** يُفضل تجنب تحديد الفائز واللعب على (Under 3.5 Goals) أو (Double Chance).\n"
    else:
        report += f"⚖️ **خيار متوازن:** فوز {home if h_prob > a_prob else away}.\n"
        
    report += f"🎯 **النتيجة الرقمية المتوقعة:** ({score_pred})\n"
    report += f"🛡️ **درجة الأمان:** {risk}/10"
        
    return report

# --- 5. نظام الدخول والحماية ---
def check_password():
    if st.session_state.get("password_correct", False):
        key = st.session_state.get("current_key")
        is_allowed, msg = manage_session_lock(key)
        if not is_allowed: st.error(msg); st.stop()
        return True

    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2: 
        st.image("https://cdn-icons-png.flaticon.com/512/3593/3593510.png", width=80)
        st.title("💎 Koralytics AI")
        st.info("💡 التحليل الرياضي العميق (Pro Version).")
        wa_link = f"https://wa.me/{MY_PHONE_NUMBER}?text=شراء مفتاح"
        st.link_button("📲 شراء مفتاح (WhatsApp)", wa_link, use_container_width=True)
        
        with st.form("login_form"):
            password_input = st.text_input("مفتاح الدخول:", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                if "passwords" not in st.secrets: st.error("⚠️ خطأ Secrets")
                else:
                    if password_input in st.secrets["passwords"].values():
                        is_allowed, error_msg = manage_session_lock(password_input)
                        if is_allowed:
                            st.session_state["password_correct"] = True
                            st.session_state["current_key"] = password_input
                            st.success("✅"); time.sleep(0.5); st.rerun()
                        else: st.error(error_msg)
                    else: st.error("❌ خطأ")
    return False

# --- 6. API & Data ---
@st.cache_data(ttl=86400)
def get_active_sports():
    if API_KEY == "YOUR_API_KEY": return []
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}')
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(sport_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        return (r.json(), None) if r.status_code == 200 else (None, str(r.status_code))
    except Exception as e: return None, str(e)

def process_data(raw_data):
    matches = []
    for match in raw_data:
        if not match['bookmakers']: continue
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
        matches.append({
            "المضيف": match['home_team'], "الضيف": match['away_team'],
            "فوز المضيف (1)": h_odd, "تعادل (X)": d_odd, "فوز الضيف (2)": a_odd,
            "Over 2.5": over_25, "Under 2.5": under_25
        })
    return pd.DataFrame(matches)

# --- 7. Main App ---
def show_app_content():
    manage_session_lock(st.session_state["current_key"])

    with st.sidebar:
        st.header("💎 لوحة التحكم")
        if st.button("🔴 تسجيل الخروج"): logout_user()
        if st.session_state.get("current_key") == "admin2026": 
            if st.button("تصفير الجلسات"): get_active_sessions().clear(); st.success("تم!")
        st.divider()
        active = get_active_sports()
        if not active: st.error("API Error"); return
        groups = sorted(list(set([s['group'] for s in active])))
        grp = st.selectbox("الرياضة:", groups)
        leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
        lname = st.selectbox("البطولة:", list(leagues.keys()))
        lkey = leagues[lname]

    st.subheader(f"📊 تحليل: {lname}")
    data, error = fetch_odds(lkey)
    
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات.")
    else:
        df = process_data(data)
        if not df.empty:
            st.dataframe(df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens').format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']), use_container_width=True)
            st.divider()
            
            # --- منطقة التحليل والربح ---
            st.subheader("🧠 غرفة المحلل الذكي & حاسبة الربح")
            c1, c2 = st.columns([1, 1.3])
            
            # العمود 1: المدخلات والربح
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("1️⃣ اختر المباراة:", matches_txt)
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]

                st.markdown("### 💰 حاسبة الربح")
                bet_cat = st.radio("الرهان:", ["الفائز (1X2)", "Over/Under"], horizontal=True)
                selected_odd = 0.0
                selection_name = ""
                
                if bet_cat == "الفائز (1X2)":
                    opts = {f"فوز {match_row['المضيف']} ({match_row['فوز المضيف (1)']})": match_row['فوز المضيف (1)'], f"تعادل ({match_row['تعادل (X)']})": match_row['تعادل (X)'], f"فوز {match_row['الضيف']} ({match_row['فوز الضيف (2)']})": match_row['فوز الضيف (2)']}
                    choice = st.selectbox("النتيجة:", list(opts.keys()))
                    selected_odd = opts[choice]
                    selection_name = choice
                else:
                    opts = {f"Over 2.5 ({match_row['Over 2.5']})": match_row['Over 2.5'], f"Under 2.5 ({match_row['Under 2.5']})": match_row['Under 2.5']}
                    choice = st.selectbox("النتيجة:", list(opts.keys()))
                    selected_odd = opts[choice]
                    selection_name = choice
                
                stake = st.number_input("المبلغ ($):", min_value=1.0, value=10.0, step=1.0)
                if selected_odd > 0:
                    ret = stake * selected_odd
                    prof = ret - stake
                    st.markdown(f"""
                    <div class="profit-box">
                        <ul style="margin:0; padding-left:20px">
                            <li>العائد: <b>{ret:.2f}$</b></li>
                            <li><b>صافي الربح: {prof:.2f}$ 🤑</b></li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

            # العمود 2: التقرير المفصل والرسوم
            with c2:
                goals_probs = {}
                if match_row['Over 2.5'] > 0:
                    goals_probs, expected_goals = calculate_exact_goals(match_row['Over 2.5'], match_row['Under 2.5'])
                    
                    # عرض التقرير الجديد المفصل
                    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                    st.markdown(ai_analyst_report(match_row, expected_goals))
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("**🔵 احتمالية الفوز:**")
                h_prob = (1 / match_row['فوز المضيف (1)']) * 100
                d_prob = (1 / match_row['تعادل (X)']) * 100
                a_prob = (1 / match_row['فوز الضيف (2)']) * 100
                chart_df = pd.DataFrame({'Team': [match_row['المضيف'], 'Draw', match_row['الضيف']], 'Prob': [h_prob, d_prob, a_prob]}).set_index('Team')
                st.bar_chart(chart_df, color="#0083B8", height=200)

                if goals_probs:
                    st.markdown("**🔴 توقعات الأهداف:**")
                    goals_df = pd.DataFrame(list(goals_probs.items()), columns=['G', 'P']).set_index('G')
                    st.bar_chart(goals_df, color="#FF4B4B", height=200)

def main():
    if check_password(): show_app_content()

if __name__ == '__main__': main()

import streamlit as st
import pandas as pd
import requests
import time
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | المحلل الذكي",
    page_icon="🧠",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .ai-box {background-color: #e8f4f8; padding: 15px; border-radius: 10px; border-left: 5px solid #0083B8; margin-bottom: 20px;}
    a[href*="wa.me"] button {background-color: #25D366 !important; border-color: #25D366 !important; color: white !important;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات المطور ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY"

MY_PHONE_NUMBER = "21600000000" 

# --- 3. محرك الذكاء الاصطناعي والإحصاء ---

def calculate_exact_goals(over_odd, under_odd):
    """حساب احتمالات الأهداف الدقيقة (0-4+)"""
    prob_over = 1 / over_odd
    prob_under = 1 / under_odd
    margin = prob_over + prob_under
    fair_prob_under = prob_under / margin
    
    if fair_prob_under > 0.5: expected_goals = 2.0
    elif fair_prob_under < 0.3: expected_goals = 3.2
    else: expected_goals = 2.7
        
    goals_probs = {}
    for k in range(5):
        goals_probs[k] = poisson.pmf(k, expected_goals) * 100
    goals_probs['4+'] = (1 - poisson.cdf(3, expected_goals)) * 100
    
    return goals_probs, expected_goals

def ai_analyst_report(match_row, expected_goals):
    """توليد التقرير النصي"""
    home = match_row['المضيف']
    away = match_row['الضيف']
    h_odd = match_row['فوز المضيف (1)']
    a_odd = match_row['فوز الضيف (2)']
    
    report = f"**🤖 تقرير المحلل الذكي:**\n\n"
    
    # تحليل الفائز
    if h_odd < 1.5: report += f"• **النتيجة:** البيانات ترشح **{home}** باكتساح.\n"
    elif a_odd < 1.5: report += f"• **النتيجة:** البيانات ترشح **{away}** باكتساح.\n"
    elif abs(h_odd - a_odd) < 0.5: report += f"• **النتيجة:** مباراة صعبة جداً (Derby). التعادل وارد.\n"
    else:
        fav = home if h_odd < a_odd else away
        report += f"• **النتيجة:** الأفضلية لـ **{fav}**.\n"
        
    # تحليل الأهداف
    report += f"• **معدل الأهداف:** {expected_goals} هدف.\n"
    if expected_goals > 2.9: report += "• **النمط:** مباراة هجومية مفتوحة (Over).\n"
    elif expected_goals < 2.2: report += "• **النمط:** مباراة دفاعية مغلقة (Under).\n"
    else: report += "• **النمط:** نسق متوسط.\n"
        
    return report

# --- 4. نظام الحماية ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3593/3593510.png", width=80)
        st.title("💎 Koralytics AI")
        st.info("💡 التحليل بالذكاء الاصطناعي وتوقعات الأهداف.")
        wa_link = f"https://wa.me/{MY_PHONE_NUMBER}?text=مرحبا"
        st.link_button("📲 شراء مفتاح اشتراك", wa_link, use_container_width=True)
        with st.form("login_form"):
            password_input = st.text_input("مفتاح الدخول:", type="password")
            if st.form_submit_button("دخول", use_container_width=True):
                try:
                    if password_input in st.secrets["passwords"].values():
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else: st.error("❌ خطأ")
                except: st.error("⚠️ خطأ Secrets")
    return False

# --- 5. دوال البيانات ---
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

# --- 6. الواجهة الرئيسية ---
def show_app_content():
    with st.sidebar:
        st.header("💎 التحكم")
        if st.button("خروج"): st.session_state["password_correct"] = False; st.rerun()
        active = get_active_sports()
        if not active: st.error("API Error"); return
        groups = sorted(list(set([s['group'] for s in active])))
        grp = st.selectbox("الرياضة:", groups)
        leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
        lname = st.selectbox("البطولة:", list(leagues.keys()))
        lkey = leagues[lname]
        st.divider()
        budget = st.number_input("المحفظة ($)", 100.0, 10000.0, 1000.0)

    st.subheader(f"📊 تحليل: {lname}")
    data, error = fetch_odds(lkey)
    
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات.")
    else:
        df = process_data(data)
        if not df.empty:
            st.dataframe(df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens').format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']), use_container_width=True)
            
            st.divider()
            st.subheader("🧠 غرفة المحلل الذكي (AI Room)")
            
            c1, c2 = st.columns([1, 1.5])
            
            # --- العمود الأول: التقرير النصي ---
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر المباراة للتحليل:", matches_txt)
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]
                
                # حسابات الأهداف
                goals_probs = {}
                expected_goals = 0
                if match_row['Over 2.5'] > 0:
                    goals_probs, expected_goals = calculate_exact_goals(match_row['Over 2.5'], match_row['Under 2.5'])
                    
                    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                    st.markdown(ai_analyst_report(match_row, expected_goals))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("بيانات الأهداف غير متوفرة.")

            # --- العمود الثاني: الرسوم البيانية (تمت إعادة الرسم المفقود) ---
            with c2:
                # 1. رسم احتمالات الفوز (Win Probability) - عاد من جديد!
                st.write("🔵 **احتمالية الفوز (Win Probability):**")
                
                # نحول الـ Odds إلى نسبة مئوية (Prob = 1/Odd) لتكون منطقية في الرسم
                h_prob = (1 / match_row['فوز المضيف (1)']) * 100
                d_prob = (1 / match_row['تعادل (X)']) * 100
                a_prob = (1 / match_row['فوز الضيف (2)']) * 100
                
                win_chart_df = pd.DataFrame({
                    'Team': [match_row['المضيف'], 'Draw', match_row['الضيف']],
                    'Probability (%)': [h_prob, d_prob, a_prob]
                }).set_index('Team')
                
                st.bar_chart(win_chart_df, color="#0083B8") # لون أزرق

                st.divider()

                # 2. رسم الأهداف (Exact Goals)
                if goals_probs:
                    st.write("🔴 **توقعات عدد الأهداف (Exact Goals):**")
                    goals_df = pd.DataFrame(list(goals_probs.items()), columns=['الأهداف', 'الاحتمال %'])
                    goals_df.set_index('الأهداف', inplace=True)
                    st.bar_chart(goals_df, color="#FF4B4B") # لون أحمر
                    
                    best_goal = max(goals_probs, key=goals_probs.get)
                    st.caption(f"السيناريو الأقوى: {best_goal} أهداف.")

# --- التشغيل ---
def main():
    if check_password(): show_app_content()

if __name__ == '__main__': main()

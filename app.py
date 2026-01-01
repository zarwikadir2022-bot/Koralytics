import streamlit as st
import pandas as pd
import requests
import time
import numpy as np
from scipy.stats import poisson # مكتبة الحسابات الإحصائية للأهداف

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

# --- 3. محرك الذكاء الاصطناعي والإحصاء (AI Engine) ---

def calculate_exact_goals(over_odd, under_odd):
    """
    استخدام توزيع بواسون لتوقع عدد الأهداف بدقة بناءً على احتمالات Over/Under
    """
    # 1. حساب الاحتمالية الضمنية للسوق
    prob_over = 1 / over_odd
    prob_under = 1 / under_odd
    
    # تصحيح الهامش (Margin removal) للحصول على احتمالات عادلة
    margin = prob_over + prob_under
    fair_prob_under = prob_under / margin
    
    # 2. استنتاج معدل الأهداف المتوقع (Lambda) من احتمالية Under 2.5
    # في توزيع بواسون: Prob(X < 2.5) تعتمد على المعدل lambda
    # معادلة تقريبية عكسية لاستخراج Lambda
    if fair_prob_under > 0.5:
        expected_goals = 2.0 # مباراة مغلقة
    elif fair_prob_under < 0.3:
        expected_goals = 3.2 # مباراة مفتوحة جداً
    else:
        expected_goals = 2.7 # مباراة متوسطة
        
    # 3. توليد احتمالات الأهداف (0, 1, 2, 3, 4+)
    goals_probs = {}
    for k in range(5):
        goals_probs[k] = poisson.pmf(k, expected_goals) * 100
    
    # تجميع 4 أهداف فما فوق
    goals_probs['4+'] = (1 - poisson.cdf(3, expected_goals)) * 100
    
    return goals_probs, expected_goals

def ai_analyst_report(match_row, expected_goals):
    """
    توليد نص تحليلي ذكي بناءً على البيانات
    """
    home = match_row['المضيف']
    away = match_row['الضيف']
    h_odd = match_row['فوز المضيف (1)']
    a_odd = match_row['فوز الضيف (2)']
    
    report = f"**🤖 تقرير المحلل الذكي:**\n\n"
    
    # تحليل الفائز
    if h_odd < 1.5:
        report += f"• **النتيجة:** البيانات ترشح **{home}** باكتساح. المخاطرة منخفضة.\n"
    elif a_odd < 1.5:
        report += f"• **النتيجة:** البيانات ترشح **{away}** باكتساح.\n"
    elif abs(h_odd - a_odd) < 0.5:
        report += f"• **النتيجة:** مباراة معقدة ومتقاربة جداً (Derby Style). التعادل وارد بقوة.\n"
    else:
        fav = home if h_odd < a_odd else away
        report += f"• **النتيجة:** الأفضلية تميل لـ **{fav}** ولكن الحذر واجب.\n"
        
    # تحليل الأهداف
    report += f"• **معدل الأهداف المتوقع:** {expected_goals} هدف في المباراة.\n"
    if expected_goals > 2.9:
        report += "• **السيناريو:** نتوقع مباراة مفتوحة وهجومية (Open Game). خيار Over 2.5 ممتاز.\n"
    elif expected_goals < 2.2:
        report += "• **السيناريو:** نتوقع مباراة تكتيكية مغلقة دفاعياً (Under).\n"
    else:
        report += "• **السيناريو:** النسق سيكون متوسطاً.\n"
        
    return report

# --- 4. نظام الحماية ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3593/3593510.png", width=80)
        st.title("💎 Koralytics AI")
        st.info("💡 التحليل بالذكاء الاصطناعي وتوقعات الأهداف الدقيقة.")
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
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر المباراة للتحليل:", matches_txt)
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]
                
                # حسابات الذكاء الاصطناعي
                goals_probs = {}
                expected_goals = 0
                if match_row['Over 2.5'] > 0:
                    goals_probs, expected_goals = calculate_exact_goals(match_row['Over 2.5'], match_row['Under 2.5'])
                    
                    # عرض تقرير المحلل
                    st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                    st.markdown(ai_analyst_report(match_row, expected_goals))
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.warning("بيانات الأهداف غير متوفرة لهذه المباراة للتحليل.")

            with c2:
                if goals_probs:
                    st.write("📈 **احتمالية عدد الأهداف (Exact Goals Probability):**")
                    
                    # تحضير بيانات الرسم البياني
                    goals_df = pd.DataFrame(list(goals_probs.items()), columns=['عدد الأهداف', 'الاحتمالية %'])
                    goals_df.set_index('عدد الأهداف', inplace=True)
                    
                    st.bar_chart(goals_df, color="#FF4B4B")
                    
                    # عرض الاحتمال الأقوى كرقم
                    best_goal_count = max(goals_probs, key=goals_probs.get)
                    st.success(f"📌 السيناريو الأكثر احتمالاً: تسجيل **{best_goal_count}** أهداف في المباراة (بنسبة {goals_probs[best_goal_count]:.1f}%).")

# --- التشغيل ---
def main():
    if check_password(): show_app_content()

if __name__ == '__main__': main()

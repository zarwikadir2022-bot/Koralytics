import streamlit as st
import pandas as pd
import requests
import time

# --- 1. إعدادات الصفحة (يجب أن تكون دائماً في الأول) ---
st.set_page_config(
    page_title="Koralytics VIP | نسخة المشتركين",
    page_icon="💎",
    layout="wide"
)

# تنسيق CSS للشاشة
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .login-box {padding: 20px; border-radius: 10px; background-color: #f0f2f6; text-align: center;}
</style>
""", unsafe_allow_html=True)

# --- 2. نظام الحماية (Authentication) ---

def check_password():
    """دالة التحقق من مفتاح الاشتراك"""
    
    # إذا كان المستخدم قد سجل دخوله سابقاً
    if st.session_state.get("password_correct", False):
        return True

    # واجهة تسجيل الدخول
    st.header("🔒 منطقة المشتركين فقط")
    st.write("هذا التطبيق خاص. يرجى إدخال مفتاح الاشتراك للمتابعة.")
    
    password_input = st.text_input("أدخل مفتاح الاشتراك (Access Key):", type="password")
    
    if st.button("تسجيل الدخول"):
        # جلب كلمات المرور من Secrets
        try:
            valid_passwords = st.secrets["passwords"].values()
        except:
            st.error("خطأ في إعدادات النظام (Secrets).")
            return False

        if password_input in valid_passwords:
            st.session_state["password_correct"] = True
            st.success("✅ تم تسجيل الدخول بنجاح! جاري التحميل...")
            time.sleep(1) # لحظة انتظار جمالية
            st.rerun() # إعادة تحميل الصفحة للدخول
        else:
            st.error("❌ مفتاح خاطئ. يرجى التأكد من الاشتراك.")
            
    return False

# --- 3. دوال التطبيق الأصلية (Backend) ---
# (نفس الدوال السابقة، لم نغير فيها شيئاً)

try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY"

@st.cache_data(ttl=86400)
def get_active_sports():
    if API_KEY == "YOUR_API_KEY": return []
    try:
        url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(sport_key, region='eu'):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': API_KEY, 'regions': region, 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return (response.json(), None) if response.status_code == 200 else (None, f"Status: {response.status_code}")
    except Exception as e: return None, str(e)

def process_data(raw_data):
    matches = []
    for match in raw_data:
        if not match['bookmakers']: continue
        bookmaker = match['bookmakers'][0]
        markets = bookmaker['markets']
        
        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)

        totals = next((m for m in markets if m['key'] == 'totals'), None)
        over_25 = under_25 = 0.0
        if totals:
            outcomes = totals['outcomes']
            over_25 = next((x['price'] for x in outcomes if x['name'] == 'Over' and x['point'] == 2.5), 0)
            under_25 = next((x['price'] for x in outcomes if x['name'] == 'Under' and x['point'] == 2.5), 0)

        matches.append({
            "التاريخ": match['commence_time'][:10],
            "المضيف": match['home_team'],
            "الضيف": match['away_team'],
            "فوز المضيف (1)": h_odd,
            "تعادل (X)": d_odd,
            "فوز الضيف (2)": a_odd,
            "Over 2.5": over_25,
            "Under 2.5": under_25
        })
    return pd.DataFrame(matches)

# --- 4. واجهة المستخدم الرئيسية (The App) ---

def show_app_content():
    # هنا نضع كل كود التطبيق الذي كتبناه سابقاً
    with st.sidebar:
        st.header("💎 Koralytics VIP")
        
        # زر تسجيل الخروج
        if st.button("تسجيل الخروج"):
            st.session_state["password_correct"] = False
            st.rerun()
            
        st.divider()
        st.write("أهلاً بك أيها المشترك المميز.")
        
        # بقية الـ Sidebar
        active_sports = get_active_sports()
        if not active_sports:
            st.error("تأكد من API Key")
            return
        
        groups = sorted(list(set([s['group'] for s in active_sports])))
        selected_group = st.selectbox("الرياضة:", groups)
        filtered_leagues = {s['title']: s['key'] for s in active_sports if s['group'] == selected_group}
        selected_league_name = st.selectbox("البطولة:", list(filtered_leagues.keys()))
        selected_league_key = filtered_leagues[selected_league_name]
        
        st.divider()
        budget = st.number_input("رصيد المحفظة ($)", 100.0, 10000.0, 1000.0)

    # المحتوى الرئيسي
    st.title(f"تحليل حصري: {selected_league_name}")

    data, error = fetch_odds(selected_league_key)
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات.")
    else:
        df = process_data(data)
        if not df.empty:
            st.subheader("📊 جدول الفرص الذهبية")
            try:
                st.dataframe(
                    df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                      .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
                    use_container_width=True
                )
            except: st.dataframe(df, use_container_width=True)

            st.divider()
            
            # قسم المحاكاة
            st.subheader("🧠 المختبر")
            c1, c2 = st.columns([1, 2])
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("المباراة:", matches_txt)
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]
                
                bet_type = st.radio("السوق:", ["1X2", "Over/Under"])
                user_odd = 0.0
                if bet_type == "1X2":
                    choice = st.selectbox("توقعك:", ["فوز المضيف", "تعادل", "فوز الضيف"])
                    if choice == "فوز المضيف": user_odd = match_row['فوز المضيف (1)']
                    elif choice == "تعادل": user_odd = match_row['تعادل (X)']
                    else: user_odd = match_row['فوز الضيف (2)']
                else:
                    choice = st.selectbox("العدد:", ["Over 2.5", "Under 2.5"])
                    if "Over" in choice: user_odd = match_row['Over 2.5']
                    else: user_odd = match_row['Under 2.5']
                
                stake = st.number_input("الرهان ($):", 10.0, float(budget), 50.0)

            with c2:
                if user_odd > 0:
                    implied = (1/user_odd)*100
                    profit = (stake*user_odd)-stake
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Odd", f"{user_odd}")
                    k2.metric("Probability", f"{implied:.1f}%")
                    k3.metric("Profit", f"{profit:.2f}$")
                    
                    if implied > 60: st.success("خيار آمن (Low Risk)")
                    elif implied < 30: st.warning("مخاطرة عالية (High Risk)")
                    else: st.info("متوازن")

# --- 5. تشغيل البرنامج (Main Entry Point) ---

def main():
    # هنا يتم التحقق أولاً قبل عرض أي شيء
    if not check_password():
        st.stop()  # إيقاف التنفيذ إذا لم يسجل الدخول
    
    # إذا نجح الدخول، نعرض التطبيق
    show_app_content()

if __name__ == '__main__':
    main()

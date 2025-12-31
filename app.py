import streamlit as st
import pandas as pd
import requests
import time

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics VIP | نسخة المشتركين",
    page_icon="💎",
    layout="centered" # جعلت التصميم متمحوراً في الوسط لتركيز الانتباه عند الدخول
)

# تنسيق CSS (تجميل زر الواتساب وحقل الدخول)
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .login-container {padding: 30px; border-radius: 15px; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    /* جعل زر الواتساب أخضر */
    a[href*="wa.me"] button {
        background-color: #25D366 !important;
        border-color: #25D366 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات المطور (Secrets) ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY"

# رقم هاتفك للواتساب (غيّر هذا الرقم برقمك الحقيقي)
MY_PHONE_NUMBER = "+21694928912" 

# --- 3. نظام الحماية والبوابة التسويقية ---

def check_password():
    """التحقق من الدخول + واجهة البيع"""
    if st.session_state.get("password_correct", False):
        return True

    # --- واجهة الدخول والتسويق ---
    st.image("https://cdn-icons-png.flaticon.com/512/3593/3593510.png", width=80) # أيقونة معبرة
    st.title("💎 Koralytics VIP")
    st.markdown("### المنصة الأولى لتحليل الاحتمالات الرياضية بذكاء.")
    
    st.divider()

    # 1. منطقة البيع (لغير المشتركين)
    st.info("💡 هذه النسخة للمشتركين فقط. هل تريد تحقيق أرباح مدروسة؟")
    
    wa_msg = "مرحبا، أرغب في الحصول على مفتاح اشتراك في Koralytics VIP"
    wa_link = f"https://wa.me/{MY_PHONE_NUMBER}?text={wa_msg.replace(' ', '%20')}"
    
    # زر الواتساب
    st.link_button("📲 اضغط هنا لشراء مفتاح اشتراك (WhatsApp)", wa_link, use_container_width=True)
    
    st.write("--- أو ---")

    # 2. منطقة الدخول (للمشتركين الحاليين)
    with st.form("login_form"):
        st.write("🔐 **لديك مفتاح بالفعل؟ أدخله هنا:**")
        password_input = st.text_input("مفتاح الدخول (Access Key):", type="password")
        submit_btn = st.form_submit_button("تسجيل الدخول", use_container_width=True)
        
        if submit_btn:
            try:
                valid_passwords = st.secrets["passwords"].values()
                if password_input in valid_passwords:
                    st.session_state["password_correct"] = True
                    st.success("✅ مفتاح صحيح! جاري تحويلك...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ المفتاح غير صحيح أو منتهي الصلاحية.")
            except:
                st.error("⚠️ خطأ في النظام: لم يتم ضبط كلمات المرور.")

    return False

# --- 4. دوال التطبيق (Backend) ---
# (نفس الدوال السابقة تماماً)

@st.cache_data(ttl=86400)
def get_active_sports():
    if API_KEY == "YOUR_API_KEY": return []
    try:
        url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
        r = requests.get(url)
        return r.json() if r.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(sport_key, region='eu'):
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {'apiKey': API_KEY, 'regions': region, 'markets': 'h2h,totals', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return (r.json(), None) if r.status_code == 200 else (None, str(r.status_code))
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

# --- 5. واجهة التطبيق الداخلية (تظهر بعد الدخول فقط) ---
def show_app_content():
    # تعديل بسيط: إعادة التخطيط لـ Wide بعد الدخول ليكون الجدول واسعاً
    # ملاحظة: set_page_config يمكن استدعاؤها مرة واحدة فقط، لذا سنستخدم الأعمدة للتنسيق
    
    with st.sidebar:
        st.header("💎 لوحة التحكم")
        if st.button("تسجيل الخروج"):
            st.session_state["password_correct"] = False
            st.rerun()
            
        st.divider()
        active = get_active_sports()
        if not active:
            st.error("API Error")
            return
            
        groups = sorted(list(set([s['group'] for s in active])))
        grp = st.selectbox("الرياضة:", groups)
        leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
        lname = st.selectbox("البطولة:", list(leagues.keys()))
        lkey = leagues[lname]
        
        st.divider()
        budget = st.number_input("المحفظة ($)", 100.0, 10000.0, 1000.0)

    st.subheader(f"تحليل: {lname}")
    data, error = fetch_odds(lkey)
    
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات.")
    else:
        df = process_data(data)
        if not df.empty:
            st.caption("أفضل الفرص المتاحة حالياً:")
            try:
                st.dataframe(
                    df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                      .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
                    use_container_width=True
                )
            except: st.dataframe(df, use_container_width=True)

            st.divider()
            st.subheader("🧠 مختبر المحاكاة")
            c1, c2 = st.columns([1, 2])
            
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر المباراة:", matches_txt)
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
                    st.markdown(f"**تحليل {sel_match}**")
                    if bet_type == "1X2":
                        chart = pd.DataFrame({'Op': [match_row['المضيف'], 'Draw', match_row['الضيف']], 'Odd': [match_row['فوز المضيف (1)'], match_row['تعادل (X)'], match_row['فوز الضيف (2)']]}).set_index('Op')
                        st.bar_chart(chart, color="#0083B8")
                    else:
                        chart = pd.DataFrame({'Op': ['Over 2.5', 'Under 2.5'], 'Odd': [match_row['Over 2.5'], match_row['Under 2.5']]}).set_index('Op')
                        st.bar_chart(chart, color="#25D366")
                    
                    implied = (1/user_odd)*100
                    profit = (stake*user_odd)-stake
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Odd", f"{user_odd}")
                    k2.metric("Prob", f"{implied:.1f}%")
                    k3.metric("Profit", f"{profit:.2f}$")
                    
                    if implied > 60: st.success("✅ فرصة قوية")
                    elif implied < 30: st.warning("🔥 مخاطرة عالية")
                    else: st.info("⚖️ متوازنة")

# --- 6. التشغيل الرئيسي ---
def main():
    if check_password():
        show_app_content()

if __name__ == '__main__':
    main()

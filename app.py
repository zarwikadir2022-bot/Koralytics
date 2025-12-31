import streamlit as st
import pandas as pd
import requests
import time

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics VIP | نسخة المشتركين",
    page_icon="💎",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .stButton>button {width: 100%; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- 2. نظام الحماية ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.header("🔒 منطقة المشتركين فقط")
    st.write("أدخل مفتاح الاشتراك للمتابعة.")
    password_input = st.text_input("Access Key:", type="password")
    
    if st.button("دخول"):
        try:
            valid_passwords = st.secrets["passwords"].values()
            if password_input in valid_passwords:
                st.session_state["password_correct"] = True
                st.success("✅ تم الدخول!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ مفتاح خاطئ")
        except:
            st.error("لم يتم إعداد كلمات المرور في Secrets")
    return False

# --- 3. دوال المعالجة ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY"

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

# --- 4. واجهة التطبيق ---
def show_app_content():
    with st.sidebar:
        st.header("💎 Koralytics VIP")
        if st.button("تسجيل خروج"):
            st.session_state["password_correct"] = False
            st.rerun()
            
        st.divider()
        active = get_active_sports()
        if not active:
            st.error("Check API Key")
            return
            
        groups = sorted(list(set([s['group'] for s in active])))
        grp = st.selectbox("الرياضة:", groups)
        leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
        lname = st.selectbox("البطولة:", list(leagues.keys()))
        lkey = leagues[lname]
        
        st.divider()
        budget = st.number_input("المحفظة ($)", 100.0, 10000.0, 1000.0)

    st.title(f"تحليل: {lname}")
    data, error = fetch_odds(lkey)
    
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات.")
    else:
        df = process_data(data)
        if not df.empty:
            # الجدول
            st.subheader("📊 جدول الفرص")
            try:
                st.dataframe(
                    df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                      .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
                    use_container_width=True
                )
            except: st.dataframe(df, use_container_width=True)

            st.divider()
            
            # قسم التحليل
            st.subheader("🧠 المختبر")
            c1, c2 = st.columns([1, 2])
            
            # --- العمود الأول: المدخلات ---
            with c1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر المباراة:", matches_txt)
                
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]
                
                bet_type = st.radio("السوق:", ["1X2", "Over/Under"])
                
                # منطق اختيار الرهان
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

            # --- العمود الثاني: النتائج والرسم البياني ---
            with c2:
                # 1. الرسم البياني (يظهر دائماً الآن!)
                st.markdown(f"**مقارنة الفرص لـ: {sel_match}**")
                
                if bet_type == "1X2":
                    chart_df = pd.DataFrame({
                        'Option': [match_row['المضيف'], 'Draw', match_row['الضيف']],
                        'Odd': [match_row['فوز المضيف (1)'], match_row['تعادل (X)'], match_row['فوز الضيف (2)']]
                    }).set_index('Option')
                    st.bar_chart(chart_df, color="#0083B8")
                else:
                    chart_df = pd.DataFrame({
                        'Option': ['Over 2.5', 'Under 2.5'],
                        'Odd': [match_row['Over 2.5'], match_row['Under 2.5']]
                    }).set_index('Option')
                    st.bar_chart(chart_df, color="#28a745")

                # 2. بطاقات الأرقام
                if user_odd > 0:
                    st.divider()
                    implied = (1/user_odd)*100
                    profit = (stake*user_odd)-stake
                    
                    k1, k2, k3 = st.columns(3)
                    k1.metric("القيمة (Odd)", f"{user_odd}")
                    k2.metric("الاحتمالية", f"{implied:.1f}%")
                    k3.metric("الربح المتوقع", f"{profit:.2f}$")
                    
                    if implied > 60: st.success("✅ فرصة آمنة إحصائياً")
                    elif implied < 30: st.warning("🔥 مخاطرة عالية")
                    else: st.info("⚖️ فرصة متوازنة")
                else:
                    st.warning("⚠️ لا توجد بيانات لهذا الرهان.")

# --- 5. التشغيل ---
def main():
    if check_password():
        show_app_content()

if __name__ == '__main__':
    main()

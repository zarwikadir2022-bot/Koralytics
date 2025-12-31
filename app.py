import streamlit as st
import pandas as pd
import requests

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(
    page_title="Koralytics | منصة التحليل الذكي",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص CSS بسيط لجعل التطبيق أجمل
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;}
    .stButton>button {width: 100%; border-radius: 5px; background-color: #0083B8; color: white;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات API (الأمان) ---
# ملاحظة للمطور: احصل على المفتاح من https://the-odds-api.com/
# وضعه في st.secrets باسم "ODDS_API_KEY"
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    # مفتاح افتراضي للتجربة فقط (يفضل تغييره)
    API_KEY = "YOUR_API_KEY_HERE" 

# --- 3. دوال المعالجة (Backend Logic) ---

@st.cache_data(ttl=3600) # تخزين مؤقت للبيانات لمدة ساعة لتوفير الطلبات
def fetch_odds(sport_key, region='eu'):
    """جلب البيانات من المزود الخارجي"""
    if API_KEY == "YOUR_API_KEY_HERE":
        return None, "يرجى إعداد مفتاح API أولاً"
        
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': region,
        'markets': 'h2h', # Head to Head (فوز - تعادل - خسارة)
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"خطأ في الاتصال: {response.status_code}"
    except Exception as e:
        return None, str(e)

def process_data(raw_data):
    """تحويل JSON المعقد إلى جدول بيانات نظيف"""
    matches = []
    for match in raw_data:
        # نأخذ أول وكالة مراهنات متوفرة
        if not match['bookmakers']: continue
        
        bookmaker = match['bookmakers'][0]
        outcomes = bookmaker['markets'][0]['outcomes']
        
        # استخراج القيم (مع التعامل مع اختلاف ترتيب الأسماء)
        home = match['home_team']
        away = match['away_team']
        
        # البحث عن القيم بدقة
        h_odd = next((x['price'] for x in outcomes if x['name'] == home), 1.0)
        a_odd = next((x['price'] for x in outcomes if x['name'] == away), 1.0)
        d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 1.0)
        
        matches.append({
            "التاريخ": match['commence_time'][:10],
            "المضيف": home,
            "الضيف": away,
            "فوز المضيف (1)": h_odd,
            "تعادل (X)": d_odd,
            "فوز الضيف (2)": a_odd
        })
    return pd.DataFrame(matches)

def highlight_best_odds(data):
    """دالة التنسيق الشرطي لتلوين أفضل احتمال"""
    numeric_cols = ['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)']
    df_styler = pd.DataFrame('', index=data.index, columns=data.columns)
    attr = 'background-color: #d4edda; color: #155724; font-weight: bold;'
    
    for idx, row in data.iterrows():
        max_val = row[numeric_cols].max()
        for col in numeric_cols:
            if row[col] == max_val:
                df_styler.at[idx, col] = attr
    return df_styler

# --- 4. واجهة المستخدم (Frontend) ---

def main():
    # الشريط الجانبي
    with st.sidebar:
        st.title("⚽ Koralytics")
        st.caption("منصة تحليل احتمالات رياضية")
        
        st.header("⚙️ الإعدادات")
        league_map = {
            "الدوري الإنجليزي (EPL)": "soccer_epl",
            "الدوري الإسباني (La Liga)": "soccer_spain_la_liga",
            "دوري أبطال أوروبا": "soccer_uefa_champs_league",
            "الدوري الإيطالي": "soccer_italy_serie_a",
            "الدوري الفرنسي": "soccer_france_ligue_one"
        }
        selected_league_name = st.selectbox("اختر البطولة", list(league_map.keys()))
        selected_league_key = league_map[selected_league_name]
        
        st.divider()
        st.subheader("💰 المحفظة الافتراضية")
        budget = st.number_input("رصيدك ($)", value=1000.0, step=50.0)

    # المحتوى الرئيسي
    st.title(f"تحليل {selected_league_name}")
    
    # 1. جلب وعرض البيانات
    raw_data, error = fetch_odds(selected_league_key)
    
    if error:
        st.warning(f"⚠️ {error}")
        st.info("نصيحة: تأكد من تفعيل مفتاح API في ملف secrets.")
    elif not raw_data:
        st.info("لا توجد مباريات متاحة حالياً في هذه البطولة.")
    else:
        df = process_data(raw_data)
        
        # عرض الجدول الملون
        st.subheader("📊 جدول الاحتمالات (الفرص الأفضل بالأخضر)")
        st.dataframe(
            df.style.apply(highlight_best_odds, axis=None).format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)']),
            use_container_width=True
        )
        
        st.divider()
        
        # 2. منطقة المحاكاة والتحليل العميق
        st.subheader("🧠 مختبر التحليل والمحاكاة")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown("#### اختر المباراة")
            match_options = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
            selected_match_str = st.selectbox("المباراة:", match_options)
            
            # استخراج بيانات المباراة المختارة
            host_team = selected_match_str.split(" vs ")[0]
            match_row = df[df['المضيف'] == host_team].iloc[0]
            
            st.markdown("#### قرارك؟")
            prediction = st.radio("التوقع:", ["فوز المضيف", "تعادل", "فوز الضيف"])
            
            # تحديد الـ Odd
            if prediction == "فوز المضيف": 
                user_odd = match_row['فوز المضيف (1)']
                choice_name = match_row['المضيف']
            elif prediction == "تعادل": 
                user_odd = match_row['تعادل (X)']
                choice_name = "تعادل"
            else: 
                user_odd = match_row['فوز الضيف (2)']
                choice_name = match_row['الضيف']

            stake = st.slider("مبلغ الرهان ($):", 10.0, budget, 50.0)

        with c2:
            st.markdown("#### 📈 التحليل البصري والإحصائي")
            
            # الرسم البياني
            chart_data = pd.DataFrame({
                'النتيجة': [match_row['المضيف'], 'تعادل', match_row['الضيف']],
                'الاحتمال (Odd)': [match_row['فوز المضيف (1)'], match_row['تعادل (X)'], match_row['فوز الضيف (2)']]
            }).set_index('النتيجة')
            
            st.bar_chart(chart_data, color="#0083B8")
            
            # حساب الاحتمالية الضمنية (Implied Probability)
            implied_prob = (1 / user_odd) * 100
            potential_profit = (stake * user_odd) - stake
            
            # بطاقات المؤشرات (Metrics)
            m1, m2, m3 = st.columns(3)
            m1.metric("القيمة (Odd)", f"{user_odd}")
            m2.metric("احتمالية الفوز (إحصائياً)", f"{implied_prob:.1f}%")
            m3.metric("الربح الصافي المتوقع", f"{potential_profit:.2f}$", delta_color="normal")
            
            if st.button("محاكاة النتيجة الآن"):
                st.toast(f"تم تسجيل توقعك لـ {choice_name} بـ {stake}$", icon="✅")
                if implied_prob > 60:
                    st.balloons()
                    st.success("هذا خيار 'آمن' إحصائياً (احتمالية عالية)!")
                elif implied_prob < 30:
                    st.warning("هذا خيار 'مخاطرة عالية' (High Risk)!")
                else:
                    st.info("رهان متوازن.")

if __name__ == '__main__':
    main()

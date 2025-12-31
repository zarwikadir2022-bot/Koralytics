import streamlit as st
import pandas as pd
import requests

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics Pro | محلل المباريات والأهداف",
    page_icon="⚽",
    layout="wide"
)

# تنسيق CSS مخصص
st.markdown("""
<style>
    .stMetric {background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6;}
    .big-font {font-size: 18px !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعداد المفتاح السري ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    # مفتاح مؤقت في حال نسيان وضعه في Secrets (لن يعمل إلا إذا استبدلته)
    API_KEY = "YOUR_API_KEY_HERE"

# --- 3. دوال المعالجة (Backend) ---

@st.cache_data(ttl=3600)
def fetch_odds(sport_key, region='eu'):
    if API_KEY == "YOUR_API_KEY_HERE":
        return None, "يرجى وضع مفتاح API في Secrets"
        
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': region,
        # التحديث الهام: نطلب الفائز (h2h) ومجموع الأهداف (totals)
        'markets': 'h2h,totals', 
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
    """تحويل JSON المعقد إلى جدول بيانات شامل"""
    matches = []
    for match in raw_data:
        # نحتاج لوجود مكاتب مراهنات
        if not match['bookmakers']: continue
        
        # نأخذ أول وكالة كمرجع (عادة تكون Unibet أو William Hill)
        bookmaker = match['bookmakers'][0]
        markets = bookmaker['markets']
        
        # 1. استخراج الفائز (H2H)
        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)

        # 2. استخراج الأهداف (Totals - Over/Under 2.5)
        totals = next((m for m in markets if m['key'] == 'totals'), None)
        over_25 = under_25 = 0.0
        
        if totals:
            outcomes = totals['outcomes']
            # نبحث عن النقطة 2.5 تحديداً
            over_25 = next((x['price'] for x in outcomes if x['name'] == 'Over' and x['point'] == 2.5), 0)
            under_25 = next((x['price'] for x in outcomes if x['name'] == 'Under' and x['point'] == 2.5), 0)

        matches.append({
            "التاريخ": match['commence_time'][:10],
            "المضيف": match['home_team'],
            "الضيف": match['away_team'],
            "فوز المضيف (1)": h_odd,
            "تعادل (X)": d_odd,
            "فوز الضيف (2)": a_odd,
            "Over 2.5": over_25,   # عمود جديد
            "Under 2.5": under_25  # عمود جديد
        })
        
    return pd.DataFrame(matches)

def color_h2h(val):
    """تلوين بسيط للأرقام"""
    return 'color: black' 

# --- 4. واجهة المستخدم (Frontend) ---

def main():
    with st.sidebar:
        st.header("🏆 Koralytics Pro")
        st.info("نسخة التحليل الشامل (فائز + أهداف)")
        
        league_map = {
            "الدوري الإنجليزي": "soccer_epl",
            "الدوري الإسباني": "soccer_spain_la_liga",
            "دوري أبطال أوروبا": "soccer_uefa_champs_league",
            "الدوري الإيطالي": "soccer_italy_serie_a",
            "الدوري الألماني": "soccer_germany_bundesliga"
        }
        selected_league = st.selectbox("اختر الدوري", list(league_map.keys()))
        sport_key = league_map[selected_league]
        
        st.divider()
        budget = st.number_input("محفظة المحاكاة ($)", 100, 10000, 1000)

    st.title(f"تحليل مباريات: {selected_league}")

    # جلب البيانات
    data, error = fetch_odds(sport_key)
    
    if error:
        st.error(error)
    elif not data:
        st.warning("لا توجد مباريات متاحة حالياً.")
    else:
        df = process_data(data)
        
        # --- القسم 1: جدول البيانات الشامل ---
        st.subheader("📊 جدول الاحتمالات (مقارنة شاملة)")
        
        # تلوين أفضل الاحتمالات في أعمدة الفوز
        st.dataframe(
            df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                    .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
            use_container_width=True
        )

        st.divider()

        # --- القسم 2: مختبر التحليل ---
        st.subheader("⚽ مختبر المحاكاة (Match Lab)")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            # اختيار المباراة
            match_list = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
            selected_match_txt = st.selectbox("اختر المباراة للتحليل:", match_list)
            
            # استخراج الصف الخاص بالمباراة
            host = selected_match_txt.split(" vs ")[0]
            match_row = df[df['المضيف'] == host].iloc[0]
            
            st.markdown("---")
            st.write("🛠 **أدوات الرهان:**")
            bet_type = st.radio("نوع الرهان:", ["نتيجة المباراة (1X2)", "الأهداف (Over/Under)"])
            
            user_odd = 0.0
            selection = ""
            
            if bet_type == "نتيجة المباراة (1X2)":
                choice = st.selectbox("توقعك:", ["فوز المضيف", "تعادل", "فوز الضيف"])
                if choice == "فوز المضيف": user_odd = match_row['فوز المضيف (1)']
                elif choice == "تعادل": user_odd = match_row['تعادل (X)']
                else: user_odd = match_row['فوز الضيف (2)']
                selection = choice
                
            else: # Over/Under
                choice = st.selectbox("عدد الأهداف:", ["Over 2.5 (أكثر من هدفين)", "Under 2.5 (أقل من 3 أهداف)"])
                if "Over" in choice:
                    user_odd = match_row['Over 2.5']
                    selection = "Over 2.5"
                else:
                    user_odd = match_row['Under 2.5']
                    selection = "Under 2.5"

            stake = st.slider("مبلغ الرهان ($)", 10, int(budget), 50)

        with c2:
            st.markdown(f"### تحليل مباراة: {match_row['المضيف']} ضد {match_row['الضيف']}")
            
            # حسابات المحلل
            if user_odd > 0:
                implied_prob = (1 / user_odd) * 100
                potential_profit = (stake * user_odd) - stake
                
                # عرض البطاقات (Metrics)
                k1, k2, k3 = st.columns(3)
                k1.metric("القيمة (Odd)", f"{user_odd}")
                k2.metric("احتمالية النجاح", f"{implied_prob:.1f}%")
                k3.metric("الربح المتوقع", f"{potential_profit:.2f}$", delta_color="normal")
                
                # الرسم البياني للتحليل
                st.write("📈 **مقارنة الفرص:**")
                
                if bet_type == "نتيجة المباراة (1X2)":
                    chart_data = pd.DataFrame({
                        'الخيار': [match_row['المضيف'], 'تعادل', match_row['الضيف']],
                        'الاحتمال (Odd)': [match_row['فوز المضيف (1)'], match_row['تعادل (X)'], match_row['فوز الضيف (2)']]
                    }).set_index('الخيار')
                    st.bar_chart(chart_data, color="#0083B8")
                else:
                    # رسم بياني للأهداف
                    chart_data = pd.DataFrame({
                        'الخيار': ['Over 2.5', 'Under 2.5'],
                        'الاحتمال (Odd)': [match_row['Over 2.5'], match_row['Under 2.5']]
                    }).set_index('الخيار')
                    st.bar_chart(chart_data, color="#28a745") # لون أخضر للأهداف

                # حكم المحلل (الذكاء الاصطناعي البسيط)
                if user_odd == 0:
                    st.warning("⚠️ لا توجد بيانات كافية لهذا السوق.")
                elif implied_prob > 65:
                    st.success("✅ **تحليل:** رهان آمن جداً (Low Risk). الأرقام تدعم هذا الخيار بقوة.")
                elif implied_prob < 35:
                    st.error("🔥 **تحليل:** رهان عالي المخاطرة (High Risk). العائد كبير لكن الفرصة ضئيلة.")
                else:
                    st.info("⚖️ **تحليل:** رهان متوازن.")
            else:
                st.warning("عذراً، بيانات هذا الرهان غير متوفرة لهذه المباراة.")

if __name__ == '__main__':
    main()

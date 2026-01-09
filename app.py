import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics - Live AI Analysis", layout="wide")

# --- دالة جلب النتائج المباشرة (Caching لتقليل استهلاك الـ API) ---
@st.cache_data(ttl=60)  # تحديث كل دقيقة واحدة فقط
def get_live_scores(api_key):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"live": "all"}
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        return response.json()['response']
    except:
        return []

# --- واجهة المستخدم ---
st.title("⚽ Koralytics: المختبر الإحصائي المباشر")
st.markdown(f"**التوقيت الحالي:** {datetime.now().strftime('%H:%M')} | **الزوار:** 151 🚀")

# --- القسم الأول: النتائج المباشرة (الخاصية الجديدة) ---
st.header("🏟️ المباريات الجارية الآن")
API_KEY = "ضع_مفتاحك_هنا" # استبدله بمفتاحك من RapidAPI

live_data = get_live_scores(API_KEY)

if live_data:
    cols = st.columns(len(live_data) if len(live_data) < 3 else 3)
    for idx, match in enumerate(live_data[:6]): # عرض أول 6 مباريات مباشرة
        with cols[idx % 3]:
            home = match['teams']['home']['name']
            away = match['teams']['away']['name']
            score_h = match['goals']['home']
            score_a = match['goals']['away']
            time = match['fixture']['status']['elapsed']
            
            st.info(f"**{home}** {score_h} - {score_a} **{away}** \n\n ⏱️ الدقيقة: {time}'")
            if st.button(f"تحليل مباراة {home}", key=f"btn_{idx}"):
                st.session_state['target_match'] = f"{home} vs {away}"
else:
    st.warning("لا توجد مباريات مباشرة حالياً أو المفتاح غير مفعل.")

st.divider()

# --- القسم الثاني: نظام التحليل بالذكاء الاصطناعي (ChatGPT) ---
st.header("🤖 مستشار التحليل الذكي")
col_input, col_stats = st.columns([1, 1])

with col_input:
    match_name = st.text_input("اسم المباراة (مثلاً: السنغال ضد مالي)", 
                              value=st.session_state.get('target_match', ''))
    stats_input = st.text_area("أدخل الإحصائيات الحالية (الاستحواذ، التسديدات...)", 
                               placeholder="الاستحواذ 60%، ركنيات 5...")
    
    if st.button("إجراء التحليل العميق 🔍"):
        with st.spinner('جاري تحليل البيانات برادار Koralytics...'):
            # هنا تضع كود الربط مع OpenAI الذي تملكه سابقاً
            st.success(f"تحليل مباراة {match_name} جاهز!")
            st.markdown("> **توقع النتيجة:** بناءً على الضغط الحالي، احتمالية هدف في الدقائق العشر القادمة هي 70%.")

with col_stats:
    st.subheader("📈 الرادار الإحصائي")
    # محاكاة لرادار القوة (يمكنك ربطه ببيانات حقيقية)
    chart_data = pd.DataFrame({
        'Team': ['Home', 'Away'],
        'Power': [75, 45]
    })
    st.bar_chart(chart_data, x='Team', y='Power')

# --- تذييل الصفحة ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/91/91503.png", width=100)
st.sidebar.write("### إحصائيات المنصة اليوم")
st.sidebar.metric("التحليلات المكتملة", "151")
st.sidebar.metric("مشاهدات تيك توك", "286")

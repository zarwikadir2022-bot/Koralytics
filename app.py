import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(
    page_title="Koralytics Pro - Live AI",
    page_icon="⚽",
    layout="wide"
)

# --- 2. دالة جلب النتائج المباشرة (محمية بـ Caching) ---
@st.cache_data(ttl=60)  # تحديث البيانات كل 60 ثانية فقط لتوفير استهلاك الـ API
def get_live_scores(api_key):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"live": "all"}
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json().get('response', [])
        return []
    except Exception as e:
        return []

# --- 3. الواجهة الرسومية (Sidebar) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/91/91503.png", width=80)
    st.title("لوحة التحكم")
    st.metric(label="إجمالي الزوار الآن", value="151", delta="🚀")
    st.metric(label="تحليلات اليوم", value="125", delta="📈")
    st.divider()
    st.info("Koralytics يستخدم الذكاء الاصطناعي لتحليل المباريات بناءً على الإحصائيات الحية.")

# --- 4. الجزء العلوي: النتائج المباشرة ---
st.title("🏟️ النتائج المباشرة والتحليل الذكي")
st.write(f"توقيت تونس: {datetime.now().strftime('%H:%M')}")

# أدخل مفتاحك هنا
API_KEY = "ضع_مفتاحك_هنا" 

st.subheader("📺 مباريات جارية الآن")
live_matches = get_live_scores(API_KEY)

if live_matches:
    # عرض المباريات في أعمدة جذابة
    cols = st.columns(3)
    for i, match in enumerate(live_matches[:6]): # عرض أهم 6 مباريات مباشرة
        with cols[i % 3]:
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_score = match['goals']['home']
            away_score = match['goals']['away']
            elapsed = match['fixture']['status']['elapsed']
            league = match['league']['name']
            
            with st.container(border=True):
                st.caption(f"🏆 {league}")
                st.markdown(f"**{home_team}** {home_score} - {away_score} **{away_team}**")
                st.markdown(f"⏱️ `الدقيقة: {elapsed}'` ")
                if st.button(f"تحليل {home_team}", key=f"btn_{i}"):
                    st.session_state['selected_match'] = f"{home_team} vs {away_team}"
else:
    st.warning("لا توجد مباريات مباشرة حالياً أو يرجى التحقق من مفتاح الـ API.")

st.divider()

# --- 5. الجزء الأوسط: مختبر التحليل بالذكاء الاصطناعي ---
st.header("🤖 مختبر Koralytics للتحليل")

col_left, col_right = st.columns([1.2, 0.8])

with col_left:
    selected = st.session_state.get('selected_match', '')
    match_input = st.text_input("المباراة المستهدفة:", value=selected)
    
    stats_area = st.text_area(
        "أدخل إحصائيات المباراة (أو الصقها هنا):",
        placeholder="مثال: الاستحواذ 55%، التسديدات على المرمى 4، الركنيات 3...",
        height=150
    )
    
    if st.button("بدء التحليل العميق برادار AI 🔍", use_container_width=True):
        if match_input and stats_area:
            with st.spinner('جاري معالجة البيانات الإحصائية...'):
                # محاكاة لرد الذكاء الاصطناعي (ChatGPT)
                st.success("تم اكتمال التحليل!")
                st.markdown(f"### 📋 تقرير مباراة {match_input}")
                st.write("بناءً على المعطيات، الفريق المستضيف يضغط بقوة في المناطق الجانبية. احتمالية تسجيل هدف قبل نهاية الشوط الثاني مرتفعة بنسبة 65%.")
        else:
            st.error("يرجى إدخال اسم المباراة والإحصائيات أولاً.")

with col_right:
    st.subheader("📊 مؤشر القوة اللحظي")
    # عرض رسم بياني بسيط يوضح ضغط الفريقين
    chart_data = pd.DataFrame({
        "الفريق": ["المستضيف", "الضيف"],
        "نسبة الضغط": [70, 45]
    })
    st.bar_chart(chart_

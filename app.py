import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt # ضروري للتلوين

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics Global | كل دوريات العالم",
    page_icon="🌍",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #dee2e6;}
</style>
""", unsafe_allow_html=True)

# --- 2. المفتاح السري ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY_HERE"

# --- 3. دوال المعالجة (Backend) ---

@st.cache_data(ttl=86400) # تخزين القائمة لمدة يوم كامل لأنها لا تتغير كثيراً
def get_active_sports():
    """جلب قائمة كل الرياضات النشطة حالياً من المصدر"""
    if API_KEY == "YOUR_API_KEY_HERE":
        return []
    
    url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except:
        return []

@st.cache_data(ttl=3600)
def fetch_odds(sport_key, region='eu'):
    """جلب الاحتمالات للدوري المختار"""
    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': region,
        'markets': 'h2h,totals', 
        'oddsFormat': 'decimal'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Status: {response.status_code}"
    except Exception as e:
        return None, str(e)

def process_data(raw_data):
    matches = []
    for match in raw_data:
        if not match['bookmakers']: continue
        
        bookmaker = match['bookmakers'][0] # نأخذ أول وكالة
        markets = bookmaker['markets']
        
        # 1. الفائز (H2H)
        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)

        # 2. الأهداف (Totals)
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

# --- 4. واجهة المستخدم ---

def main():
    with st.sidebar:
        st.header("🌍 المستكشف الشامل")
        st.info("يتم تحديث القائمة تلقائياً حسب البطولات النشطة عالمياً.")
        
        # 1. جلب القائمة الديناميكية
        active_sports = get_active_sports()
        
        if not active_sports:
            st.error("تأكد من مفتاح API أو الاتصال بالإنترنت.")
            return

        # 2. تصنيف الرياضات (للتنظيم)
        # نستخرج المجموعات الفريدة (مثل Soccer, Basketball, Tennis)
        groups = sorted(list(set([s['group'] for s in active_sports])))
        selected_group = st.selectbox("1️⃣ اختر نوع الرياضة:", groups)
        
        # 3. فلترة البطولات بناءً على المجموعة المختارة
        # ننشئ قاموساً يربط اسم البطولة بالكود الخاص بها
        filtered_leagues = {s['title']: s['key'] for s in active_sports if s['group'] == selected_group}
        
        selected_league_name = st.selectbox("2️⃣ اختر البطولة:", list(filtered_leagues.keys()))
        selected_league_key = filtered_leagues[selected_league_name]
        
        st.divider()
        budget = st.number_input("المحفظة ($)", 100, 10000, 1000)

    # --- المحتوى الرئيسي ---
    st.title(f"تحليل: {selected_league_name}")
    st.caption(f"Category: {selected_group}")

    # جلب البيانات
    data, error = fetch_odds(selected_league_key)
    
    if error:
        st.error(f"خطأ: {error}")
    elif not data:
        st.warning("هذه البطولة متاحة في القائمة، ولكن لا توجد مباريات مجدولة لليوم أو الغد.")
    else:
        df = process_data(data)
        
        # عرض الجدول
        if not df.empty:
            st.subheader("📊 جدول الفرص والاحتمالات")
            try:
                st.dataframe(
                    df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                      .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
                    use_container_width=True
                )
            except Exception as e:
                # في حال حدوث خطأ بالتلوين نعرض الجدول عادياً
                st.dataframe(df, use_container_width=True)

            st.divider()
            
            # قسم المحاكاة السريع
            st.subheader("🎲 محاكاة سريعة")
            col1, col2 = st.columns(2)
            with col1:
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر مباراة:", matches_txt)
                
            with col2:
                # عرض رسم بياني سريع للمباراة المختارة
                host = sel_match.split(" vs ")[0]
                row = df[df['المضيف'] == host].iloc[0]
                
                chart_data = pd.DataFrame({
                    'Team': [row['المضيف'], 'Draw', row['الضيف']],
                    'Odd': [row['فوز المضيف (1)'], row['تعادل (X)'], row['فوز الضيف (2)']]
                }).set_index('Team')
                
                st.bar_chart(chart_data)
        else:
            st.info("تم جلب البيانات ولكن الجدول فارغ (قد تكون كل الاحتمالات مغلقة حالياً).")

if __name__ == '__main__':
    main()

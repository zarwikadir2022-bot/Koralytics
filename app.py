import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics Global | كل دوريات العالم",
    page_icon="🌍",
    layout="wide"
)

# تنسيق CSS لتحسين مظهر البطاقات
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .stButton>button {width: 100%; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

# --- 2. المفتاح السري ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_API_KEY_HERE"

# --- 3. دوال المعالجة (Backend) ---

@st.cache_data(ttl=86400)
def get_active_sports():
    """جلب قائمة الرياضات النشطة"""
    if API_KEY == "YOUR_API_KEY_HERE": return []
    try:
        url = f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}'
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []
    except: return []

@st.cache_data(ttl=3600)
def fetch_odds(sport_key, region='eu'):
    """جلب الاحتمالات"""
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
        
        # 1. H2H
        h2h = next((m for m in markets if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)

        # 2. Totals
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
        st.header("🌍 إعدادات البحث")
        active_sports = get_active_sports()
        
        if not active_sports:
            st.error("تأكد من مفتاح API.")
            return

        groups = sorted(list(set([s['group'] for s in active_sports])))
        selected_group = st.selectbox("الرياضة:", groups)
        
        filtered_leagues = {s['title']: s['key'] for s in active_sports if s['group'] == selected_group}
        selected_league_name = st.selectbox("البطولة:", list(filtered_leagues.keys()))
        selected_league_key = filtered_leagues[selected_league_name]
        
        st.divider()
        budget = st.number_input("رصيد المحفظة ($)", 100.0, 10000.0, 1000.0)

    st.title(f"تحليل: {selected_league_name}")

    data, error = fetch_odds(selected_league_key)
    
    if error: st.error(error)
    elif not data: st.warning("لا توجد مباريات مجدولة حالياً لهذه البطولة.")
    else:
        df = process_data(data)
        
        if not df.empty:
            # 1. عرض الجدول
            st.subheader("📊 جدول الفرص")
            try:
                st.dataframe(
                    df.style.background_gradient(subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)'], cmap='Greens')
                      .format("{:.2f}", subset=['فوز المضيف (1)', 'تعادل (X)', 'فوز الضيف (2)', 'Over 2.5', 'Under 2.5']),
                    use_container_width=True
                )
            except: st.dataframe(df) # fallback without style if matplotlib error

            st.divider()
            
            # 2. مختبر المحاكاة (عاد للعمل الآن!)
            st.subheader("🧠 مختبر المحاكاة والتحليل")
            
            c1, c2 = st.columns([1, 2])
            
            with c1:
                st.markdown("#### 1. خيارات الرهان")
                # قائمة المباريات
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel_match = st.selectbox("اختر المباراة:", matches_txt)
                
                # استخراج الصف
                host = sel_match.split(" vs ")[0]
                match_row = df[df['المضيف'] == host].iloc[0]
                
                # نوع الرهان
                bet_type = st.radio("نوع السوق:", ["الفائز بالمباراة (1X2)", "الأهداف (Over/Under)"])
                
                user_odd = 0.0
                if bet_type == "الفائز بالمباراة (1X2)":
                    choice = st.selectbox("توقعك:", ["فوز المضيف", "تعادل", "فوز الضيف"])
                    if choice == "فوز المضيف": user_odd = match_row['فوز المضيف (1)']
                    elif choice == "تعادل": user_odd = match_row['تعادل (X)']
                    else: user_odd = match_row['فوز الضيف (2)']
                else:
                    choice = st.selectbox("العدد:", ["Over 2.5 (أكثر من 2)", "Under 2.5 (أقل من 3)"])
                    if "Over" in choice: user_odd = match_row['Over 2.5']
                    else: user_odd = match_row['Under 2.5']
                
                # إدخال المبلغ (عاد الآن!)
                stake = st.number_input("مبلغ الرهان ($):", 10.0, float(budget), 50.0)

            with c2:
                st.markdown(f"#### 2. نتائج التحليل: {sel_match}")
                
                if user_odd > 0:
                    # الحسابات
                    implied_prob = (1 / user_odd) * 100
                    potential_profit = (stake * user_odd) - stake
                    
                    # عرض النتائج
                    k1, k2, k3 = st.columns(3)
                    k1.metric("القيمة (Odd)", f"{user_odd}")
                    k2.metric("احتمالية الفوز", f"{implied_prob:.1f}%")
                    k3.metric("الربح المتوقع", f"{potential_profit:.2f}$", delta_color="normal")
                    
                    # الرسم البياني الذكي
                    st.caption("مقارنة الفرص بصرياً:")
                    if bet_type == "الفائز بالمباراة (1X2)":
                        chart_data = pd.DataFrame({
                            'Option': [match_row['المضيف'], 'Draw', match_row['الضيف']],
                            'Odd': [match_row['فوز المضيف (1)'], match_row['تعادل (X)'], match_row['فوز الضيف (2)']]
                        }).set_index('Option')
                        st.bar_chart(chart_data, color="#0083B8")
                    else:
                        chart_data = pd.DataFrame({
                            'Option': ['Over 2.5', 'Under 2.5'],
                            'Odd': [match_row['Over 2.5'], match_row['Under 2.5']]
                        }).set_index('Option')
                        st.bar_chart(chart_data, color="#28a745")

                    # نصيحة المحلل
                    if implied_prob > 60:
                        st.success(f"✅ إحصائياً: هذا خيار آمن نسبياً (احتمالية {implied_prob:.1f}%).")
                    elif implied_prob < 30:
                        st.warning(f"🔥 إحصائياً: مخاطرة عالية جداً! الربح مغرٍ لكن الاحتمال ضعيف.")
                    else:
                        st.info("⚖️ إحصائياً: رهان متوازن.")
                else:
                    st.warning("⚠️ عذراً، الاحتمالات غير متوفرة لهذا الخيار بالتحديد.")

        else:
            st.info("تم الاتصال بنجاح، لكن لا توجد بيانات للعرض (الجدول فارغ).")

if __name__ == '__main__':
    main()

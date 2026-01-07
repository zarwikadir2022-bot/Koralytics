import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Pro Analysis", page_icon="💎", layout="wide")

# --- 2. محرك الإحصائيات ---
def update_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn):
        with open(fn, "w") as f: f.write("0")
    with open(fn, "r") as f:
        try: count = int(f.read())
        except: count = 0
    count += 1
    with open(fn, "w") as f: f.write(str(count))
    return count

def get_stat(feat):
    fn = f"stat_{feat}.txt"
    if not os.path.exists(fn): return 0
    with open(fn, "r") as f:
        try: return int(f.read())
        except: return 0

# --- 3. محرك السيناريوهات التحليلية (الجديد) ---
def get_ai_insight(p1, px, p2, xg, row):
    insights = []
    # تحليل القوة الهجومية
    if xg > 2.5: insights.append(f"🔥 **نزعة هجومية:** المباراة تتجه لتكون مفتوحة مع فرص تسجيل عالية.")
    else: insights.append(f"🛡️ **تحفظ تكتيكي:** من المتوقع أن يغلب الطابع الدفاعي على مجريات اللقاء.")
    
    # تحليل الطرف الأقرب
    if p1 > 55: insights.append(f"🏟️ **أفضلية الأرض:** {row['المضيف']} يمتلك زمام المبادرة إحصائياً.")
    elif p2 > 55: insights.append(f"🚀 **خطر الضيف:** {row['الضيف']} قادر على خطف نقاط المباراة عبر المرتدات.")
    else: insights.append(f"⚖️ **تكافؤ فرص:** المباراة متوازنة جداً وصراع كبير في منطقة العمليات.")
    
    # تحليل البطاقات
    tightness = 1 - abs((p1/100) - (p2/100))
    if tightness > 0.7: insights.append(f"🟨 **اندفاع بدني:** تقارب المستوى قد يؤدي لتدخلات قوية وكثرة البطاقات.")
    
    return insights

# --- 4. محرك النتائج ---
def predict_exact_score(p1, px, p2, xg):
    if px > 34: return "1 - 1" if xg > 2.0 else "0 - 0"
    if p1 > p2:
        if p1 > 60: return "3 - 0" if xg > 3.0 else "2 - 0"
        return "2 - 1" if xg > 2.2 else "1 - 0"
    else:
        if p2 > 60: return "0 - 3" if xg > 3.0 else "0 - 2"
        return "1 - 2" if xg > 2.2 else "0 - 1"

# --- 5. التصميم ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stApp { background: #f0f2f6; }
    .match-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; }
    .score-banner { background: #1e3799; color: gold; padding: 25px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .insight-card { background: #eef2f7; border-right: 6px solid #1e3799; padding: 15px; border-radius: 8px; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 6. التطبيق الرئيسي ---
def main():
    if 'v' not in st.session_state:
        update_stat("unique_visitors")
        st.session_state['v'] = True

    st.sidebar.title("💎 Koralytics AI")
    st.sidebar.write(f"👤 الزوار: {get_stat('unique_visitors')} | 🎯 التحليلات: {get_stat('deep_analysis')}")

    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={st.secrets["ODDS_API_KEY"]}').json()
        l_map = {s['title']: s['key'] for s in r if s['group'] == 'Soccer'}
        sel_l = st.sidebar.selectbox("🏆 اختر البطولة", list(l_map.keys()))
    except: st.error("تأكد من وجود API KEY"); return

    df = pd.DataFrame() # جلب البيانات هنا (كما في الكود السابق)
    # ... (كود fetch_data السابق) ...
    
    # للعرض فقط سنفترض وجود بيانات (يجب دمج دالة fetch_data هنا)
    
    st.title(f"🏟️ {sel_l}")
    # (هنا يتم عرض المباريات المختصرة)

    st.markdown("---")
    st.header("🔬 المختبر الإحصائي التفصيلي")
    # بعد اختيار المباراة:
    # (بفرض أننا اخترنا صف "row")
    
    p1, px, p2 = 45.0, 30.0, 25.0 # قيم تجريبية
    xg = 2.4
    score = predict_exact_score(p1, px, p2, xg)
    insights = get_ai_insight(p1, px, p2, xg, {"المضيف": "الفريق أ", "الضيف": "الفريق ب"})

    st.markdown(f"""<div class="score-banner">
        <small>النتيجة الرقمية المتوقعة</small><br>
        <span style="font-size:3.5rem;">{score}</span>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📊 توزيع الاحتمالات")
        st.bar_chart(pd.DataFrame({'%': [p1, px, p2]}, index=['المضيف', 'تعادل', 'الضيف']))
        st.write(f"🎯 **مؤشر الثقة:** {int(max(p1, p2, px) + 15)}%")

    with col2:
        st.subheader("📝 الرؤية التحليلية للذكاء الاصطناعي")
        for ins in insights:
            st.markdown(f'<div class="insight-card">{ins}</div>', unsafe_allow_html=True)
            
        st.markdown(f"""
        <div style="margin-top:20px; padding:15px; background:white; border-radius:10px;">
            <b>📋 ملخص الميزات الإحصائية:</b><br>
            • الأهداف المتوقعة (xG): {xg}<br>
            • احتمالية البطاقات: {round(1.5+(1-abs(p1-p2)/100)*2,1)}<br>
            • ضغط المباراة: عالية جداً
        </div>
        """, unsafe_allow_html=True)

if __name__ == '__main__': main()

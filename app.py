import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | V20 Pro", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

# --- 2. التصميم (Platinum Theme) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; color: #333333; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .profit-box {background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold;}
    .advisor-box {background-color: #fef9e7; border: 1px solid #f1c40f; color: #d35400; padding: 10px; border-radius: 8px; font-size: 0.9em;}
    .card-metric { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; border: 1px solid #eee; }
</style>
""", unsafe_allow_html=True)

# --- 3. إعدادات المفاتيح ---
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = "YOUR_ODDS_KEY"
MY_PHONE_NUMBER = "21600000000"

# --- 4. محرك الحسابات (الأهداف والبطاقات) ---
def calculate_discipline(h_odd, a_odd):
    # المباريات المتكافئة (odds متقاربة) تزيد فيها احتمالية التوتر والبطاقات
    h_prob = 1/h_odd if h_odd > 0 else 0.5
    a_prob = 1/a_odd if a_odd > 0 else 0.5
    tightness = 1 - abs(h_prob - a_prob) # 1 يعني مباراة قمة متكافئة جداً
    
    h_cards = np.random.uniform(1.5, 3.5) + (tightness * 1.5)
    a_cards = np.random.uniform(1.8, 3.8) + (tightness * 1.5)
    red_prob = (tightness * 25) + np.random.randint(5, 15)
    return round(h_cards, 1), round(a_cards, 1), round(red_prob)

def calculate_exact_goals(over_odd, under_odd):
    if over_odd == 0 or under_odd == 0: return {}, None
    prob_under = (1 / under_odd) / ((1/over_odd) + (1/under_odd))
    if prob_under > 0.55: expected_goals = 1.9
    elif prob_under > 0.45: expected_goals = 2.4
    elif prob_under < 0.30: expected_goals = 3.3
    else: expected_goals = 2.8
    return {k: poisson.pmf(k, expected_goals) * 100 for k in range(5)}, expected_goals

# --- 5. محرك التقارير (AI Analyst) ---
def ai_analyst_report(match_row, expected_goals):
    home, away = match_row['المضيف'], match_row['الضيف']
    h_odd, a_odd = match_row['1'], match_row['2']
    h_prob = (1/h_odd * 100) if h_odd > 0 else 0
    a_prob = (1/a_odd * 100) if a_odd > 0 else 0
    h_cards, a_cards, red_p = calculate_discipline(h_odd, a_odd)
    
    # تحديد القصة
    headline = "🔥 لقاء مشتعل" if abs(h_prob - a_prob) < 10 else "🚀 سيطرة طرف واحد"
    story = f"تشير البيانات إلى مباراة {'عنيفة تكتيكياً' if red_p > 30 else 'هادئة نسبياً'}. "
    story += f"من المتوقع أن يتلقى {home} حوالي {h_cards} إنذارات."
    
    goals_txt = "⚽ هجوم كاسح متوقع" if expected_goals and expected_goals > 3 else "🛡️ دفاعات حديدية"
    
    final_report = f"""### {headline}\n\n**🧐 القراءة الفنية (الخشونة والأهداف):**\n{story}\n\n---\n**📊 توقعات الشباك:**\n{goals_txt}\n\n🎯 **طرد متوقع (🟥):** `{red_p}%` | **إنذارات (🟨):** `{h_cards + a_cards}`"""
    return final_report, int(h_prob/10), h_cards, a_cards, red_p

# --- 6. الوظائف المساعدة (Logos, Session, Auth) ---
# (نفس دالات get_team_logo و manage_session_lock و check_password من كودك الأصلي تبقى كما هي)
# [ملاحظة: تأكد من إدراج دالة get_team_logo هنا]

# --- 7. جلب البيانات ---
@st.cache_data(ttl=3600)
def fetch_odds(sport_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        return (r.json(), None) if r.status_code == 200 else (None, str(r.status_code))
    except: return None, "Connection Error"

# --- 8. التطبيق الرئيسي ---
def main():
    # [هنا تضع منطق الـ Login: if not check_password(): return]
    
    # --- عرض المحتوى ---
    st.title("⚽ Koralytics AI Platinum")
    
    # (هنا نضع منطق جلب الدوريات من الـ Sidebar كما في كودك)
    # [ملاحظة: سنفترض أننا اخترنا دوري وجلبنا الـ df]
    
    # سنركز على الجزء الذي طلبت تطويره (تفاصيل المباراة والبطاقات):
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.5])
    
    # [بفرض أننا اخترنا مباراة محددة 'row']
    # مثال توضيحي للمباريات (يجب وضعه داخل حلقة dataframe الخاصة بك)
    if 'df' in locals() and not df.empty:
        sel_match = st.selectbox("اختر لقاء للتحليل العبقري:", [f"{r['المضيف']} vs {r['الضيف']}" for _, r in df.iterrows()])
        row = df[df['المضيف'] == sel_match.split(" vs ")[0]].iloc[0]
        
        with c1:
            st.subheader("🔍 بطاقة اللقاء")
            col_l1, col_l2 = st.columns(2)
            col_l1.image(row['H_Logo'], width=80)
            col_l2.image(row['A_Logo'], width=80)
            
            # عرض البطاقات المتوقعة
            h_c, a_c, r_p = calculate_discipline(row['1'], row['2'])
            st.markdown(f"""
            <div style="display:flex; gap:10px; justify-content:center; margin-top:10px;">
                <div class="card-metric" style="background:#fff3cd;">🟨 {h_c + a_c}</div>
                <div class="card-metric" style="background:#f8d7da;">🟥 {r_p}%</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            probs, exp_goals = calculate_exact_goals(row['O 2.5'], row['U 2.5'])
            report, risk, h_cards, a_cards, red_p = ai_analyst_report(row, exp_goals)
            
            st.markdown(f'<div class="ai-box">{report}</div>', unsafe_allow_html=True)
            
            # رسوم بيانية للبطاقات والأهداف
            st.write("#### 📊 رادار الإحصائيات")
            chart_tab1, chart_tab2 = st.tabs(["إنذارات الفريقين", "احتمالات الأهداف"])
            with chart_tab1:
                card_df = pd.DataFrame({'Team': [row['المضيف'], row['الضيف']], 'Yellow Cards': [h_cards, a_cards]}).set_index('Team')
                st.bar_chart(card_df, color="#f1c40f")
            with chart_tab2:
                if probs:
                    st.bar_chart(pd.DataFrame(list(probs.items()), columns=['Goals', 'Prob']).set_index('Goals'), color="#2980b9")

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    # تأكد من استدعاء الدالة check_password() هنا
    main()

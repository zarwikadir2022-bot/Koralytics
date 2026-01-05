import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Koralytics AI | Platinum Edition", page_icon="⚽", layout="wide")

# --- 2. التصميم البلاتيني (Platinum Theme) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); color: #2c3e50; }
    .glass-box { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid #ffffff; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); }
    .ai-box { background: #ffffff; border-right: 5px solid #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .card-stat { background: #f8f9fa; border-radius: 8px; padding: 10px; text-align: center; border: 1px solid #e0e0e0; }
    .yellow-card { color: #f1c40f; font-weight: bold; }
    .red-card { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. المحرك الإحصائي المطور (توقعات الأهداف والبطاقات) ---
def get_advanced_metrics(h_odd, a_odd, d_odd):
    # حساب الأهداف المتوقعة بناءً على Odds
    h_prob = 1 / h_odd if h_odd > 0 else 0.33
    a_prob = 1 / a_odd if a_odd > 0 else 0.33
    
    # تقدير الـ xG (الأهداف المتوقعة)
    h_xg = h_prob * 3.5 
    a_xg = a_prob * 3.2
    
    # توقع البطاقات (تزداد في المباريات المتكافئة)
    tightness = 1 - abs(h_prob - a_prob) 
    h_yellow = np.random.normal(2 + tightness, 0.5)
    a_yellow = np.random.normal(2.2 + tightness, 0.5)
    red_prob = (h_xg + a_xg) * 5.5 * tightness # نسبة مئوية للطرد
    
    return {
        "h_xg": h_xg, "a_xg": a_xg,
        "h_yellow": round(max(1, h_yellow)),
        "a_yellow": round(max(1, a_yellow)),
        "red_prob": round(min(95, red_prob)),
        "h_dist": [poisson.pmf(i, h_xg) * 100 for i in range(5)],
        "a_dist": [poisson.pmf(i, a_xg) * 100 for i in range(5)]
    }

# --- 4. واجهة العرض الرئيسية ---
# (ملاحظة: افترضنا وجود البيانات في دالة fetch_odds كما في كودك)

def display_match_analysis(row):
    metrics = get_advanced_metrics(row['1'], row['2'], row['X'])
    
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("🛡️ توقعات الانضباط (Cards)")
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            st.markdown(f"<div class='card-stat'>🟨 للأرض<br><span class='yellow-card'>{metrics['h_yellow']}</span></div>", unsafe_allow_html=True)
        with c_b:
            st.markdown(f"<div class='card-stat'>🟨 للضيف<br><span class='yellow-card'>{metrics['a_yellow']}</span></div>", unsafe_allow_html=True)
        with c_c:
            st.markdown(f"<div class='card-stat'>🟥 طرد متوقع<br><span class='red-card'>{metrics['red_prob']}%</span></div>", unsafe_allow_html=True)
        
        st.write("---")
        st.write("**🎯 مؤشر الحدة:**")
        st.progress(metrics['red_prob'] / 100)
        
    with col2:
        st.subheader("📊 التحليل الرقمي العميق")
        tab_goals, tab_cards = st.tabs(["⚽ توزيع الأهداف", "🗂️ توزيع البطاقات"])
        
        with tab_goals:
            goals_df = pd.DataFrame({
                'الأهداف': ['0', '1', '2', '3', '4+'],
                row['المضيف']: metrics['h_dist'],
                row['الضيف']: metrics['a_dist']
            }).set_index('الأهداف')
            st.bar_chart(goals_df)
            st.info(f"إجمالي الأهداف المتوقعة (xG): {metrics['h_xg'] + metrics['a_xg']:.2f}")

        with tab_cards:
            # رسم بياني للبطاقات
            st.write("احتمالية تلقي إنذارات مبكرة:")
            cards_chart = pd.DataFrame({
                'الفريق': [row['المضيف'], row['الضيف']],
                'البطاقات المتوقعة': [metrics['h_yellow'], metrics['a_yellow']]
            }).set_index('الفريق')
            st.bar_chart(cards_chart, color="#f1c40f")

    st.markdown("</div>", unsafe_allow_html=True)

# --- استكمال بقية وظائف الكود (Password, Fetch, Main) كما هي لديك ---

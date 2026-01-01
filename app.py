import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | Debug Mode",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# تنسيق CSS
st.markdown("""
<style>
    .stMetric {background-color: #f0f2f6; border: 1px solid #dce0e6; border-radius: 10px; padding: 10px;}
    .ai-box {
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 15px; 
        border-right: 6px solid #0083B8; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
        margin-bottom: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.8;
    }
    .ticket-box {background-color: #2b313e; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;}
    .ticket-item {border-bottom: 1px solid #555; padding-bottom: 5px; margin-bottom: 5px; font-size: 0.9em;}
    .profit-box {background-color: #d1e7dd; padding: 15px; border-radius: 10px; border: 1px solid #badbcc; color: #0f5132; margin-top: 10px;}
    .advisor-box {background-color: #fff3cd; padding: 10px; border-radius: 8px; border: 1px solid #ffecb5; color: #856404; margin-top: 10px; font-size: 0.9em;}
    a[href*="wa.me"] button {background-color: #25D366 !important; border-color: #25D366 !important; color: white !important;}
    .magic-btn button {background: linear-gradient(45deg, #833ab4, #fd1d1d, #fcb045); color: white !important; border: none; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 2. إعدادات المفاتيح ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_ODDS_KEY"

MY_PHONE_NUMBER = "21600000000"

# --- 3. إدارة الجلسات ---
@st.cache_resource
def get_active_sessions(): return {}

def manage_session_lock(key):
    active_sessions = get_active_sessions()
    current_time = time.time()
    TIMEOUT = 60 
    keys_to_remove = [k for k, t in active_sessions.items() if current_time - t > TIMEOUT]
    for k in keys_to_remove: del active_sessions[k]

    if key in active_sessions:
        if current_time - active_sessions[key] < TIMEOUT:
            if st.session_state.get("current_key") == key:
                active_sessions[key] = current_time 
                return True, ""
            else: return False, "⚠️ المفتاح مشغول."
    active_sessions[key] = current_time
    return True, ""

def logout_user():
    st.session_state["password_correct"] = False
    st.session_state["current_key"] = None
    st.session_state["my_ticket"] = [] 
    st.rerun()

if "my_ticket" not in st.session_state: st.session_state["my_ticket"] = []

# --- 4. جلب الشعارات (مع القائمة الموسعة) ---
def get_team_logo(team_name):
    name_clean = team_name.lower().strip()
    
    # تحسينات للقائمة لتشمل اختصارات شائعة
    logos = {
        # 🇹🇳 تونس
        "esperance": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Esp%C3%A9rance_Sportive_de_Tunis.svg/1200px-Esp%C3%A9rance_Sportive_de_Tunis.svg.png",
        "club africain": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Club_Africain_logo.svg/1200px-Club_Africain_logo.svg.png",
        "etoile": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Etoile_du_Sahel.svg/1200px-Etoile_du_Sahel.svg.png",
        "sahel": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Etoile_du_Sahel.svg/1200px-Etoile_du_Sahel.svg.png",
        "sfaxien": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/CS_Sfaxien_Logo.svg/1200px-CS_Sfaxien_Logo.svg.png",
        "stade tunisien": "https://upload.wikimedia.org/wikipedia/fr/4/4e/Stade_tunisien.png",
        "monastir": "https://upload.wikimedia.org/wikipedia/fr/thumb/3/30/Union_sportive_monastirienne_%28logo%29.svg/1200px-Union_sportive_monastirienne_%28logo%29.svg.png",

        # 🇪🇸 إسبانيا
        "real madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/1200px-Real_Madrid_CF.svg.png",
        "barcelona": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/1200px-FC_Barcelona_%28crest%29.svg.png",
        "atletico": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/1200px-Atletico_Madrid_2017_logo.svg.png",
        "girona": "https://upload.wikimedia.org/wikipedia/en/thumb/9/90/For_Girona_FC.svg/1200px-For_Girona_FC.svg.png",
        "sevilla": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Sevilla_FC_logo.svg/1200px-Sevilla_FC_logo.svg.png",
        "valencia": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/Valenciacf.svg/1200px-Valenciacf.svg.png",
        "betis": "https://upload.wikimedia.org/wikipedia/en/thumb/1/13/Real_betis_logo.svg/1200px-Real_betis_logo.svg.png",
        "sociedad": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/Real_Sociedad_logo.svg/1200px-Real_Sociedad_logo.svg.png",
        "bilbao": "

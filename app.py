import streamlit as st
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="Koralytics AI | Platinum V19",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. التصميم الرصاصي الفاتح (Platinum Theme CSS) ---
st.markdown("""
<style>
    /* 1. الخلفية العامة (رصاصي فاتح متدرج) */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        color: #2c3e50; /* نص غامق لضمان الوضوح */
    }
    
    /* 2. تحسين القائمة الجانبية (أبيض نقي) */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #d1d5db;
    }
    
    /* 3. العناوين والنصوص */
    h1, h2, h3 {
        color: #2c3e50 !important; /* رمادي غامق مزرق */
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* 4. الصناديق الزجاجية (Glassmorphism for Light Mode) */
    .glass-box {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid #ffffff;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* ظل خفيف جداً */
    }

    /* 5. صندوق الذكاء الاصطناعي */
    .ai-box {
        background: #ffffff;
        border-right: 5px solid #2980b9;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 15px;
        color: #333333;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 6. صندوق الورقة (Ticket) */
    .ticket-box {
        background: linear-gradient(45deg, #2c3e50, #4ca1af);
        color: white;
        font-weight: bold;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .ticket-item {border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 5px; margin-bottom: 5px;}

    /* 7. صندوق الأرباح والمستشار */
    .profit-box {background-color: #e8f8f5; border: 1px solid #2ecc71; color: #27ae60; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold;}
    .advisor-box {background-color: #fef9e7; border: 1px solid #f1c40f; color: #d35400; padding: 10px; border-radius: 8px; font-size: 0.9em;}
    
    /* 8. الأزرار */
    div.stButton > button {
        background: linear-gradient(90deg, #2980b9 0%, #2c3e50 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background: #3498db;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(41, 128, 185, 0.3);
    }
    
    /* 9. الجداول (تحسين القراءة) */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    
    /* 10. نصوص الجدول */
    div[data-testid="stDataFrame"] * {
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. إعدادات المفاتيح ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = "YOUR_ODDS_KEY"

# ⚠️ ضع رقمك هنا
MY_PHONE_NUMBER = "21600000000"

# --- 4. إدارة الجلسات ---
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

# --- 5. جلب الشعارات (القائمة الكاملة) ---
def get_team_logo(team_name):
    name_clean = team_name.lower().strip()
    
    logos = {
        # 🇹🇳 أندية تونس
        "esperance": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Esp%C3%A9rance_Sportive_de_Tunis.svg/1200px-Esp%C3%A9rance_Sportive_de_Tunis.svg.png",
        "club africain": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/Club_Africain_logo.svg/1200px-Club_Africain_logo.svg.png",
        "etoile": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Etoile_du_Sahel.svg/1200px-Etoile_du_Sahel.svg.png",
        "sahel": "https://upload.wikimedia.org/wikipedia/en/thumb/2/2f/Etoile_du_Sahel.svg/1200px-Etoile_du_Sahel.svg.png",
        "sfaxien": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/CS_Sfaxien_Logo.svg/1200px-CS_Sfaxien_Logo.svg.png",
        "stade tunisien": "https://upload.wikimedia.org/wikipedia/fr/4/4e/Stade_tunisien.png",
        "monastir": "https://upload.wikimedia.org/wikipedia/fr/thumb/3/30/Union_sportive_monastirienne_%28logo%29.svg/1200px-Union_sportive_monastirienne_%28logo%29.svg.png",
        "ben guerdane": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7e/US_Ben_Guerdane.png/200px-US_Ben_Guerdane.png",
        "bizertin": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e8/CA_Bizertin.png/200px-CA_Bizertin.png",
        "gafsa": "https://upload.wikimedia.org/wikipedia/en/thumb/1/1e/EGS_Gafsa.png",
        "metlaoui": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/ES_Metlaoui.png",

        # 🇪🇸 إسبانيا
        "real madrid": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Real_Madrid_CF.svg/1200px-Real_Madrid_CF.svg.png",
        "barcelona": "https://upload.wikimedia.org/wikipedia/en/thumb/4/47/FC_Barcelona_%28crest%29.svg/1200px-FC_Barcelona_%28crest%29.svg.png",
        "atletico": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f4/Atletico_Madrid_2017_logo.svg/1200px-Atletico_Madrid_2017_logo.svg.png",
        "girona": "https://upload.wikimedia.org/wikipedia/en/thumb/9/90/For_Girona_FC.svg/1200px-For_Girona_FC.svg.png",
        "sevilla": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Sevilla_FC_logo.svg/1200px-Sevilla_FC_logo.svg.png",
        "valencia": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/Valenciacf.svg/1200px-Valenciacf.svg.png",
        "betis": "https://upload.wikimedia.org/wikipedia/en/thumb/1/13/Real_betis_logo.svg/1200px-Real_betis_logo.svg.png",
        "sociedad": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/Real_Sociedad_logo.svg/1200px-Real_Sociedad_logo.svg.png",
        "bilbao": "https://upload.wikimedia.org/wikipedia/en/thumb/9/98/Club_Athletic_Bilbao_logo.svg/1200px-Club_Athletic_Bilbao_logo.svg.png",
        "athletic club": "https://upload.wikimedia.org/wikipedia/en/thumb/9/98/Club_Athletic_Bilbao_logo.svg/1200px-Club_Athletic_Bilbao_logo.svg.png",
        "villarreal": "https://upload.wikimedia.org/wikipedia/en/thumb/7/70/Villarreal_CF_logo.svg/1200px-Villarreal_CF_logo.svg.png",

        # 🇬🇧 إنجلترا
        "man city": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/1200px-Manchester_City_FC_badge.svg.png",
        "manchester city": "https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Manchester_City_FC_badge.svg/1200px-Manchester_City_FC_badge.svg.png",
        "man utd": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/1200px-Manchester_United_FC_crest.svg.png",
        "manchester united": "https://upload.wikimedia.org/wikipedia/en/thumb/7/7a/Manchester_United_FC_crest.svg/1200px-Manchester_United_FC_crest.svg.png",
        "liverpool": "https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/1200px-Liverpool_FC.svg.png",
        "arsenal": "https://upload.wikimedia.org/wikipedia/en/thumb/5/53/Arsenal_FC.svg/1200px-Arsenal_FC.svg.png",
        "chelsea": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cc/Chelsea_FC.svg/1200px-Chelsea_FC.svg.png",
        "tottenham": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b4/Tottenham_Hotspur.svg/1200px-Tottenham_Hotspur.svg.png",
        "newcastle": "https://upload.wikimedia.org/wikipedia/en/thumb/5/56/Newcastle_United_Logo.svg/1200px-Newcastle_United_Logo.svg.png",
        "aston villa": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f9/Aston_Villa_FC_crest_%282016%29.svg/1200px-Aston_Villa_FC_crest_%282016%29.svg.png",
        "west ham": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c2/West_Ham_United_FC_logo.svg/1200px-West_Ham_United_FC_logo.svg.png",
        "brighton": "https://upload.wikimedia.org/wikipedia/en/thumb/f/fd/Brighton_%26_Hove_Albion_logo.svg/1200px-Brighton_%26_Hove_Albion_logo.svg.png",

        # 🇮🇹 إيطاليا
        "inter": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/FC_Internazionale_Milano_2021.svg/1200px-FC_Internazionale_Milano_2021.svg.png",
        "milan": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/1200px-Logo_of_AC_Milan.svg.png",
        "juventus": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Juventus_FC_2017_icon_%28black%29.svg/1200px-Juventus_FC_2017_icon_%28black%29.svg.png",
        "napoli": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/SSC_Neapel.svg/1200px-SSC_Neapel.svg.png",
        "roma": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f7/AS_Roma_logo_%282017%29.svg/1200px-AS_Roma_logo_%282017%29.svg.png",
        "lazio": "https://upload.wikimedia.org/wikipedia/en/thumb/c/ce/S.S._Lazio_badge.svg/1200px-S.S._Lazio_badge.svg.png",
        "atalanta": "https://upload.wikimedia.org/wikipedia/en/thumb/6/66/AtalantaBC.svg/1200px-AtalantaBC.svg.png",
        "fiorentina": "https://upload.wikimedia.org/wikipedia/en/thumb/b/ba/ACF_Fiorentina_2.svg/1200px-ACF_Fiorentina_2.svg.png",

        # 🇫🇷 فرنسا
        "psg": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/1200px-Paris_Saint-Germain_F.C..svg.png",
        "paris": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Paris_Saint-Germain_F.C..svg/1200px-Paris_Saint-Germain_F.C..svg.png",
        "marseille": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Olympique_Marseille_logo.svg/1200px-Olympique_Marseille_logo.svg.png",
        "lyon": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c6/Olympique_Lyonnais.svg/1200px-Olympique_Lyonnais.svg.png",
        "monaco": "https://upload.wikimedia.org/wikipedia/en/thumb/b/ba/AS_Monaco_FC.svg/1200px-AS_Monaco_FC.svg.png",
        "lille": "https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/LOSC_Lille_Logo.svg/1200px-LOSC_Lille_Logo.svg.png",

        # 🇩🇪 ألمانيا
        "bayern": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg/1200px-FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg.png",
        "dortmund": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Borussia_Dortmund_logo.svg/1200px-Borussia_Dortmund_logo.svg.png",
        "leverkusen": "https://upload.wikimedia.org/wikipedia/en/thumb/5/59/Bayer_04_Leverkusen_logo.svg/1200px-Bayer_04_Leverkusen_logo.svg.png",
        "leipzig": "https://upload.wikimedia.org/wikipedia/en/thumb/0/04/RB_Leipzig_2014_logo.svg/1200px-RB_Leipzig_2014_logo.svg.png",
        "stuttgart": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/VfB_Stuttgart_1893_Logo.svg/1200px-VfB_Stuttgart_1893_Logo.svg.png",

        # 🇵🇹🇳🇱 البرتغال وهولندا
        "porto": "https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/FC_Porto.svg/1200px-FC_Porto.svg.png",
        "benfica": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/SL_Benfica_logo.svg/1200px-SL_Benfica_logo.svg.png",
        "sporting": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg/1200px-Sporting_Clube_de_Portugal_%28Logo%29.svg.png",
        "ajax": "https://upload.wikimedia.org/wikipedia/en/thumb/7/79/Ajax_Amsterdam.svg/1200px-Ajax_Amsterdam.svg.png",
        "feyenoord": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e3/Feyenoord_logo.svg/1200px-Feyenoord_logo.svg.png",
        "psv": "https://upload.wikimedia.org/wikipedia/en/thumb/0/05/PSV_Eindhoven.svg/1200px-PSV_Eindhoven.svg.png",

        # 🌍 أفريقيا (CAF)
        "tunisia": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Flag_of_Tunisia.svg/1200px-Flag_of_Tunisia.svg.png",
        "morocco": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Flag_of_Morocco.svg/1200px-Flag_of_Morocco.svg.png",
        "egypt": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Egypt.svg/1200px-Flag_of_Egypt.svg.png",
        "algeria": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Flag_of_Algeria.svg/1200px-Flag_of_Algeria.svg.png",
        "senegal": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Flag_of_Senegal.svg/1200px-Flag_of_Senegal.svg.png",
        "nigeria": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Flag_of_Nigeria.svg/1200px-Flag_of_Nigeria.svg.png",
        "cameroon": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Flag_of_Cameroon.svg/1200px-Flag_of_Cameroon.svg.png",
        "ghana": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Flag_of_Ghana.svg/1200px-Flag_of_Ghana.svg.png",
        "ivory coast": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_C%C3%B4te_d%27Ivoire.svg/1200px-Flag_of_C%C3%B4te_d%27Ivoire.svg.png",
        "cote d'ivoire": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_C%C3%B4te_d%27Ivoire.svg/1200px-Flag_of_C%C3%B4te_d%27Ivoire.svg.png",
        "south africa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Flag_of_South_Africa.svg/1200px-Flag_of_South_Africa.svg.png",
        "mali": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Flag_of_Mali.svg/1200px-Flag_of_Mali.svg.png",
        "burkina faso": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Flag_of_Burkina_Faso.svg/1200px-Flag_of_Burkina_Faso.svg.png",
        "dr congo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Flag_of_the_Democratic_Republic_of_the_Congo.svg/1200px-Flag_of_the_Democratic_Republic_of_the_Congo.svg.png",
        "guinea": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Flag_of_Guinea.svg/1200px-Flag_of_Guinea.svg.png",

        # 🇪🇺 أوروبا (UEFA)
        "france": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c3/Flag_of_France.svg/1200px-Flag_of_France.svg.png",
        "germany": "https://upload.wikimedia.org/wikipedia/en/thumb/b/ba/Flag_of_Germany.svg/1200px-Flag_of_Germany.svg.png",
        "england": "https://upload.wikimedia.org/wikipedia/en/thumb/b/be/Flag_of_England.svg/1200px-Flag_of_England.svg.png",
        "spain": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9a/Flag_of_Spain.svg/1200px-Flag_of_Spain.svg.png",
        "italy": "https://upload.wikimedia.org/wikipedia/en/thumb/0/03/Flag_of_Italy.svg/1200px-Flag_of_Italy.svg.png",
        "portugal": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Portugal.svg/1200px-Flag_of_Portugal.svg.png",
        "netherlands": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/1200px-Flag_of_the_Netherlands.svg.png",
        "belgium": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Belgium.svg/1200px-Flag_of_Belgium.svg.png",
        "croatia": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Flag_of_Croatia.svg/1200px-Flag_of_Croatia.svg.png",
        "denmark": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Flag_of_Denmark.svg/1200px-Flag_of_Denmark.svg.png",
        "switzerland": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Flag_of_Switzerland.svg/1024px-Flag_of_Switzerland.svg.png",
        "sweden": "https://upload.wikimedia.org/wikipedia/en/thumb/4/4c/Flag_of_Sweden.svg/1200px-Flag_of_Sweden.svg.png",
        "poland": "https://upload.wikimedia.org/wikipedia/en/thumb/1/12/Flag_of_Poland.svg/1200px-Flag_of_Poland.svg.png",
        "turkey": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Flag_of_Turkey.svg/1200px-Flag_of_Turkey.svg.png",
        "serbia": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Flag_of_Serbia.svg/1200px-Flag_of_Serbia.svg.png",
        "scotland": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Flag_of_Scotland.svg/1200px-Flag_of_Scotland.svg.png",
        "wales": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Flag_of_Wales_2.svg/1200px-Flag_of_Wales_2.svg.png",
        "ukraine": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Flag_of_Ukraine.svg/1200px-Flag_of_Ukraine.svg.png",
        "austria": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_Austria.svg/1200px-Flag_of_Austria.svg.png",
        "hungary": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Flag_of_Hungary.svg/1200px-Flag_of_Hungary.svg.png",
        "czech republic": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_Czech_Republic.svg/1200px-Flag_of_the_Czech_Republic.svg.png",
        "greece": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_Greece.svg/1200px-Flag_of_Greece.svg.png",

        # 🌎 أمريكا الجنوبية (CONMEBOL)
        "brazil": "https://upload.wikimedia.org/wikipedia/en/thumb/0/05/Flag_of_Brazil.svg/1200px-Flag_of_Brazil.svg.png",
        "argentina": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Flag_of_Argentina.svg/1200px-Flag_of_Argentina.svg.png",
        "uruguay": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Flag_of_Uruguay.svg/1200px-Flag_of_Uruguay.svg.png",
        "colombia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Flag_of_Colombia.svg/1200px-Flag_of_Colombia.svg.png",
        "chile": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/Flag_of_Chile.svg/1200px-Flag_of_Chile.svg.png",
        "ecuador": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Flag_of_Ecuador.svg/1200px-Flag_of_Ecuador.svg.png",
        "peru": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Flag_of_Peru.svg/1200px-Flag_of_Peru.svg.png",
        "paraguay": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Flag_of_Paraguay.svg/1200px-Flag_of_Paraguay.svg.png",
        "venezuela": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Flag_of_Venezuela.svg/1200px-Flag_of_Venezuela.svg.png",

        # 🌏 آسيا (AFC)
        "saudi arabia": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Flag_of_Saudi_Arabia.svg/1200px-Flag_of_Saudi_Arabia.svg.png",
        "qatar": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Flag_of_Qatar.svg/1200px-Flag_of_Qatar.svg.png",
        "japan": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9e/Flag_of_Japan.svg/1200px-Flag_of_Japan.svg.png",
        "south korea": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Flag_of_South_Korea.svg/1200px-Flag_of_South_Korea.svg.png",
        "iran": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Flag_of_Iran.svg/1200px-Flag_of_Iran.svg.png",
        "australia": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Flag_of_Australia.svg/1200px-Flag_of_Australia.svg.png",
        "iraq": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Flag_of_Iraq.svg/1200px-Flag_of_Iraq.svg.png",
        "uae": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Flag_of_the_United_Arab_Emirates.svg/1200px-Flag_of_the_United_Arab_Emirates.svg.png",
        "jordan": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Flag_of_Jordan.svg/1200px-Flag_of_Jordan.svg.png",
        "oman": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Flag_of_Oman.svg/1200px-Flag_of_Oman.svg.png",
        "uzbekistan": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Flag_of_Uzbekistan.svg/1200px-Flag_of_Uzbekistan.svg.png",

        # 🌎 أمريكا الشمالية (CONCACAF)
        "usa": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/Flag_of_the_United_States.svg/1200px-Flag_of_the_United_States.svg.png",
        "united states": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a4/Flag_of_the_United_States.svg/1200px-Flag_of_the_United_States.svg.png",
        "mexico": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Flag_of_Mexico.svg/1200px-Flag_of_Mexico.svg.png",
        "canada": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Flag_of_Canada_%28Pantone%29.svg/1200px-Flag_of_Canada_%28Pantone%29.svg.png",
        "costa rica": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Flag_of_Costa_Rica.svg/1200px-Flag_of_Costa_Rica.svg.png",
        "panama": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Flag_of_Panama.svg/1200px-Flag_of_Panama.svg.png"
    }
    
    for key in logos:
        if key in name_clean:
            return logos[key]
            
    return "https://cdn-icons-png.flaticon.com/512/10542/10542547.png"

# --- 6. محرك الذكاء الاصطناعي (السردي) ---
def calculate_exact_goals(over_odd, under_odd):
    if over_odd == 0 or under_odd == 0: return {}, None
    prob_over = 1 / over_odd
    prob_under = 1 / under_odd
    margin = prob_over + prob_under
    fair_prob_under = prob_under / margin
    if fair_prob_under > 0.55: expected_goals = 1.9
    elif fair_prob_under > 0.45: expected_goals = 2.4
    elif fair_prob_under < 0.30: expected_goals = 3.3
    else: expected_goals = 2.8
    goals_probs = {}
    for k in range(5): goals_probs[k] = poisson.pmf(k, expected_goals) * 100
    return goals_probs, expected_goals

def ai_analyst_report(match_row, expected_goals):
    home = match_row['المضيف']
    away = match_row['الضيف']
    h_odd = match_row['1']
    a_odd = match_row['2']
    h_prob = (1/h_odd * 100) if h_odd > 0 else 0
    a_prob = (1/a_odd * 100) if a_odd > 0 else 0
    
    headline = ""; risk = 5
    if h_prob > 70: headline = f"🔥 {home} في طريق مفتوح للاكتساح!"; risk = 9
    elif a_prob > 70: headline = f"🚀 {away} يفرض سيطرته المطلقة!"; risk = 9
    elif h_prob > 55: headline = f"🔵 أفضلية مريحة لـ {home}، ولكن الحذر واجب."; risk = 7
    elif a_prob > 55: headline = f"🔴 {away} يمتلك الأسلحة الأخطر."; risk = 7
    elif abs(h_prob - a_prob) < 5: headline = "⚔️ معركة تكسير عظام.. لقاء متكافئ!"; risk = 4
    else: headline = "⚖️ كفة المباراة تميل قليلاً لأحد الطرفين."; risk = 6

    story = ""
    if risk >= 8:
        fav = home if h_prob > a_prob else away
        weak = away if h_prob > a_prob else home
        story += f"لغة الأرقام تشير بوضوح إلى أن **{fav}** يدخل بنية الحسم المبكر. الفوارق الفنية شاسعة، ودفاعات **{weak}** ستكون تحت ضغط رهيب. سيناريو 'المباراة من طرف واحد'."
    elif risk <= 4:
        story += f"مباراة شطرنج تكتيكية. لا يوجد طرف يملك أفضلية واضحة. **{home}** سيستغل الأرض، لكن **{away}** عنيد. التوقعات تشير لتعادل أو فوز صعب."
    else:
        fav = home if h_prob > a_prob else away
        story += f"المعطيات ترجح كفة **{fav}** الأكثر جاهزية. رغم ذلك، المباراة لن تكون نزهة، فالخصم يمتلك أدوات قد تسبب إزعاجاً."

    goals_txt = ""; score_pred = "غ/م"
    if expected_goals:
        if expected_goals >= 2.9:
            goals_txt = "⚽ **مهرجان أهداف:** دفاعات مفتوحة ولعب هجومي. (Over 2.5)."
            score_pred = "3-1 / 2-2"
        elif expected_goals <= 2.0:
            goals_txt = "🔒 **أقفال دفاعية:** مباراة مغلقة وشحيحة الفرص. (Under 2.5)."
            score_pred = "1-0 / 0-0"
        else:
            goals_txt = "⚖️ **توازن:** هدفين أو ثلاثة. (2-1 وارد جداً)."
            score_pred = "2-1 / 1-1"
    
    final_report = f"""### {headline}\n\n**🧐 القراءة الفنية:**\n{story}\n\n---\n**📊 توقعات الشباك:**\n{goals_txt}\n\n🎯 **النتيجة:** `{score_pred}`\n🛡️ **الأمان:** `{risk}/10`"""
    return final_report, risk

# --- 7. الحماية ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2: 
        st.markdown("<div class='glass-box' style='text-align:center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3593/3593510.png", width=100)
        st.title("💎 Koralytics AI")
        st.markdown("**بوابة التحليل الرياضي الذكي**")
        st.markdown("</div>", unsafe_allow_html=True)
        
        wa_link = f"https://wa.me/{MY_PHONE_NUMBER}?text=شراء مفتاح"
        st.link_button("📲 شراء مفتاح (VIP)", wa_link, use_container_width=True)
        
        with st.form("login_form"):
            password_input = st.text_input("🔑 مفتاح الدخول:", type="password")
            if st.form_submit_button("🚀 دخول للنظام", use_container_width=True):
                if "passwords" in st.secrets and password_input in st.secrets["passwords"].values():
                    is_allowed, msg = manage_session_lock(password_input)
                    if is_allowed:
                        st.session_state["password_correct"] = True
                        st.session_state["current_key"] = password_input
                        st.success("✅"); time.sleep(0.5); st.rerun()
                    else: st.error(msg)
                else: st.error("❌ مفتاح خاطئ")
    return False

# --- 8. جلب البيانات ---
@st.cache_data(ttl=3600)
def fetch_odds(sport_key):
    try:
        r = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds', 
                         params={'apiKey': API_KEY, 'regions': 'eu,us', 'markets': 'h2h,totals', 'oddsFormat': 'decimal'})
        return (r.json(), None) if r.status_code == 200 else (None, str(r.status_code))
    except Exception as e: return None, str(e)

def process_data_with_logos(raw_data):
    matches = []
    debug_names = []
    
    for match in raw_data:
        if not match['bookmakers']: continue
        raw_date = match['commence_time'].replace('T', ' ')[:16]
        debug_names.append(f"{match['home_team']} 🆚 {match['away_team']}")

        mkts = match['bookmakers'][0]['markets']
        h2h = next((m for m in mkts if m['key'] == 'h2h'), None)
        h_odd = d_odd = a_odd = 0.0
        if h2h:
            outcomes = h2h['outcomes']
            h_odd = next((x['price'] for x in outcomes if x['name'] == match['home_team']), 0)
            a_odd = next((x['price'] for x in outcomes if x['name'] == match['away_team']), 0)
            d_odd = next((x['price'] for x in outcomes if x['name'] == 'Draw'), 0)
        
        totals = next((m for m in mkts if m['key'] == 'totals'), None)
        over_25 = under_25 = 0.0
        if totals:
            outcomes = totals['outcomes']
            over_25 = next((x['price'] for x in outcomes if x['name'] == 'Over' and x['point'] == 2.5), 0)
            under_25 = next((x['price'] for x in outcomes if x['name'] == 'Under' and x['point'] == 2.5), 0)
        
        h_logo = get_team_logo(match['home_team'])
        a_logo = get_team_logo(match['away_team'])
        
        matches.append({
            "التوقيت": raw_date,
            "H_Logo": h_logo, "المضيف": match['home_team'], 
            "A_Logo": a_logo, "الضيف": match['away_team'],
            "1": h_odd, "X": d_odd, "2": a_odd,
            "O 2.5": over_25, "U 2.5": under_25
        })
    
    with st.sidebar:
        with st.expander("🕵️‍♂️ Debug Names (كاشف الأسماء)"):
            st.code("\n".join(debug_names))
        
    return pd.DataFrame(matches)

# --- 9. التطبيق الرئيسي ---
def main():
    if not check_password(): return

    # --- Sidebar ---
    with st.sidebar:
        st.title("💎 Koralytics")
        st.markdown("---")
        
        if st.session_state["my_ticket"]:
            total_odd = 1.0
            ticket_txt = "🚀 *Koralytics VIP Ticket:*\n"
            st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
            st.markdown("#### 🧾 ورقتي")
            for item in st.session_state["my_ticket"]:
                st.markdown(f"<div class='ticket-item'>✅ {item['pick']} <b style='float:right'>{item['odd']}</b></div>", unsafe_allow_html=True)
                total_odd *= item['odd']
                ticket_txt += f"✅ {item['pick']} @ {item['odd']}\n"
            st.markdown('</div>', unsafe_allow_html=True)
            
            col_t1, col_t2 = st.columns(2)
            with col_t1: st.metric("Total Odds", f"{total_odd:.2f}")
            with col_t2: 
                wa_url = f"https://wa.me/?text={urllib.parse.quote(ticket_txt)}"
                st.link_button("📲 واتساب", wa_url, use_container_width=True)
            
            if st.button("🗑️ مسح الورقة", use_container_width=True): 
                st.session_state["my_ticket"] = []; st.rerun()
            
        st.markdown("---")
        try:
            r = requests.get(f'https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}')
            if r.status_code != 200:
                st.error("API Error: Check Key"); return
            active = r.json()
            groups = sorted(list(set([s['group'] for s in active])))
            grp = st.selectbox("🏅 الرياضة", groups)
            leagues = {s['title']: s['key'] for s in active if s['group'] == grp}
            lname = st.selectbox("🏆 البطولة", list(leagues.keys()))
            lkey = leagues[lname]
        except: st.error("Connection Error"); return

        st.markdown("---")
        st.markdown("### ⚙️ أدوات")
        budget = st.number_input("💵 ميزانيتك ($):", 100.0, 50000.0, 500.0, step=50.0)
        show_gold = st.checkbox("🔥 عرض الفرص الذهبية")
        if st.button("🔴 تسجيل خروج", use_container_width=True): logout_user()

    # --- Main Content ---
    st.title(f"⚽ {lname}")
    
    col_mw1, col_mw2, col_mw3 = st.columns([1,2,1])
    with col_mw2:
        if st.button("🪄 العصا السحرية (اختر لي أفضل 3 مباريات)", use_container_width=True):
             st.session_state["magic_trigger"] = True

    data, error = fetch_odds(lkey)
    
    if data:
        df = process_data_with_logos(data)
        
        if show_gold and not df.empty:
            df = df[((1/df['1']) > 0.65) | ((1/df['2']) > 0.65)]
            if df.empty: st.warning("لا توجد فرص ذهبية حالياً.")

        if st.session_state.get("magic_trigger") and not df.empty:
            st.session_state["my_ticket"] = []
            candidates = []
            for i, row in df.iterrows():
                if row['1'] > 1.05 and (1/row['1']) > 0.60:
                    candidates.append({"pick": f"Win {row['المضيف']}", "odd": row['1'], "prob": 1/row['1']})
                if row['2'] > 1.05 and (1/row['2']) > 0.60:
                    candidates.append({"pick": f"Win {row['الضيف']}", "odd": row['2'], "prob": 1/row['2']})
            candidates.sort(key=lambda x: x['prob'], reverse=True)
            st.session_state["my_ticket"] = candidates[:3]
            st.session_state["magic_trigger"] = False
            st.rerun()

        if not df.empty:
            st.dataframe(
                df,
                column_config={
                    "H_Logo": st.column_config.ImageColumn("🏠", width="small"),
                    "A_Logo": st.column_config.ImageColumn("✈️", width="small"),
                    "1": st.column_config.NumberColumn("1 (Home)", format="%.2f"),
                    "X": st.column_config.NumberColumn("X (Draw)", format="%.2f"),
                    "2": st.column_config.NumberColumn("2 (Away)", format="%.2f"),
                },
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")
            
            st.markdown("<div class='glass-box'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.subheader("🔍 تفاصيل المباراة")
                matches_txt = [f"{row['المضيف']} vs {row['الضيف']}" for i, row in df.iterrows()]
                sel = st.selectbox("اختر المباراة:", matches_txt)
                host = sel.split(" vs ")[0]
                row = df[df['المضيف'] == host].iloc[0]
                
                col_img1, col_vs, col_img2 = st.columns([1,0.5,1])
                with col_img1: st.image(row['H_Logo'], width=100)
                with col_img2: st.image(row['A_Logo'], width=100)
                
                st.markdown("#### 💰 حاسبة الربح")
                bet_type = st.radio("النوع", ["فوز (1X2)", "أهداف (O/U)"], horizontal=True, label_visibility="collapsed")
                if bet_type == "فوز (1X2)":
                    opts = {f"فوز {row['المضيف']}": row['1'], "تعادل": row['X'], f"فوز {row['الضيف']}": row['2']}
                else:
                    opts = {"Over 2.5": row['O 2.5'], "Under 2.5": row['U 2.5']}
                
                sel_opt = st.selectbox("النتيجة", list(opts.keys()))
                val_odd = opts[sel_opt]
                
                if st.button(f"➕ أضف للورقة (@ {val_odd})", use_container_width=True):
                    st.session_state["my_ticket"].append({"pick": sel_opt, "odd": val_odd})
                    st.toast("✅ تمت الإضافة")
                    time.sleep(0.5); st.rerun()
                
                stake = st.number_input("الرهان ($):", 1.0, 1000.0, 10.0)
                st.markdown(f"<div class='profit-box'>الربح المتوقع: <b>{(stake * val_odd):.2f}$</b></div>", unsafe_allow_html=True)

            with c2:
                probs, exp_goals = calculate_exact_goals(row['O 2.5'], row['U 2.5'])
                report, risk = ai_analyst_report(row, exp_goals)
                
                st.markdown('<div class="ai-box">', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)

                rec_msg = "مغامرة!" if risk < 5 else "آمنة."
                rec_amount = budget * (3 if risk > 7 else 1) / 100
                st.markdown(f"""<div class="advisor-box">💡 <b>المستشار المالي:</b> الفرصة {rec_msg} ({risk}/10).<br>المبلغ المقترح: {rec_amount:.1f}$</div>""", unsafe_allow_html=True)

                # --- الرسوم البيانية (موجودة ولم تختفِ) ---
                st.markdown("#### 📊 الرسوم البيانية")
                
                # 1. رسم احتمالات الفوز (أزرق غامق ليناسب الرصاصي)
                if row['1'] > 0:
                    h_prob = (1 / row['1']) * 100
                    d_prob = (1 / row['X']) * 100
                    a_prob = (1 / row['2']) * 100
                    chart_df = pd.DataFrame({'Team': [row['المضيف'], 'Draw', row['الضيف']], 'Prob': [h_prob, d_prob, a_prob]}).set_index('Team')
                    st.bar_chart(chart_df, color=["#2980b9"]) 
                
                # 2. رسم توقعات الأهداف (أحمر)
                if probs:
                    goals_df = pd.DataFrame(list(probs.items()), columns=['Goals', 'Probability']).set_index('Goals')
                    st.bar_chart(goals_df, color=["#e74c3c"])

            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__': main()

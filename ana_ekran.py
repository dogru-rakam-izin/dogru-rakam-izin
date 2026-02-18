import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE KURUMSAL AYARLAR ---
# Buraya 1. Adımda aldığınız linki yapıştırın:
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    /* Yan menüde logoyu göster */
    [data-testid="stSidebarNav"] {{
        background-image: url({LOGO_URL});
        background-repeat: no-repeat;
        padding-top: 100px;
        background-position: center 20px;
        background-size: 120px auto;
    }}
    .main-title {{ color: #CC0000; font-size: 40px; font-weight: bold; margin-bottom: 0px; }}
    .sub-title {{ color: #333; font-size: 18px; margin-top: -10px; }}
    
    /* Butonları Logo Kırmızısı Yap */
    div.stButton > button:first-child {{
        background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- ANA SAYFA ÜST KISIM ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    st.image(LOGO_URL, width=150)
with col_text:
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Personel İzin Takip Sistemi</p>', unsafe_allow_html=True)

# ... (Kodun geri kalan kısmı aynı kalacak şekilde devam eder)

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE KURUMSAL AYARLAR ---
# Yeni paylaştığınız şeffaf PNG logo linki
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    /* Yan menüde logoyu göster ve silüeti kaldır */
    [data-testid="stSidebarNav"] {{
        background-image: url({LOGO_URL});
        background-repeat: no-repeat;
        padding-top: 140px;
        background-position: center 20px;
        background-size: 150px auto;
    }}
    /* Başlık ve Buton Renkleri (Logo Kırmızısı) */
    .main-title {{ color: #CC0000; font-size: 40px; font-weight: bold; margin-bottom: 0px; }}
    .sub-title {{ color: #333; font-size: 18px; margin-top: -10px; font-weight: 600; }}
    
    div.stButton > button:first-child {{
        background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 3.5em;
    }}
    div.stButton > button:hover {{ background-color: #990000; color: white; }}
    
    /* Metrik Kartları Tasarımı */
    [data-testid="stMetricValue"] {{ color: #CC0000; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- ANA SAYFA ÜST KISIM (LOGO + BAŞLIK) ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    # Şeffaf logo olduğu için genişliği biraz daha artırdık
    st.image(LOGO_URL, width=200)
with col_text:
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Rehabilitasyon Merkezi Personel İzin Yönetim Sistemi</p>', unsafe_allow_html=True)

# --- AYARLAR VE FORMATLAR ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]
TP_LIST = ["Tam Gün", "Saatlik"]

def hakedis_bul(yil):
    if yil < 1: return 0
    if yil < 5: return 14
    if yil < 15: return 20
    return 26

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                ts = str(r['Tür'])
                f = F_TAM if "Saatlik" in ts else F_TARIH
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in ts:
                    return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0].astype(float), res[1].astype(float)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if "PERSONEL" in m:
    ad_c, tc_c = st.columns(2)
    ad = ad_c.text_input("Ad Soyad")
    tc = tc_c.text_input("TC Kimlik No", max_chars=11)
    tp = st.radio("İzin Süresi", TP_LIST, horizontal=True)
    
    with st.expander("📝 İzin Başvuru Formu", expanded=True):
        with st.

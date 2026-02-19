import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE AYARLAR ---
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"
st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- İŞE GİRİŞ TARİHLERİ (Örnek veritabanı) ---
GIRIS_TARIHLERI = {
    "Örnek Personel": "2022-05-15"
}

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebarNav"] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }}
    .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; margin-bottom: 5px; }}
    div.stButton > button:first-child {{ background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; }}
    [data-testid="stMetricValue"] {{ color: #CC0000; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- AYARLAR ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]

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
        # Saatlik/Günlük ayrımı ve hesaplama
        def h(r):
            try:
                ts = str(r['Tür'])
                b_str = str(r['Başlangıç'])
                d_str = str(r['Dönüş'])
                if "Saatlik" in ts:
                    b = datetime.strptime(b_str, F_TAM)
                    d = datetime.strptime(d_str, F_TAM)
                    return 0, round((d-b).total_seconds()/3600, 1)
                else:
                    b = datetime.strptime(b_str[:10], F_TARIH)
                    d = datetime.strptime(d_str[:10], F_TARIH)
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
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c

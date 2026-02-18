import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- YAPILANDIRMA ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
SHEET_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
SHEET_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Doğru Rakam İzin Sistemi", layout="wide")

# Türkçe Ay Sözlüğü
TR_AYLAR = {
    "January": "Ocak", "February": "Şubat", "March": "Mart", "April": "Nisan",
    "May": "Mayıs", "June": "Haziran", "July": "Temmuz", "August": "Ağustos",
    "September": "Eylül", "October": "Ekim", "November": "Kasım", "December": "Aralık"
}

def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        df.columns = [c.strip() for c in df.columns]
        
        def sure_hesapla(row):
            try:
                if "Saatlik" in str(row['Tür']):
                    fmt = "%d/%m/%Y %H:%M"
                    bas = datetime.strptime(row['Başlangıç'], fmt)
                    bit = datetime.strptime(row['Dönüş'], fmt)
                    fark = bit - bas
                    return float(round(fark.seconds / 3600, 1))
                else:
                    fmt = "%d/%m/%Y"
                    bas = datetime.strptime(row['Başlangıç'], fmt)
                    bit = datetime.strptime(row['Dönüş'], fmt)
                    fark = (bit - bas).days
                    return int(fark)
            except:
                return 0

        df['Sure_Deger'] = df.apply(sure_hesapla, axis=1)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ing'] = df['Tarih_Obj'].dt.strftime('%B')
        df['Yil'] = df['Tarih_Obj'].dt.strftime('%Y')
        df['Ay_Ismi'] = df['Ay_Ing'].map(TR_AYLAR) + " " + df['Yil']
        return df
    except:
        return pd.DataFrame()

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ SEÇİMİ", ["⬇️ PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "⬇️ PERSONEL İZİN TALEBİ":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Ad Soyad")
            tc = st.text_input("TC Kimlik No", max_chars=11)
            tip = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
        with f2:
            tur = st.selectbox("Tür", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"])
            tar = st.date_input("İzin Tarihi")
            if tip == "Saatlik":
                s1, s2 = st.columns(2)
                saat1 = s1.time_input("Çıkış")
                saat2 = s2.time_input("Dönüş")
                bas, bit = f"{tar.strftime('%d/%m/%Y')} {saat1.strftime('%H:%M')}", f"{tar.strftime('%d/%m/%Y')} {saat2.strftime('%H:%M')}"
            else:
                donus = st.date_input("İş Başı Tarihi")
                bas, bit = tar.strftime('%d/%m/%Y'), donus.strftime('%d/%m/%Y')
        
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad and tc and onay:
                p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans

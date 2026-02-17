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

def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli (Onay & Takip)"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    df_mevcut = verileri_yukle()
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "İdari"])
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu"])
            bas = st.date_input("Başlangıç")
            bit = st.date_input("Dönüş")
        
        # --- KALAN İZİN HESAPLAMA GÖRÜNÜMÜ ---
        if tc:
            kullanilan = len(df_mevcut[(df_mevcut['TC No'].astype(str) == str(tc)) & (df_mevcut['Durum'] == 'Onaylandı') & (df_mevcut['Tür'] == tur)])
            st.info(f"Bilgi: Bu türde daha önce {kullanilan} adet onaylanmış izniniz bulunuyor.")

        submit = st.form_submit_button("Talebi Gönder")
        if submit and ad and tc:
            payload = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": tur, "bas": str(bas), "bit": str(bit)}
            requests.post(APPS_SCRIPT_URL, data=json.dumps(payload))
            st.success("Talebiniz yönetici onayına gönderildi.")

else:
    st.title("📊 Yönetici Onay ve Analiz Paneli")
    sifre = st.text_input("Şifre", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        
        # --- ÖZET İSTATİSTİKLER ---
        st.subheader("Genel Durum Analizi")
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Talep", len(df))
        c2.metric("Onay Bekleyen", len(df[df['Durum'] == 'Bekliyor']))
        c3.metric("Onaylanan", len(df[df['Durum'] == 'Onaylandı']))

        st.write("---")
        st.subheader("İzin Talepleri Listesi")
        
        # Onaylama Mekanizması (Basitleştirilmiş)
        # Not: Tam onay butonu için Google Sheets'te ilgili satırı güncelleyen bir script gerekir.
        # Şimdilik listeyi gösterip "Durum" sütununa göre filtreleme yapıyoruz.
        
        st.dataframe(df, use_container_width=True)
        
        # Personel Bazlı Kalan İzin Tablosu
        st.subheader("👤 Personel Bazlı Kullanılan İzinler")
        personel_ozet = df[df['Durum'] == 'Onaylandı'].groupby(['Ad Soyad', 'Tür']).size().reset_index(name='Kullanılan Gün')
        st.table(personel_ozet)

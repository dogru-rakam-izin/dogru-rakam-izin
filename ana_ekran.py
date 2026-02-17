import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- GOOGLE SHEETS AYARLARI ---
# Tablo ID'niz sisteme tanımlandı
SHEET_ID = "1UQLc2FmIuvFptf14nbPT83ZK4p42OpYAkFYSrZVdIlc"
# Verileri okumak için CSV formatında URL
SHEET_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
# Veri eklemek için Google Form/AppScript yerine en basit yöntem:
# (Not: Bu yöntem için tablonun "Herkes - Düzenleyici" olması şarttır)

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide")

def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        # Sütun isimlerini temizle
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- LOGO VE ARAYÜZ ---
st.sidebar.title("Doğru Rakam")
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Analiz Paneli"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    st.subheader("Dijital İzin Talep Formu")
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            brans = st.selectbox("Branşı / Dalı", [
                "Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog / Rehber Öğretmen", 
                "Odyolog", "Ergoterapist", "Dil ve Konuşma Terapisti", 
                "İdari Personel", "Destek Personel"
            ])
            tc = st.text_input("TC Kimlik No", max_chars=11)
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Ücretsiz İzin"])
            bas = st.date_input("İzin Başlangıç Tarihi")
            bit = st.date_input("İş Başı Tarihi (Dönüş)")
        
        st.warning("Beyan: Telafi dersleri planlanmış olup velilere bilgilendirme yapılmıştır.")
        onay = st.checkbox("Yukarıdaki beyanı okudum ve onaylıyorum.")
        submit = st.form_submit_button("Talebi Gönder")
        
        if submit:
            if ad and tc and onay:
                # Veriyi geçici olarak göster (Google Sheets API entegrasyonu için 
                # manuel olarak tablonuza ekleme yapılması veya AppScript kullanılması önerilir)
                st.success(f"Sayın {ad}, talebiniz sisteme iletildi. (Tablonuzu kontrol edin)")
                # Google Sheets'e veri yazma kısmı için AppScript URL'niz gerekecektir.
            else:
                st.error("Lütfen tüm alanları doldurun.")

else:
    st.title("📊 Yönetici Takip Paneli")
    df = verileri_yukle()
    if not df.empty:
        st.write("### Güncel İzin Listesi (Google Sheets'ten)")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Henüz kayıtlı veri bulunamadı.")

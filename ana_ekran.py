import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- YAPILANDIRMA (SİZİN BİLGİLERİNİZ) ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx53rgpCGw9iQDlGl00SgrkFpXrwBxETdlhzx2o2gmNvb4pmV7Ik4VKDQsaUGojR0Sb/exec"
SHEET_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
SHEET_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Doğru Rakam İzin Sistemi", layout="wide")

# --- VERİ OKUMA FONKSİYONU ---
def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        # Sütun isimlerindeki boşlukları temizle
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- SOL MENÜ ---
st.sidebar.title("DOĞRU RAKAM")
st.sidebar.info("Özel Eğitim İzin Takip Sistemi v2.0")
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Analiz Paneli"])

# --- 1. BÖLÜM: PERSONEL FORMU ---
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
                # Veriyi Google Sheets'e gönder
                payload = {
                    "tarih": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "tc": str(tc),
                    "ad": ad,
                    "brans": brans,
                    "tur": tur,
                    "bas": bas.strftime("%d/%m/%Y"),
                    "bit": bit.strftime("%d/%m/%Y")
                }
                try:
                    response = requests.post(APPS_SCRIPT_URL, data=json.dumps(payload))
                    st.success(f"Sayın {ad}, talebiniz başarıyla iletildi ve kayıt altına alındı.")
                    st.balloons()
                except:
                    st.error("Bir bağlantı sorunu oluştu, lütfen tekrar deneyin.")
            else:
                st.error("Lütfen tüm alanları doldurun ve onay kutusunu işaretleyin.")

# --- 2. BÖLÜM: YÖNETİCİ PANELİ ---
else:
    st.title("📊 Yönetici Takip Paneli")
    sifre = st.text_input("Yönetici Şifresi", type="password")
    
    if sifre == "1234": # Şifreniz
        df = verileri_yukle()
        if not df.empty:
            st.write("### Güncel İzin Listesi")
            st.dataframe(df, use_container_width=True)
            
            # Excel olarak indir
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Listeyi İndir (CSV)", csv, "Izin_Listesi.csv", "text/csv")
        else:
            st.info("Henüz sisteme girilmiş bir izin kaydı bulunamadı.")
    elif sifre != "":
        st.error("Hatalı şifre!")

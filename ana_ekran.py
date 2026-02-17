import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# --- AYARLAR ---
EXCEL_DOSYASI = "İZİN TAKİP S.xlsm"
YONETICI_SIFRE = "1234" 
LOGO_YOLU = "logo.jpg" 

st.set_page_config(page_title="Doğru Rakam İzin Sistemi", layout="wide")

# --- FONKSİYONLAR ---
def verileri_yukle():
    if os.path.exists(EXCEL_DOSYASI):
        try:
            df = pd.read_excel(EXCEL_DOSYASI)
            # Tarihleri sisteme uygun formata çevir
            for col in ["Tarih", "Başlangıç", "Dönüş"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
            if "Durum" not in df.columns:
                df["Durum"] = "Bekliyor"
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- YAN MENÜ ---
if os.path.exists(LOGO_YOLU):
    st.sidebar.image(LOGO_YOLU, use_container_width=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Analiz Paneli"])

# --- 1. BÖLÜM: PERSONEL FORMU ---
if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    st.subheader("Dijital İzin Talep Formu")
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            # GÜNCELLENEN BRANŞ LİSTESİ
            brans = st.selectbox("Branşı / Dalı", [
                "Uzman Öğretici",
                "Özel Eğitim Öğretmeni", 
                "Psikolog / Rehber Öğretmen", 
                "Odyolog",
                "Ergoterapist", 
                "Dil ve Konuşma Terapisti", 
                "İdari Personel", 
                "Destek Personel"
            ])
            tc = st.text_input("TC Kimlik No", max_chars=11)
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Ücretsiz İzin"])
            bas = st.date_input("İzin Başlangıç Tarihi")
            bit = st.date_input("İş Başı Tarihi (Dönüş)")
        
        st.warning("Beyan: Telafi dersleri planlanmış olup velilere gerekli bilgilendirme yapılmıştır.")
        onay = st.checkbox("Yukarıdaki beyanı okudum ve onaylıyorum.")
        submit = st.form_submit_button("Talebi Gönder")
        
        if submit:
            if ad and tc and onay:
                df = verileri_yukle()
                yeni = pd.DataFrame([{"Tarih": datetime.now(), "TC No": tc, "Ad Soyad": ad, "Branş": brans, "Tür": tur, "Başlangıç": pd.to_datetime(bas), "Dönüş": pd.to_datetime(bit), "Durum": "Bekliyor"}])
                df = pd.concat([df, yeni], ignore_index=True)
                df.to_excel(EXCEL_DOSYASI, index=False)
                st.success(f"Sayın {ad}, talebiniz başarıyla iletildi.")
            else:
                st.error("Lütfen tüm alanları doldurun ve onay kutusunu işaretleyin.")

# --- 2. BÖLÜM: YÖNETİCİ PANELİ ---
else:
    st.title("📊 Yönetici Takip ve Analiz Paneli")
    sifre = st.text_input("Yönetici Şifresi", type="password")
    
    if sifre == YONETICI_SIFRE:
        df = verileri_yukle()
        if not df.empty:
            df['Gün'] = (df['Dönüş'] - df['Başlangıç']).dt.days
            
            # İstatistikler
            st.subheader("📌 Genel İstatistikler")
            m1, m2, m3 = st.columns(3)
            m1.metric("Toplam Talep", len(df))
            subat_sayisi = len(df[df['Başlangıç'].dt.month == 2]) if df['Başlangıç'].notnull().any() else 0
            m2.metric("Şubat Ayı İzinleri", subat_sayisi)
            m3.metric("Toplam Kullanılan Gün", f"{int(df['Gün'].sum()) if 'Gün' in df.columns else 0} Gün")

            # Filtreleme
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                ay_ad = st.selectbox("Aya Göre Süz", ["Hepsi", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs"])
            with c2:
                p_sec = st.multiselect("Personele Göre Süz", df["Ad Soyad"].unique())

            f_df = df.copy()
            if ay_ad != "Hepsi":
                ay_no = {"Ocak":1, "Şubat":2, "Mart":3, "Nisan":4, "Mayıs":5}[ay_ad]
                f_df = f_df[f_df['Başlangıç'].dt.month == ay_no]
            if p_sec:
                f_df = f_df[f_df['Ad Soyad'].isin(p_sec)]

            # Tabloyu Göster
            display_df = f_df.copy()
            for col in ["Tarih", "Başlangıç", "Dönüş"]:
                if col in display_df.columns:
                    display_df[col] = display_df[col].dt.strftime('%d/%m/%Y')
            st.dataframe(display_df, use_container_width=True)

            # Excel İndir
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                f_df.to_excel(writer, index=False)
            st.download_button("📥 Listeyi Excel Olarak İndir", output.getvalue(), f"Izin_Raporu.xlsx")

            # Onay Sistemi
            st.divider()
            st.subheader("✅ Onay Mekanizması")
            bekleyenler = df[df["Durum"] == "Bekliyor"]["Ad Soyad"].tolist()
            if bekleyenler:
                onay_kisi = st.selectbox("Personel Seçin", bekleyenler)
                if st.button("İzni Onayla"):
                    df.loc[(df["Ad Soyad"] == onay_kisi) & (df["Durum"] == "Bekliyor"), "Durum"] = "Onaylandı"
                    df.to_excel(EXCEL_DOSYASI, index=False)
                    st.success(f"{onay_kisi} onaylandı!")
                    st.rerun()
            else:
                st.info("Onay bekleyen kayıt yok.")
        else:
            st.warning("Veri bulunamadı.")

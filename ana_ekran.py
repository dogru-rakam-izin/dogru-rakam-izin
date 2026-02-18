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
        # Tarih analiz sütunları
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B %Y')
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "Odyolog", "İdari", "Destek"])
            izin_tipi = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"])
            tarih_secim = st.date_input("İzin Tarihi")
            if izin_tipi == "Saatlik":
                s1, s2 = st.columns(2)
                saat_bas = s1.time_input("Çıkış")
                saat_bit = s2.time_input("Dönüş")
                bas_str, bit_str = f"{tarih_secim.strftime('%d/%m/%Y')} {saat_bas.strftime('%H:%M')}", f"{tarih_secim.strftime('%d/%m/%Y')} {saat_bit.strftime('%H:%M')}"
            else:
                donus_tarih = st.date_input("İş Başı Tarihi")
                bas_str, bit_str = tarih_secim.strftime('%d/%m/%Y'), donus_tarih.strftime('%d/%m/%Y')
        
        if st.form_submit_button("Talebi Gönder"):
            if ad and tc:
                p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": f"{tur} ({izin_tipi})", "bas": bas_str, "bit": bit_str}
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                st.success("Talebiniz iletildi.")

else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        if not df.empty:
            tab1, tab2, tab3 = st.tabs(["📋 Tüm Hareketler", "📅 Aylık Detay Listesi", "👤 Personel Sorgu"])
            
            with tab1:
                st.subheader("Genel İzin Listesi")
                st.dataframe(df[['Tarih', 'Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş']], use_container_width=True)
            
            with tab2:
                st.subheader("🗓️ Aylara Göre İzin Dağılım Listesi")
                
                # Mevcut ayları listele
                aylar = sorted(df['Ay_Ismi'].dropna().unique())
                secilen_ay = st.selectbox("Görüntülemek İstediğiniz Ayı Seçin", aylar)
                
                # Seçilen aya göre filtrele
                ay_df = df[df['Ay_Ismi'] == secilen_ay]
                
                # Özet bilgi kartları
                k1, k2 = st.columns(2)
                k1.metric("Bu Ay Toplam İzin Sayısı", len(ay_df))
                k2.metric("İzin Kullanan Personel Sayısı", ay_df['Ad Soyad'].nunique())
                
                st.write(f"### {secilen_ay} Ayı İzin Detayları")
                st.table(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Branş']])
                
                # Tür bazlı özet tablo
                st.write("---")
                st.write(f"**{secilen_ay} Ayı Tür Bazlı Dağılım**")
                tur_ozet = ay_df['Tür'].value_counts().reset_index()
                tur_ozet.columns = ['İzin Türü', 'Kullanım Adedi']
                st.table(tur_ozet)

            with tab3:
                st.subheader("👤 Personel Geçmişi")
                kisi = st.selectbox("Personel Seçin", sorted(df['Ad Soyad'].unique()))
                kisi_df = df[df['Ad Soyad'] == kisi]
                st.dataframe(kisi_df[['Tarih_Obj', 'Tür', 'Başlangıç', 'Dönüş']].sort_values('Tarih_Obj', ascending=False))
        else:
            st.info("Henüz kayıt bulunamadı.")

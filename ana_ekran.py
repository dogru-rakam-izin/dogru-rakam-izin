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
        # Tarih formatını ayıklama ve Ay/Yıl sütunu oluşturma
        # Başlangıç sütunundan sadece tarihi alır (Saatlik olsa bile)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Yil'] = df['Tarih_Obj'].dt.strftime('%m-%Y') # 02-2026 formatı
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B %Y') # Şubat 2026 formatı
        return df
    except Exception as e:
        return pd.DataFrame()

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "İdari", "Destek"])
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
                st.success("Talebiniz başarıyla iletildi.")

else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        if not df.empty:
            tab1, tab2, tab3 = st.tabs(["📋 Liste & Kayıt", "📈 Aylık Analiz", "🔍 Personel Bazlı"])
            
            with tab1:
                st.write("### Tüm İzin Hareketleri")
                st.dataframe(df[['Tarih', 'Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Durum']], use_container_width=True)
            
            with tab2:
                st.subheader("📅 Ay Bazlı İzin Dağılımı")
                
                # Ay bazlı gruplama
                aylik_sayi = df['Ay_Ismi'].value_counts().sort_index()
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.bar_chart(aylik_sayi)
                with col2:
                    st.write("**Ay Bazlı Toplamlar**")
                    st.table(aylik_sayi)
                
                st.write("---")
                st.subheader("📊 İzin Türüne Göre Aylık Kırılım")
                pivot_df = df.pivot_table(index='Ay_Ismi', columns='Tür', aggfunc='size', fill_value=0)
                st.dataframe(pivot_df, use_container_width=True)

            with tab3:
                st.subheader("👤 Personel Geçmişi")
                kisi = st.selectbox("Personel Seçin", sorted(df['Ad Soyad'].unique()))
                kisi_df = df[df['Ad Soyad'] == kisi]
                st.metric("Toplam İzin Sayısı", len(kisi_df))
                st.table(kisi_df[['Tür', 'Başlangıç', 'Dönüş']])
        else:
            st.info("Henüz analiz edilecek veri bulunamadı.")
    elif sifre != "":
        st.error("Hatalı Şifre")

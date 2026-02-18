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

# Veri Yükleme ve Ay Analiz Hazırlığı
def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        df.columns = [c.strip() for c in df.columns]
        # Tarih analizi için yardımcı sütunlar
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B %Y')
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli"])

# --- 1. PERSONEL İZİN GİRİŞİ ---
if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    st.subheader("İzin Talebinizi Buradan Oluşturun")
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No (Zorunlu)", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "Odyolog", "İdari", "Destek"])
            izin_tipi = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
            
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"])
            tarih_secim = st.date_input("İzin Tarihi / Başlangıç")
            
            if izin_tipi == "Saatlik":
                s1, s2 = st.columns(2)
                saat_bas = s1.time_input("Çıkış Saati")
                saat_bit = s2.time_input("Dönüş Saati")
                bas_str = f"{tarih_secim.strftime('%d/%m/%Y')} {saat_bas.strftime('%H:%M')}"
                bit_str = f"{tarih_secim.strftime('%d/%m/%Y')} {saat_bit.strftime('%H:%M')}"
            else:
                donus_tarih = st.date_input("İş Başı Tarihi (Dönüş)")
                bas_str = tarih_secim.strftime('%d/%m/%Y')
                bit_str = donus_tarih.strftime('%d/%m/%Y')
        
        st.warning("Beyan: Telafi dersleri planlanmış olup velilere bilgilendirme yapılmıştır.")
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        
        if st.form_submit_button("Talebi Gönder"):
            if ad and tc and onay:
                p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": f"{tur} ({izin_tipi})", "bas": bas_str, "bit": bit_str}
                try:
                    requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                    st.success("Talebiniz yöneticiye iletildi.")
                    st.balloons()
                except:
                    st.error("Bir hata oluştu.")
            else:
                st.error("Lütfen eksik alanları doldurun.")

# --- 2. YÖNETİCİ PANELİ (Giriş, Onay, Analiz) ---
else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        kayitli_personeller = sorted(df['Ad Soyad'].unique().tolist()) if not df.empty else []
        
        tab1, tab2, tab3 = st.tabs(["📝 İzin Girişi & Liste", "📈 Aylık Analiz", "👤 Personel Takip"])
        
        with tab1:
            st.subheader("Hızlı İzin Girişi (Yönetici)")
            with st.expander("Yönetici Olarak Yeni Kayıt Ekle", expanded=False):
                with st.form("yönetici_ekleme"):
                    y_ad_secim = st.selectbox("Personel Seçin", ["Yeni Kayıt..."] + kayitli_personeller)
                    y_ad = st.text_input("İsim Soyisim") if y_ad_secim == "Yeni Kayıt..." else y_ad_secim
                    
                    y_tip = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
                    c1, c2 = st.columns(2)
                    y_tur = c1.selectbox("Tür", ["Yıllık İzin", "Mazeret", "Saatlik İzin", "Rapor"])
                    y_tar = c2.date_input("Tarih")
                    
                    if y_tip == "Saatlik":
                        y_s1 = c1.time_input("Başlangıç Saati")
                        y_s2 = c2.time_input("Bitiş Saati")
                        y_bas, y_bit = f"{y_tar.strftime('%d/%m/%Y')} {y_s1.strftime('%H:%M')}", f"{y_tar.strftime('%d/%m/%Y')} {y_s2.strftime('%H:%M')}"
                    else:
                        y_don = c1.date_input("Dönüş Tarihi")
                        y_bas, y_bit = y_tar.strftime('%d/%m/%Y'), y_don.strftime('%d/%m/%Y')
                    
                    if st.form_submit_button("Sisteme İşle"):
                        p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "---", "ad": y_ad, "brans": "Yönetici Girişi", "tur": f"{y_tur} ({y_tip})", "bas": y_bas, "bit": y_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                        st.success("Kayıt eklendi!")
                        st.rerun()

            st.write("### Güncel İzin Listesi")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.subheader("📅 Ay Bazlı Toplam İzinler")
            if not df.empty:
                aylik_sayi = df['Ay_Ismi'].value_counts()
                st.bar_chart(aylik_sayi)
                st.table(aylik_sayi)
            else:
                st.info("Veri yok.")

        with tab3:
            st.subheader("🔍 Personel Geçmişi")
            if kayitli_personeller:
                secilen = st.selectbox("Personel", kayitli_personeller)
                st.dataframe(df[df['Ad Soyad'] == secilen])
            else:
                st.info("Kayıtlı personel bulunamadı.")
    elif sifre != "":
        st.error("Hatalı şifre!")

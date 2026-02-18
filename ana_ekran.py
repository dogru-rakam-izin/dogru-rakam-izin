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
        df['Başlangıç_DT'] = pd.to_datetime(df['Başlangıç'], dayfirst=True, errors='coerce')
        df['Ay'] = df['Başlangıç_DT'].dt.strftime('%B %Y')
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    st.info("Personel bu alanı kendi izin talepleri için kullanır.")
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No (Zorunlu)", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "Odyolog", "İdari", "Destek Personel"])
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Ücretsiz İzin"])
            bas = st.date_input("Başlangıç Tarihi")
            bit = st.date_input("Dönüş Tarihi")
        
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        submit = st.form_submit_button("Talebi Gönder")
        
        if submit and ad and tc and onay:
            payload = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": tur, "bas": bas.strftime("%d/%m/%Y"), "bit": bit.strftime("%d/%m/%Y")}
            requests.post(APPS_SCRIPT_URL, data=json.dumps(payload))
            st.success("Talebiniz başarıyla iletildi.")

else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        
        tab1, tab2, tab3 = st.tabs(["📝 İzin Girişi & Onay", "📈 Ay Bazlı Analiz", "👤 Personel Takip"])
        
        with tab1:
            st.subheader("Hızlı İzin Girişi (Yönetici)")
            
            # --- OTOMATİK İSİM LİSTESİ OLUŞTURMA ---
            if not df.empty and 'Ad Soyad' in df.columns:
                kayitli_personeller = sorted(df['Ad Soyad'].unique().tolist())
            else:
                kayitli_personeller = []
            
            with st.expander("Yeni Kayıt Ekle", expanded=True):
                with st.form("yönetici_hizli_ekle", clear_on_submit=True):
                    e1, e2 = st.columns(2)
                    
                    # İsim Seçimi (Listede yoksa yeni yazabilir)
                    y_ad_secim = e1.selectbox("Personel Seçin (Kayıtlılar)", ["Yeni Personel Ekle..."] + kayitli_personeller)
                    if y_ad_secim == "Yeni Personel Ekle...":
                        y_ad = e1.text_input("Yeni Personel Adı Soyadı")
                    else:
                        y_ad = y_ad_secim
                    
                    y_tc = e1.text_input("TC No (Opsiyonel - Boş kalabilir)")
                    y_tur = e2.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Ücretsiz İzin"])
                    y_bas = e2.date_input("Başlangıç")
                    y_bit = e2.date_input("Dönüş")
                    
                    y_submit = st.form_submit_button("Kaydı Onaylı Olarak Ekle")
                    
                    if y_submit:
                        if y_ad:
                            p = {
                                "tarih": datetime.now().strftime("%d/%m/%Y"), 
                                "tc": str(y_tc) if y_tc else "---", 
                                "ad": y_ad, 
                                "brans": "Yönetici Girişi", 
                                "tur": y_tur, 
                                "bas": y_bas.strftime("%d/%m/%Y"), 
                                "bit": y_bit.strftime("%d/%m/%Y")
                            }
                            requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                            st.success(f"{y_ad} için izin başarıyla tabloya işlendi!")
                            st.rerun() # Sayfayı yenileyerek listeyi günceller
            
            st.write("---")
            st.write("### Tüm İzin Hareketleri")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.subheader("📅 Aylık Toplam İzin Analizi")
            if not df.empty:
                aylik_ozet = df['Ay'].value_counts().reset_index()
                aylik_ozet.columns = ['Ay', 'İzin Sayısı']
                st.bar_chart(aylik_ozet.set_index('Ay'))
                st.table(aylik_ozet)

        with tab3:
            st.subheader("🔍 Personel Geçmişi Sorgulama")
            if not df.empty:
                secilen_kisi = st.selectbox("Sorgulanacak Personel", kayitli_personeller)
                kisi_df = df[df['Ad Soyad'] == secilen_kisi]
                st.metric("Toplam Kullanılan İzin", f"{len(kisi_df)} Adet")
                st.dataframe(kisi_df[['Tarih', 'Tür', 'Başlangıç', 'Dönüş']])
    
    elif sifre != "":
        st.error("Giriş yetkiniz bulunmuyor.")

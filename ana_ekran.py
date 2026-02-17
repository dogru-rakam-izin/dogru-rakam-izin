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
        # Tarih sütununu gerçek tarih formatına çevir
        df['Başlangıç_DT'] = pd.to_datetime(df['Başlangıç'], dayfirst=True, errors='coerce')
        df['Ay'] = df['Başlangıç_DT'].dt.strftime('%B %Y')
        return df
    except:
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
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "Odyolog", "İdari"])
        with f2:
            tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu"])
            bas = st.date_input("Başlangıç Tarihi")
            bit = st.date_input("Dönüş Tarihi")
        
        submit = st.form_submit_button("Talebi Gönder")
        if submit and ad and tc:
            payload = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": tur, "bas": bas.strftime("%d/%m/%Y"), "bit": bit.strftime("%d/%m/%Y")}
            requests.post(APPS_SCRIPT_URL, data=json.dumps(payload))
            st.success("Talebiniz iletildi.")

else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.text_input("Yönetici Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        
        tab1, tab2, tab3 = st.tabs(["📝 İzin Ekle/Onayla", "📈 Ay Bazlı Analiz", "👤 Personel Takip"])
        
        with tab1:
            st.subheader("Manuel İzin Ekle (Yönetici)")
            with st.expander("Yeni Kayıt Ekle"):
                with st.form("yönetici_ekleme"):
                    e1, e2 = st.columns(2)
                    y_ad = e1.text_input("Personel Adı")
                    y_tc = e1.text_input("TC No")
                    y_tur = e2.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu"])
                    y_bas = e2.date_input("Başlangıç")
                    y_bit = e2.date_input("Dönüş")
                    y_submit = st.form_submit_button("Kaydı Tabloya İşle")
                    if y_submit:
                        p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(y_tc), "ad": y_ad, "brans": "Yönetici Girişi", "tur": y_tur, "bas": y_bas.strftime("%d/%m/%Y"), "bit": y_bit.strftime("%d/%m/%Y")}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                        st.success("Kayıt eklendi!")
            
            st.write("---")
            st.write("### Tüm İzin Talepleri")
            st.dataframe(df, use_container_width=True)

        with tab2:
            st.subheader("📅 Aylık Toplam İzin Kullanımı")
            if not df.empty:
                aylik_ozet = df.groupby('Ay').size().reset_index(name='Toplam İzin Sayısı')
                st.bar_chart(aylik_ozet.set_index('Ay'))
                st.table(aylik_ozet)
            else:
                st.info("Analiz için veri bulunamadı.")

        with tab3:
            st.subheader("🔍 Personel Bazlı Detaylar")
            if not df.empty:
                secilen_kisi = st.selectbox("Personel Seçin", df['Ad Soyad'].unique())
                kisi_df = df[df['Ad Soyad'] == secilen_kisi]
                st.write(f"**{secilen_kisi}** toplamda **{len(kisi_df)}** kez izin kullanmış.")
                st.dataframe(kisi_df[['Tarih', 'Tür', 'Başlangıç', 'Dönüş', 'Durum']])

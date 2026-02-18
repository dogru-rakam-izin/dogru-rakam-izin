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
menu = st.sidebar.radio("MENÜ", ["Personel İzin Formu", "Yönetici Paneli"])

if menu == "Personel İzin Formu":
    st.title("🏢 DOĞRU RAKAM İZİN FORMU")
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Adı Soyadı")
            tc = st.text_input("TC Kimlik No (Zorunlu)", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Özel Eğitim Öğretmeni", "Psikolog", "Odyolog", "İdari", "Destek Personel"])
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
        
        onay = st.checkbox("Bilgilerin doğruluğunu ve telafi ders planını onaylıyorum.")
        submit = st.form_submit_button("Talebi Gönder")
        
        if submit and ad and tc and onay:
            payload = {
                "tarih": datetime.now().strftime("%d/%m/%Y"), 
                "tc": str(tc), 
                "ad": ad, 
                "brans": brans, 
                "tur": f"{tur} ({izin_tipi})", 
                "bas": bas_str, 
                "bit": bit_str
            }
            requests.post(APPS_SCRIPT_URL, data=json.dumps(payload))
            st.success("Talebiniz başarıyla iletildi.")

else:
    st.title("📊 Yönetici Kontrol & Analiz Paneli")
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        kayitli_personeller = sorted(df['Ad Soyad'].unique().tolist()) if not df.empty else []
        
        tab1, tab2 = st.tabs(["📝 İzin Girişi & Liste", "📈 Analiz"])
        
        with tab1:
            with st.expander("Yönetici Olarak İzin Ekle", expanded=False):
                with st.form("yönetici_ekle"):
                    y_ad_secim = st.selectbox("Personel", ["Yeni Personel..."] + kayitli_personeller)
                    y_ad = st.text_input("Yeni İsim") if y_ad_secim == "Yeni Personel..." else y_ad_secim
                    
                    y_tip = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
                    e1, e2 = st.columns(2)
                    y_tur = e1.selectbox("Tür", ["Yıllık İzin", "Mazeret", "Saatlik İzin"])
                    y_tar = e2.date_input("Tarih")
                    
                    if y_tip == "Saatlik":
                        s3, s4 = st.columns(2)
                        y_s1 = s3.time_input("Başlangıç Saati")
                        y_s2 = s4.time_input("Bitiş Saati")
                        y_bas = f"{y_tar.strftime('%d/%m/%Y')} {y_s1.strftime('%H:%M')}"
                        y_bit = f"{y_tar.strftime('%d/%m/%Y')} {y_s2.strftime('%H:%M')}"
                    else:
                        y_donus = st.date_input("Dönüş Tarihi")
                        y_bas = y_tar.strftime('%d/%m/%Y')
                        y_bit = y_donus.strftime('%d/%m/%Y')
                        
                    if st.form_submit_button("Kaydı İşle"):
                        p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "---", "ad": y_ad, "brans": "Yönetici", "tur": f"{y_tur} ({y_tip})", "bas": y_bas, "bit": y_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                        st.success("Kayıt eklendi!")
                        st.rerun()

            st.write("### Güncel Liste")
            st.dataframe(df, use_container_width=True)

        with tab2:
            if not df.empty:
                st.subheader("İstatistikler")
                st.write(df['Tür'].value_counts())
            else:
                st.info("Veri bulunamadı.")
    
    elif sifre != "":
        st.error("Hatalı Şifre")

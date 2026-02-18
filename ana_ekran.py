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
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B %Y')
        return df
    except:
        return pd.DataFrame(columns=["Tarih", "TC No", "Ad Soyad", "Branş", "Tür", "Başlangıç", "Dönüş", "Durum"])

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ SEÇİMİ", ["⬇️ PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

# --- 1. PERSONEL GİRİŞİ ---
if menu == "⬇️ PERSONEL İZİN TALEBİ":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    st.info("Personel İzin Talep Formu")
    
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Ad Soyad")
            tc = st.text_input("TC Kimlik (Zorunlu)", max_chars=11)
            brans = st.selectbox("Branş", ["Uzman Öğretici", "Öğretmen", "Psikolog", "Odyolog", "İdari", "Destek"])
            tip = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
        with f2:
            tur = st.selectbox("Tür", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"])
            tar = st.date_input("İzin Tarihi")
            if tip == "Saatlik":
                s1, s2 = st.columns(2)
                saat1 = s1.time_input("Çıkış")
                saat2 = s2.time_input("Dönüş")
                bas = f"{tar.strftime('%d/%m/%Y')} {saat1.strftime('%H:%M')}"
                bit = f"{tar.strftime('%d/%m/%Y')} {saat2.strftime('%H:%M')}"
            else:
                donus = st.date_input("İş Başı Tarihi")
                bas = tar.strftime('%d/%m/%Y')
                bit = donus.strftime('%d/%m/%Y')
        
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        submit_btn = st.form_submit_button("TALEBİ GÖNDER")
        
        if submit_btn:
            if ad and tc and onay:
                p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": brans, "tur": f"{tur} ({tip})", "bas": bas, "bit": bit}
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                st.success("Başarıyla gönderildi.")
                st.balloons()
            else:
                st.error("Lütfen ad, TC ve onay kutusunu doldurun.")

# --- 2. YÖNETİCİ PANELİ ---
else:
    st.title("🔐 YÖNETİCİ KONTROL PANELİ")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        kayitli_personeller = sorted(df['Ad Soyad'].unique().tolist()) if not df.empty else []

        st.subheader("📝 YÖNETİCİ İZİN GİRİŞİ (MANUEL)")
        with st.expander("Yeni İzin Kaydı Ekle", expanded=True):
            with st.form("yönetici_manuel_giris"):
                y1, y2 = st.columns(2)
                y_ad_secim = y1.selectbox("Kayıtlı Personel Seç", ["Yeni İsim Yaz..."] + kayitli_personeller)
                y_ad = y1.text_input("Ad Soyad (Yeni ise)") if y_ad_secim == "Yeni İsim Yaz..." else y_ad_secim
                
                y_tip = y2.radio("İzin Tipi", ["Tam Gün", "Saatlik"], horizontal=True)
                y_tur = y1.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret", "Saatlik", "Rapor"])
                y_tar = y2.date_input("Tarih")
                
                if y_tip == "Saatlik":
                    y_s1, y_s2 = y2.columns(2)
                    y_saat1 = y_s1.time_input("Başla")
                    y_saat2 = y_s2.time_input("Bitir")
                    y_bas, y_bit = f"{y_tar.strftime('%d/%m/%Y')} {y_saat1.strftime('%H:%M')}", f"{y_tar.strftime('%d/%m/%Y')} {y_saat2.strftime('%H:%M')}"
                else:
                    y_don = y2.date_input("İş Başı")
                    y_bas, y_bit = y_tar.strftime('%d/%m/%Y'), y_don.strftime('%d/%m/%Y')
                
                y_submit = st.form_submit_button("KAYDI TABLOYA EKLE")
                
                if y_submit:
                    p_y = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "---", "ad": y_ad, "brans": "YÖNETİCİ", "tur": f"{y_tur} ({y_tip})", "bas": y_bas, "bit": y_bit}
                    requests.post(APPS_SCRIPT_URL, data=json.dumps(p_y))
                    st.success(f"{y_ad} için kayıt eklendi!")
                    st.rerun()

        st.write("---")
        
        st.subheader("🗓️ AYLIK İZİN LİSTESİ")
        if not df.empty:
            aylar = sorted(df['Ay_Ismi'].dropna().unique())
            if aylar:
                secilen_ay = st.selectbox("Görüntülenecek Ay", aylar)
                ay_df = df[df['Ay_Ismi'] == secilen_ay]
                st.info(f"{secilen_ay} ayında toplam {len(ay_df)} izin kaydı bulundu.")
                st.table(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Branş']])
            else:
                st.info("Kayıtlı veri bulunamadı.")
        else:
            st.warning("Henüz hiç kayıt yok.")
            
    elif sifre != "":
        st.error("Giriş Başarısız")

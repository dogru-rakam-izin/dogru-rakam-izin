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
        
        def sure_hesapla(row):
            try:
                if "Saatlik" in str(row['Tür']):
                    fmt = "%d/%m/%Y %H:%M"
                    bas = datetime.strptime(row['Başlangıç'], fmt)
                    bit = datetime.strptime(row['Dönüş'], fmt)
                    fark = bit - bas
                    return round(fark.seconds / 3600, 1)
                else:
                    fmt = "%d/%m/%Y"
                    bas = datetime.strptime(row['Başlangıç'], fmt)
                    bit = datetime.strptime(row['Dönüş'], fmt)
                    fark = (bit - bas).days
                    return int(fark)
            except:
                return 0

        df['Sure_Deger'] = df.apply(sure_hesapla, axis=1)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B %Y')
        return df
    except:
        return pd.DataFrame()

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ SEÇİMİ", ["⬇️ PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "⬇️ PERSONEL İZİN TALEBİ":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    with st.form("personel_formu", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            ad = st.text_input("Ad Soyad")
            tc = st.text_input("TC Kimlik No", max_chars=11)
            tip = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
        with f2:
            tur = st.selectbox("Tür", ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"])
            tar = st.date_input("İzin Tarihi")
            if tip == "Saatlik":
                s1, s2 = st.columns(2)
                saat1 = s1.time_input("Çıkış")
                saat2 = s2.time_input("Dönüş")
                bas, bit = f"{tar.strftime('%d/%m/%Y')} {saat1.strftime('%H:%M')}", f"{tar.strftime('%d/%m/%Y')} {saat2.strftime('%H:%M')}"
            else:
                donus = st.date_input("İş Başı Tarihi")
                bas, bit = tar.strftime('%d/%m/%Y'), donus.strftime('%d/%m/%Y')
        
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad and tc and onay:
                p = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": "Personel", "tur": f"{tur} ({tip})", "bas": bas, "bit": bit}
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p))
                st.success("Talebiniz iletildi.")

else:
    st.title("🔐 YÖNETİCİ KONTROL PANELİ")
    sifre = st.sidebar.text_input("Giriş Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        
        if not df.empty:
            tab1, tab2 = st.tabs(["📊 Aylık Personel Özeti (Çıktı Al)", "📝 Manuel İzin Girişi"])
            
            with tab1:
                aylar = sorted(df['Ay_Ismi'].dropna().unique())
                secilen_ay = st.selectbox("Analiz Edilecek Ayı Seçin", aylar)
                ay_df = df[df['Ay_Ismi'] == secilen_ay].copy()
                
                # Personel Bazlı Özetleme Hesaplama
                ay_df['Günlük'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" not in str(x['Tür']) else 0, axis=1)
                ay_df['Saatlik'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" in str(x['Tür']) else 0, axis=1)
                
                ozet_tablo = ay_df.groupby('Ad Soyad').agg({
                    'Günlük': 'sum',
                    'Saatlik': 'sum',
                    'Tür': 'count'
                }).rename(columns={'Tür': 'İzin Adedi', 'Günlük': 'Toplam Gün', 'Saatlik': 'Toplam Saat'})
                
                st.write(f"### 🗓️ {secilen_ay} Ayı Personel İzin Karnesi")
                st.table(ozet_tablo)
                
                # İNDİRME BUTONU
                csv = ozet_tablo.to_csv(index=True).encode('utf-16')
                st.download_button(
                    label="📥 Özet Listeyi İndir (Excel/CSV)",
                    data=csv,
                    file_name=f"{secilen_ay}_izin_ozeti.csv",
                    mime="text/csv",
                )
                
                st.write("---")
                st.write("🔍 **Ay İçindeki Tüm Hareketler (Detay):**")
                st.dataframe(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Sure_Deger']])

            with tab2:
                with st.form("admin_manuel_giris", clear_on_submit=True):
                    st.subheader("Yeni Kayıt Ekle")
                    y_ad = st.text_input("Personel Ad Soyad")
                    y_tip = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
                    y_tur = st.selectbox("Tür", ["Yıllık", "Mazeret", "Saatlik", "Rapor"])
                    y_tar = st.date_input("Tarih")
                    if y_tip == "Saatlik":
                        s1, s2 = st.columns(2)
                        y_saat1 = s1.time_input("Başla")
                        y_saat2 = s2.time_input("Bitir")
                        y_bas, y_bit = f"{y_tar.strftime('%d/%m/%Y')} {y_saat1.strftime('%H:%M')}", f"{y_tar.strftime('%d/%m/%Y')} {y_saat2.strftime('%H:%M')}"
                    else:
                        y_don = st.date_input("Dönüş")
                        y_bas, y_bit = y_tar.strftime('%d/%m/%Y'), y_don.strftime('%d/%m/%Y')
                    
                    if st.form_submit_button("Sisteme Kaydet"):
                        p_y = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "---", "ad": y_ad, "brans": "Yönetici", "tur": f"{y_tur} ({y_tip})", "bas": y_bas, "bit": y_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(p_y))
                        st.success("Kaydedildi!")
                        st.rerun()
        else:
            st.warning("Veritabanı boş.")
    elif sifre != "":
        st.error("Hatalı Şifre!")

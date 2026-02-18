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

# Türkçe Ay Sözlüğü
TR_AYLAR = {
    "January": "Ocak", "February": "Şubat", "March": "Mart", "April": "Nisan",
    "May": "Mayıs", "June": "Haziran", "July": "Temmuz", "August": "Ağustos",
    "September": "Eylül", "October": "Ekim", "November": "Kasım", "December": "Aralık"
}

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
                    # Saati net sayı olarak döndür (örn: 2.5)
                    return float(round(fark.seconds / 3600, 1))
                else:
                    fmt = "%d/%m/%Y"
                    bas = datetime.strptime(row['Başlangıç'], fmt)
                    bit = datetime.strptime(row['Dönüş'], fmt)
                    fark = (bit - bas).days
                    # Günü net sayı olarak döndür (örn: 5)
                    return int(fark)
            except:
                return 0

        df['Sure_Deger'] = df.apply(sure_hesapla, axis=1)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        
        # Ay ismini al ve Türkçeye çevir
        df['Ay_Ing'] = df['Tarih_Obj'].dt.strftime('%B')
        df['Yil'] = df['Tarih_Obj'].dt.strftime('%Y')
        df['Ay_Ismi'] = df['Ay_Ing'].map(TR_AYLAR) + " " + df['Yil']
        
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
                
                ay_df['Günlük'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" not in str(x['Tür']) else 0, axis=1)
                ay_df['Saatlik'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" in str(x['Tür']) else 0, axis=1)
                
                ozet_tablo = ay_df.groupby('Ad Soyad').agg({
                    'Günlük': 'sum',
                    'Saatlik': 'sum',
                    'Tür': 'count'
                }).rename(columns={'Tür': 'İzin Adedi', 'Günlük': 'Toplam Gün', 'Saatlik': 'Toplam Saat'})
                
                # Sayı formatını düzeltme (5.000 -> 5)
                ozet_tablo['Toplam Gün'] = ozet_tablo['Toplam Gün'].astype(int)
                ozet_tablo['Toplam Saat'] = ozet_tablo['Toplam Saat'].apply(lambda x: int(x) if x == int(x) else x)

                st.write(f"### 🗓️ {secilen_ay} Personel İzin Karnesi")
                st.table(ozet_tablo)
                
                csv = ozet_tablo.to_csv(index=True).encode('utf-16')
                st.download_button(
                    label=f"📥 {secilen_ay} Özetini İndir",
                    data=csv,
                    file_name=f"{secilen_ay}_ozet.csv",
                    mime="text/csv",
                )
                
                st.write("---")
                st.write("🔍 **Detaylı Hareket Listesi:**")
                st.dataframe(ay_df[['Ad Soyad', 'Tür', 'Başlangıç

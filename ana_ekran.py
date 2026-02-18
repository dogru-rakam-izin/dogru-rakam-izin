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

# --- İZİN TÜRLERİ ---
IZIN_LISTESI = [
    "Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", 
    "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", 
    "Vefat İzni", "Babalık İzni"
]

def verileri_yukle():
    try:
        # Veriyi çek ve boşlukları temizle
        df = pd.read_csv(SHEET_READ_URL)
        if df.empty:
            return pd.DataFrame()
            
        df.columns = [c.strip() for c in df.columns]
        
        # Tarih Dönüşümü (Hata payını azaltmak için formatı zorluyoruz)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        
        # Eğer tarih okunamadıysa satırı atla
        df = df.dropna(subset=['Tarih_Obj'])
        
        def sure_hesapla(row):
            try:
                if "Saatlik" in str(row['Tür']):
                    fmt = "%d/%m/%Y %H:%M"
                    bas = datetime.strptime(str(row['Başlangıç']), fmt)
                    bit = datetime.strptime(str(row['Dönüş']), fmt)
                    fark = bit - bas
                    return float(round(fark.seconds / 3600, 1))
                else:
                    fmt = "%d/%m/%Y"
                    bas = datetime.strptime(str(row['Başlangıç']), fmt)
                    bit = datetime.strptime(str(row['Dönüş']), fmt)
                    fark = (bit - bas).days
                    return int(fark)
            except:
                return 0

        df['Sure_Deger'] = df.apply(sure_hesapla, axis=1)
        df['Ay_Ing'] = df['Tarih_Obj'].dt.strftime('%B')
        df['Yil'] = df['Tarih_Obj'].dt.strftime('%Y')
        df['Ay_Ismi'] = df['Ay_Ing'].map(TR_AYLAR) + " " + df['Yil']
        return df
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return pd.DataFrame()

# --- MENÜ ---
menu = st.sidebar.radio("MENÜ SEÇİMİ", ["⬇️ PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "⬇️ PERSONEL İZİN TALEBİ":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC Kimlik No", max_chars=11)
    tip = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    
    with st.form("personel_formu_v4"):
        f1, f2 = st.columns(2)
        with f1:
            tur = st.selectbox("İzin Türü", IZIN_LISTESI)
            tar = st.date_input("İzin Tarihi")
            
        with f2:
            if tip == "Saatlik":
                s1, s2 = st.columns(2)
                saat1 = s1.time_input("Çıkış Saati")
                saat2 = s2.time_input("Dönüş Saati")
                bas_str = f"{tar.strftime('%d/%m/%Y')} {saat1.strftime('%H:%M')}"
                bit_str = f"{tar.strftime('%d/%m/%Y')} {saat2.strftime('%H:%M')}"
            else:
                donus = st.date_input("İş Başı Tarihi")
                bas_str = tar.strftime('%d/%m/%Y')
                bit_str = donus.strftime('%d/%m/%Y')
        
        onay = st.checkbox("Bilgilerin doğruluğunu onaylıyorum.")
        submit = st.form_submit_button("TALEBİ GÖNDER")
        
        if submit:
            if ad and tc and onay:
                p_data = {
                    "tarih": datetime.now().strftime("%d/%m/%Y"),
                    "tc": str(tc), "ad": ad, "brans": "Personel",
                    "tur": f"{tur} ({tip})", "bas": bas_str, "bit": bit_str
                }
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p_data))
                st.success(f"Talebiniz ({tur}) başarıyla iletildi.")
                st.balloons()
            else:
                st.warning("Lütfen tüm alanları doldurun.")

else:
    st.title("🔐 YÖNETİCİ KONTROL PANELİ")
    sifre = st.sidebar.text_input("Giriş Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        
        if df is not None and not df.empty:
            tab1, tab2 = st.tabs(["📊 Aylık Personel Karnesi", "📝 Manuel İzin Girişi"])
            
            with tab1:
                aylar = sorted(df['Ay_Ismi'].unique(), reverse=True)
                sec_ay = st.selectbox("İncelemek İstediğiniz Ayı Seçin", aylar)
                
                ay_df = df[df['Ay_Ismi'] == sec_ay].copy()
                
                # Hesaplamalar
                ay_df['Günlük'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" not in str(x['Tür']) else 0, axis=1)
                ay_df['Saatlik'] = ay_df.apply(lambda x: x['Sure_Deger'] if "Saatlik" in str(x['Tür']) else 0, axis=1)
                
                karne = ay_df.groupby('Ad Soyad').agg({'Günlük': 'sum', 'Saatlik': 'sum', 'Tür': 'count'})
                karne.columns = ['Toplam Gün', 'Toplam Saat', 'Kayıt Adedi']
                
                st.subheader(f"🗓️ {sec_ay} Personel Karnesi")
                st.table(karne)
                
                st.write("---")
                st.write("🔍 **Detaylı Hareket Listesi:**")
                st.dataframe(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Sure_Deger']])
            
            with tab2:
                y_ad = st.text_input("Personel Ad Soyad")
                y_tip = st.radio("İzin Tipi (Admin)", ["Tam Gün", "Saatlik"], horizontal=True)
                
                with st.form("admin_manuel_form_v4"):
                    y_tur = st.selectbox("İzin Türü", IZIN_LISTESI)
                    y_tar = st.date_input("Tarih")
                    
                    if y_tip == "Saatlik":
                        c1, c2 = st.columns(2)
                        y_s1 = c1.time_input("Başla")
                        y_s2 = c2.time_input("Bitir")
                        y_bas, y_bit = f"{y_tar.strftime('%d/%m/%Y')} {y_s1.strftime('%H:%M')}", f"{y_tar.strftime('%d/%m/%Y')} {y_s2.strftime('%H:%M')}"
                    else:
                        y_don = st.date_input("İş Başı")
                        y_bas, y_bit = y_tar.strftime('%d/%m/%Y'), y_don.strftime('%d/%m/%Y')
                    
                    if st.form_submit_button("Sisteme Kaydet"):
                        p_y = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "---", "ad": y_ad, "brans": "Yönetici", "tur": f"{y_tur} ({y_tip})", "bas": y_bas, "bit": y_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(p_y))
                        st.success("Kayıt başarıyla eklendi!")
                        st.rerun()
        else:
            st.warning("Henüz hiç kayıt bulunamadı veya Google Sheets bağlantısı bekleniyor. Lütfen 'Personel İzin Talebi' kısmından bir deneme kaydı oluşturun.")
    elif sifre != "":
        st.error("Hatalı Giriş Şifresi!")

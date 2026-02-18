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
    "Vefat İzni", "Babalık İzni", "Eğitim / Seminer"
]

def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        
        def sure_ayristir(row):
            try:
                if "Saatlik" in str(row['Tür']):
                    fmt = "%d/%m/%Y %H:%M"
                    bas = datetime.strptime(str(row['Başlangıç']), fmt)
                    bit = datetime.strptime(str(row['Dönüş']), fmt)
                    fark = bit - bas
                    return 0, float(round(fark.seconds / 3600, 1))
                else:
                    fmt = "%d/%m/%Y"
                    bas = datetime.strptime(str(row['Başlangıç']), fmt)
                    bit = datetime.strptime(str(row['Dönüş']), fmt)
                    fark = (bit - bas).days
                    return int(fark), 0
            except: return 0, 0

        df[['Gun_Deger', 'Saat_Deger']] = df.apply(lambda r: pd.Series(sure_ayristir(r)), axis=1)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B').map(TR_AYLAR) + " " + df['Tarih_Obj'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

menu = st.sidebar.radio("MENÜ SEÇİMİ", ["⬇️ PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "⬇️ PERSONEL İZİN TALEBİ":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC Kimlik No", max_chars=11)
    tip = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    
    with st.form("p_form_final_v4"):
        f1, f2 = st.columns(2)
        with f1:
            tur = st.selectbox("İzin Türü", IZIN_LISTESI)
            tar = st.date_input("İzin Tarihi")
        with f2:
            if tip == "Saatlik":
                s1 = st.time_input("Çıkış Saati")
                s2 = st.time_input("Dönüş Saati")
                bas_str = f"{tar.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}"
                bit_str = f"{tar.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
            else:
                donus = st.date_input("İş Başı Tarihi")
                bas_str = tar.strftime('%d/%m/%Y')
                bit_str = donus.strftime('%d/%m/%Y')
        
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad and tc:
                p_data = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": "Personel", "tur": f"{tur} ({tip})", "bas": bas_str, "bit": bit_str}
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p_data))
                st.success("Talebiniz iletildi!")
                st.balloons()

else:
    st.title("🔐 YÖNETİCİ KONTROL PANELİ")
    sifre = st.sidebar.text_input("Giriş Şifresi", type="password")
    
    if sifre == "1234":
        df = verileri_yukle()
        tab1, tab2 = st.tabs(["📊 Aylık Personel Karnesi", "📝 Manuel İzin Girişi"])
        
        with tab1:
            if not df.empty:
                aylar = sorted(df['Ay_Ismi'].dropna().unique(), reverse=True)
                if aylar:
                    sec_ay = st.selectbox("Ay Seçin", aylar)
                    ay_df = df[df['Ay_Ismi'] == sec_ay].copy()
                    
                    karne = ay_df.groupby('Ad Soyad').agg({'Gun_Deger': 'sum', 'Saat_Deger': 'sum', 'Tür': 'count'})
                    karne.columns = ['Toplam Gün', 'Toplam Saat', 'Kayıt Sayısı']
                    
                    karne['Toplam Gün'] = karne['Toplam Gün'].apply(lambda x: int(x) if x == int(x) else round(x, 1))
                    karne['Toplam Saat'] = karne['Toplam Saat'].apply(lambda x: int(x) if x == int(x) else round(x, 1))
                    
                    st.table(karne)
                    st.write("---")
                    st.dataframe(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Gun_Deger', 'Saat_Deger']])
                else:
                    st.info("Henüz bu ay için veri yok.")
            else:
                st.info("Veritabanı boş.")

        with tab2:
            st.subheader("📝 Manuel İzin Girişi")
            m_ad = st.text_input("Personel Adı Soyadı")
            m_tip = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], key="m_key_v4")
            
            with st.form("m_form_final_v4"):
                m_tur = st.selectbox("İzin Türü", IZIN_LISTESI)
                m_tar = st.date_input("İzin Tarihi")
                if m_tip == "Saatlik":
                    m_s1 = st.time_input("Başla")
                    m_s2 = st.time_input("Bitir")
                    m_bas = f"{m_tar.strftime('%d/%m/%Y')} {m_s1.strftime('%H:%M')}"
                    m_bit = f"{m_tar.strftime('%d/%m/%Y')} {m_s2.strftime('%H:%M')}"
                else:
                    m_don = st.date_input("İş Başı")
                    m_bas = m_tar.strftime('%d/%m/%Y')
                    m_bit = m_don.strftime('%d/%m/%Y')
                
                if st.form_submit_button("Sisteme Manuel Kaydet"):
                    if m_ad:
                        m_data = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "000", "ad": m_ad, "brans": "Yönetici", "tur": f"{m_tur} ({m_tip})", "bas": m_bas, "bit": m_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(m_data))
                        st.success("Kayıt eklendi!")
                        st.rerun()
                    else:
                        st.error("İsim girilmesi zorunludur.")
    elif sifre != "":
        st.error("Hatalı Şifre!")

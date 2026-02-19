import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE AYARLAR ---
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"
st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- PERSONEL VERİTABANI ---
PERSONEL_GIRISLERI = {
    "ARİF EMRE YILDIZ": "2024-10-09","ARZU ÖZELMİŞ": "2024-10-09", 
    "AYŞE KOLBAŞ": "2022-03-04",
    "AYŞE GÜLLÜ ÇIRAY": "2023-04-27", "BURAK ÖZAYDIN": "2025-09-11",
    "BUSE MEYRİLİ": "2025-02-07", "ERSİN KALSEN": "2023-06-06",
    "FERİDE CIKKAN": "2025-03-13", "GÖKÇE DÖNMEZKOL": "2025-06-24",
    "HİDAYET ARZU ER": "2025-02-07", "HÜSEYİN KIZIL": "2025-11-18",
    "İBRAHİM SOYLU": "2020-09-17", "MERVE ANAYURT": "2025-03-11",
    "MİZGİN BİDER": "2025-09-15", "NEFİSE NUR HOŞGÖR": "2025-06-09",
    "ÖZLEM KAPLAN": "2024-08-01", "PINAR TANRIVERDİ": "1900-01-01",
    "SAMET DEMİREL": "2024-02-27", "SELEN ŞEN": "2025-11-03"
}

# --- AYARLAR ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]

def hakedis_bul(yil):
    if yil < 1: return 0
    if yil < 5: return 14
    if yil < 15: return 20
    return 26

def yukle():
    bos_df = pd.DataFrame()
    try:
        df = pd.read_csv(CSV)
        if df.empty: return bos_df, "Ad Soyad"
        
        df.columns = [str(c).strip() for c in df.columns]
        
        # Sütun tespiti
        ad_col = "Ad Soyad"
        if ad_col not in df.columns:
            # Eğer başlık farklıysa ilk 3 sütundan birini seçmeye çalış
            for col in df.columns:
                if "AD" in col.upper() or "SOYAD" in col.upper():
                    ad_col = col
                    break
        
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        def h(r):
            try:
                ts = str(r['Tür'])
                b_str, d_str = str(r['Başlangıç']).strip(), str(r['Dönüş']).strip()
                if "Saatlik" in ts:
                    b, d = datetime.strptime(b_str, F_TAM), datetime.strptime(d_str, F_TAM)
                    return 0, round((d-b).total_seconds()/3600, 1)
                else:
                    b, d = datetime.strptime(b_str[:10], F_TARIH), datetime.strptime(d_str[:10], F_TARIH)
                    return (d-b).days, 0
            except: return 0, 0
            
        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0].astype(float), res[1].astype(float)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df, ad_col
    except:
        return bos_df, "Ad Soyad"

# --- TASARIM ---
st.markdown(f"<style>[data-testid='stSidebarNav'] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }} .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; }} div.stButton > button {{ background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; }} [data-testid='stMetricValue'] {{ color: #CC0000; font-weight: bold; }}</style>", unsafe_allow_html=True)

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if m == "👤 PERSONEL GİRİŞİ":
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad").upper(); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.expander("📝 Başvuru Formu", expanded=True):
        with st.form("p_f"):
            t1 = st.selectbox("Tür", IZ); t2 = st.date_input("İzin Günü")
            if tp == "Saatlik":
                s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
            else:
                dn = st.date_input("İş Başı")
                b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
            if st.form_submit_button("GÖNDER") and ad:
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
                st.success("İletildi!")

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        df, ad_sutunu = yukle()
        t = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin", "🗑️ Liste"])
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

        with t[0]: # Karne
            if not df.empty and 'Ay' in df.columns:
                ay_list = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ay_list:
                    ay = st.selectbox("Ay Seç", ay_list)
                    st.dataframe(df[df['Ay']==ay].groupby([ad_sutunu,'Tür'])[['G','S']].sum(), use_container_width=True)
            else: st.info("Henüz analiz edilecek veri yok.")

        with t[1]: # Sicil
            p = st.selectbox("Personel", p_listesi)
            if not df.empty:
                st.dataframe(df[df[ad_sutunu]==p][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)

        with t[2]: # Manuel
            with st.form("m_f"):
                m_ad = st.selectbox("Personel", p_listesi)
                m_tp = st.selectbox("Tip", ["Tam Gün", "Saatlik"])
                m_tr = st.selectbox("Tür", IZ)
                m_tarih = st.date_input("Tarih")
                ms1, ms2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                m_db = st.date_input("İş Başı")
                if st.form_submit_button("KAYDET"):
                    mb, md = (f"{m_tarih.strftime(F_TARIH)} {ms1.strftime(F_SAAT)}", f"{m_tarih.strftime(F_TARIH)} {ms2.strftime(F_SAAT)}") if m_tp == "Saatlik" else (m_tarih.strftime(F_TARIH), m_db.strftime(F_TARIH))
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} ({m_tp})","bas":mb,"bit":md}))
                    st.success("Kayıt Eklendi!"); st.rerun()

        with t[3]: # Yıllık İzin
            py = st.selectbox("Personel Seç", p_listesi, key="py_y")
            varsay_t = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            gt = st.date_input("İşe Giriş", value=varsay_t)
            kidem = datetime.now().year - gt.year
            if (datetime.now().month, datetime.now().day) < (gt.month, gt.day): kidem -= 1
            hk = hakedis_bul(max(0, kidem))
            ku = 0
            if not df.empty and 'Tür' in df.columns:
                ku = df[(df[ad_sutunu]==py) & (df['Tür'].str.contains("Yıllık"))]['G'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")

        with t[4]: # Liste
            if not df.empty: st.dataframe(df.tail(20), use_container_width=True)
            st.link_button("🚀 Google Sheets Aç/Sil", f"https://docs.google.com/spreadsheets/d/{S_ID}/edit")
    else: st.warning("Şifre giriniz.")



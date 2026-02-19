import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE AYARLAR ---
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"
st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- İŞE GİRİŞ TARİHLERİ (Burayı personelinize göre güncelleyebilirsiniz) ---
GIRIS_TARIHLERI = {
    "Örnek Personel": "2022-05-15",
    "Fatih Öncü": "2023-01-01"
}

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebarNav"] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }}
    .main-title {{ color: #CC0000; font-size: 40px; font-weight: bold; margin-bottom: 0px; }}
    div.stButton > button:first-child {{ background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; height: 3em; }}
    [data-testid="stMetricValue"] {{ color: #CC0000; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

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
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                ts = str(r['Tür'])
                f = F_TAM if "Saatlik" in ts else F_TARIH
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in ts: return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0].astype(float), res[1].astype(float)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if "PERSONEL" in m:
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad"); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.expander("📝 İzin Başvuru Formu", expanded=True):
        with st.form("p_f"):
            t1 = st.selectbox("İzin Türü", IZ); t2 = st.date_input("Başlangıç Tarihi")
            if tp == "Saatlik":
                s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
            else:
                dn = st.date_input("İş Başı Tarihi")
                b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
            if st.form_submit_button("BAŞVURUYU GÖNDER") and ad:
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
                st.balloons(); st.success("Talebiniz iletildi!")
else:
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        if not df.empty:
            t = st.tabs(["📊 Karne", "👤 Personel Sicil", "📝 Manuel Giriş", "📅 Yıllık İzin", "🗑️ Veri Yönetimi"])
            with t[0]:
                ay = st.selectbox("Dönem", sorted(df['Ay'].dropna().unique(), reverse=True))
                st.dataframe(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum(), use_container_width=True)
            with t[1]:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)
            with t[2]:
                with st.form("m_f"):
                    m_ad = st.text_input("İsim Soyad"); m_tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
                    m_tr = st.selectbox("Tür", IZ); m_b = st.date_input("Başlangıç"); m_d = st.date_input("Dönüş/İş Başı")
                    if st.form_submit_button("KAYDET") and m_ad:
                        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} ({m_tp})","bas":m_b.strftime(F_TARIH),"bit":m_d.strftime(F_TARIH)}))
                        st.success("Kayıt eklendi!"); st.rerun()
            with t[3]:
                py = st.selectbox("Sorgula", sorted(df['Ad Soyad'].unique()), key="py")
                varsayilan_giris = datetime.strptime(GIRIS_TARIHLERI.get(py, "2024-01-01"), "%Y-%m-%d")
                gt = st.date_input("İşe Giriş Tarihi", value=varsayilan_giris)
                kd = (datetime.now().year - gt.year); hk = hakedis_bul(kd)
                ku = df[(df['Ad Soyad']==py) & (df['Tür'].str.contains("Yıllık"))]['G'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Toplam Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")
            with t[4]:
                st.warning("Silmek istediğiniz satırı yanındaki kutucuktan seçemezsiniz. Google Sheets üzerinden silmeniz önerilir ancak buradan son girilen kayıtları görebilirsiniz.")
                st.dataframe(df.tail(10))
    else: st.info("Şifre giriniz.")

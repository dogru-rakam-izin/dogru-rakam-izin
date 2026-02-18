import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE KURUMSAL AYARLAR ---
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebarNav"] {{
        background-image: url({LOGO_URL});
        background-repeat: no-repeat;
        padding-top: 140px;
        background-position: center 20px;
        background-size: 150px auto;
    }}
    .main-title {{ color: #CC0000; font-size: 40px; font-weight: bold; margin-bottom: 0px; }}
    .sub-title {{ color: #333; font-size: 18px; margin-top: -10px; font-weight: 600; }}
    div.stButton > button:first-child {{
        background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; border: none; height: 3.5em;
    }}
    div.stButton > button:hover {{ background-color: #990000; color: white; }}
    [data-testid="stMetricValue"] {{ color: #CC0000; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- ÜST KISIM ---
col_logo, col_text = st.columns([1, 4])
with col_logo:
    st.image(LOGO_URL, width=200)
with col_text:
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Rehabilitasyon Merkezi Personel İzin Yönetim Sistemi</p>', unsafe_allow_html=True)

# --- AYARLAR ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]
TP_LIST = ["Tam Gün", "Saatlik"]

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
                if "Saatlik" in ts:
                    return 0, round((d-b).total_seconds()/3600, 1)
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
    ad_c, tc_c = st.columns(2)
    ad = ad_c.text_input("Ad Soyad")
    tc = tc_c.text_input("TC Kimlik No", max_chars=11)
    tp = st.radio("İzin Süresi", TP_LIST, horizontal=True)
    
    with st.expander("📝 İzin Başvuru Formu", expanded=True):
        with st.form("p_form"):
            t1 = st.selectbox("İzin Türü", IZ)
            t2 = st.date_input("Başlangıç Tarihi")
            fmt = t2.strftime(F_TARIH)
            if tp == "Saatlik":
                s1, s2 = st.time_input("Çıkış Saati"), st.time_input("Dönüş Saati")
                b, d = f"{fmt} {s1.strftime(F_SAAT)}", f"{fmt} {s2.strftime(F_SAAT)}"
            else:
                dn = st.date_input("İş Başı Tarihi")
                b, d = fmt, dn.strftime(F_TARIH)
            
            if st.form_submit_button("BAŞVURUYU TAMAMLA") and ad:
                now = datetime.now().strftime(F_TARIH)
                pay = {"tarih":now,"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}
                requests.post(URL, data=json.dumps(pay))
                st.balloons()
                st.success("Talebiniz yönetime iletildi!")
else:
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    if sifre == "1234":
        df = yukle()
        if not df.empty:
            t = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin"])
            with t[0]:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ays:
                    ay = st.selectbox("Dönem Seç", ays)
                    st.dataframe(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().style.format("{:.1f}"), use_container_width=True)
            with t[1]:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)
            with t[2]:
                with st.form("m_form"):
                    m_ad = st.text_input("İsim Soyad")
                    m_tp = st.radio("Tip", TP_LIST, horizontal=True)
                    tr, ta = st.selectbox("İzin Türü ", IZ), st.date_input("Tarih ")
                    if st.form_submit_button("KAYDI EKLE") and m_ad:
                        now = datetime.now().strftime(F_TARIH)
                        p_m = {"tarih":now,"tc":"0","ad":m_ad,"brans":"Y","tur":f"{tr} ({m_tp})","bas":ta.strftime(F_TARIH),"bit":ta.strftime(F_TARIH)}
                        requests.post(URL, data=json.dumps(p_m))
                        st.success("Kayıt eklendi!"); st.rerun()
            with t[3]:
                py = st.selectbox("Sorgula", sorted(df['Ad Soyad'].unique()), key="py")
                gt = st.date_input("İşe Giriş", value=datetime(2023, 1, 1))
                kd = (2026 - gt.year)
                hk = hakedis_bul(kd)
                df_yil = df[(df['Ad Soyad']==py) & (df['Tür'].str.contains("Yıllık", na=False))]
                ku = df_yil['G'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Toplam Hak", f"{hk} G")
                c2.metric("Kullanılan", f"{ku:.1f} G")
                c3.metric("Kalan", f"{hk-ku:.1f} G")
                st.dataframe(df_yil[['Başlangıç', 'Dönüş', 'G']], use_container_width=True)
    else:
        st.info("Erişim için şifre gereklidir.")

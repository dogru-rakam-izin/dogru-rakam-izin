import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- TASARIM VE RENKLENDİRME (CSS) ---
st.set_page_config(page_title="Doğru Rakam İzin", layout="wide")

st.markdown("""
    <style>
    /* Ana Başlık Rengi */
    .main-title { color: #1E88E5; font-size: 36px; font-weight: bold; text-align: center; margin-bottom: 20px; }
    
    /* Butonları Renklendirme */
    div.stButton > button:first-child {
        background-color: #1E88E5; color: white; border-radius: 10px; border: none; height: 3em; width: 100%; font-weight: bold;
    }
    div.stButton > button:hover { background-color: #1565C0; color: white; border: none; }
    
    /* Yan Menü Tasarımı */
    [data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }
    
    /* Tablo ve Veri Çerçeveleri */
    .stTable { border: 1px solid #E0E0E0; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- AYARLAR VE FORMATLAR ---
F_TARIH = '%d/%m/%Y'
F_SAAT = '%H:%M'
F_TAM = '%d/%m/%Y %H:%M'
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
    st.markdown('<p class="main-title">🏢 DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    ad = c1.text_input("Ad Soyad")
    tc = c2.text_input("TC Kimlik No", max_chars=11)
    tp = st.radio("İzin Süresi", TP_LIST, horizontal=True)
    
    with st.expander("📝 İzin Formunu Doldur", expanded=True):
        with st.form("p"):
            t1 = st.selectbox("İzin Türü", IZ)
            t2 = st.date_input("Başlangıç Tarihi")
            fmt = t2.strftime(F_TARIH)
            if tp == "Saatlik":
                s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                b, d = f"{fmt} {s1.strftime(F_SAAT)}", f"{fmt} {s2.strftime(F_SAAT)}"
            else:
                dn = st.date_input("İş Başı Tarihi")
                b, d = fmt, dn.strftime(F_TARIH)
            
            if st.form_submit_button("TALEBİ GÖNDER") and ad:
                now = datetime.now().strftime(F_TARIH)
                pay = {"tarih":now,"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}
                requests.post(URL, data=json.dumps(pay))
                st.balloons()
                st.success("Talebiniz başarıyla yönetime iletildi!")

else:
    st.markdown('<p class="main-title">🔐 YÖNETİCİ KONTROL PANELİ</p>', unsafe_allow_html=True)
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "1234":
        df = yukle()
        if not df.empty:
            t = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin"])
            with t[0]:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ays:
                    ay = st.selectbox("Dönem Seçiniz", ays)
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum()
                    st.dataframe(kn.style.format("{:.1f}"), use_container_width=True)
            with t[1]:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)
            with t[2]:
                with st.form("m"):
                    m_ad = st.text_input("Personel İsmi")
                    m_tp = st.radio("Tip", TP_LIST, horizontal=True)
                    tr, ta = st.selectbox("Tür", IZ), st.date_input("Başlangıç")
                    t_f = ta.strftime(F_TARIH)
                    if m_tp == "Saatlik":
                        ms1, ms2 = st.time_input("Ç1"), st.time_input("Ç2")
                        mb, md = f"{t_f} {ms1.strftime(F_SAAT)}", f"{t_f} {ms2.strftime(F_SAAT)}"
                    else:
                        m_dn = st.date_input("Dönüş")
                        mb, md = t_f, m_dn.strftime(F_TARIH)
                    if st.form_submit_button("KAYDI TAMAMLA") and m_ad:
                        now = datetime.now().strftime(F_TARIH)
                        p_m = {"tarih":now,"tc":"0","ad":m_ad,"brans":"Y","tur":f"{tr} ({m_tp})","bas":mb,"bit":md}
                        requests.post(URL, data=json.dumps(p_m))
                        st.success("Kayıt Eklendi!"); st.rerun()
            with t[3]:
                py = st.selectbox("Personel Seç", sorted(df['Ad Soyad'].unique()), key="py")
                gt = st.date_input("İşe Giriş", value=datetime(2023, 1, 1))
                kd = (2026 - gt.year)
                hk = hakedis_bul(kd)
                df_yil = df[(df['Ad Soyad']==py) & (df['Tür'].str.contains("Yıllık", na=False))]
                ku = df_yil['G'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Toplam Hak", f"{hk} Gün")
                c2.metric("Kullanılan", f"{ku:.1f} Gün", delta=f"-{ku}", delta_color="inverse")
                c3.metric("Kalan İzin", f"{hk-ku:.1f} Gün", delta=f"{hk-ku}")
                if not df_yil.empty: st.dataframe(df_yil[['Başlangıç', 'Dönüş', 'G']], use_container_width=True)
        else: st.warning("Henüz veri yok.")
    else: st.info("Lütfen sol menüden şifre giriniz.")

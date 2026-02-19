import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- LOGO VE AYARLAR ---
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"
st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- TASARIM (CSS) ---
st.markdown(f"""
    <style>
    [data-testid="stSidebarNav"] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }}
    .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; margin-bottom: 5px; }}
    div.stButton > button:first-child {{ background-color: #CC0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; }}
    [data-testid="stMetricValue"] {{ color: #CC0000; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# --- AYARLAR ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
# Google Apps Script Web App URL'nizi buraya tekrar kontrol ederek yapıştırın
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
                b_str, d_str = str(r['Başlangıç']), str(r['Dönüş'])
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
        return df
    except: return pd.DataFrame()

# --- MENÜ ---
m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if m == "👤 PERSONEL GİRİŞİ":
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad"); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi Tipi", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.expander("📝 İzin Başvuru Formu", expanded=True):
        with st.form("p_f"):
            t1 = st.selectbox("İzin Türü", IZ); t2 = st.date_input("İzin Günü")
            if tp == "Saatlik":
                s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
            else:
                dn = st.date_input("İş Başı Tarihi")
                b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
            if st.form_submit_button("BAŞVURUYU GÖNDER") and ad:
                requests.post(URL, data=json.dumps({"method":"post","tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
                st.balloons(); st.success("Talebiniz iletildi!")

else:
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    if sifre == "1234":
        df = yukle()
        if not df.empty:
            t = st.tabs(["📊 Karne", "👤 Personel Sicil", "📝 Manuel Giriş", "📅 Yıllık İzin", "🗑️ Veri Listesi ve Silme"])
            
            with t[0]:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ays:
                    ay = st.selectbox("Dönem Seçiniz", ays)
                    st.dataframe(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum(), use_container_width=True)
            
            with t[1]:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)
            
            with t[2]:
                with st.form("m_f"):
                    m_ad = st.text_input("İsim Soyad")
                    m_tp = st.selectbox("İzin Tipi", ["Tam Gün", "Saatlik"])
                    m_tr = st.selectbox("Tür", IZ)
                    m_tarih = st.date_input("Tarih")
                    
                    # Saatlik seçilirse saat kutuları formun içinde görünür
                    c_saat1, c_saat2 = st.columns(2)
                    ms1 = c_saat1.time_input("Çıkış Saati (Sadece Saatlik için)")
                    ms2 = c_saat2.time_input("Dönüş Saati (Sadece Saatlik için)")
                    
                    m_db = st.date_input("İş Başı Tarihi (Sadece Tam Gün için)")
                    
                    if st.form_submit_button("KAYDI EKLE"):
                        if m_tp == "Saatlik":
                            mb, md = f"{m_tarih.strftime(F_TARIH)} {ms1.strftime(F_SAAT)}", f"{m_tarih.strftime(F_TARIH)} {ms2.strftime(F_SAAT)}"
                        else:
                            mb, md = m_tarih.strftime(F_TARIH), m_db.strftime(F_TARIH)
                        requests.post(URL, data=json.dumps({"method":"post","tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} ({m_tp})","bas":mb,"bit":md}))
                        st.success("Kayıt eklendi!"); st.rerun()

            with t[3]:
                py = st.selectbox("Personel Seç", sorted(df['Ad Soyad'].unique()), key="py")
                gt = st.date_input("İşe Giriş", value=datetime(2024,1,1))
                kd = (datetime.now().year - gt.year); hk = hakedis_bul(kd)
                ku = df[(df['Ad Soyad']==py) & (df['Tür'].str.contains("Yıllık"))]['G'].sum()
                st.metric("Kalan İzin", f"{hk-ku} Gün")

            with t[4]:
                st.info("💡 Silmek istediğiniz satırın solundaki index numarasını kullanın.")
                st.dataframe(df[['Ad Soyad','Tür','Başlangıç','Dönüş']].tail(20), use_container_width=True)
                
                with st.form("delete_form"):
                    row_to_delete = st.number_input("Silinecek Satır No (Index)", min_value=0, step=1)
                    if st.form_submit_button("KAYDI KALICI OLARAK SİL"):
                        # Google Script'e silme isteği gönderir (Scriptinizde delete metodu tanımlı olmalıdır)
                        # Şimdilik en güvenli yol tabloyu görüp Google Sheets'ten silmektir.
                        st.error("Silme işlemi için Google Sheets dosyasını açıp ilgili satırı silmeniz güvenlik gereği daha sağlıklıdır.")

    else: st.warning("Panele erişmek için şifre giriniz.")

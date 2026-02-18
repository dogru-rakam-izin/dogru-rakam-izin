import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Dogru Rakam", layout="wide")

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin"]

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                f = "%d/%m/%Y"
                if "Saatlik" in str(r['Tür']): f = "%d/%m/%Y %H:%M"
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): 
                    return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("MENU", ["PERSONEL", "YONETICI"])

if m == "PERSONEL":
    st.title("DOĞRU RAKAM İZİN SİSTEMİ")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No")
    with st.form("p_form"):
        t1 = st.selectbox("İzin Türü", IZ)
        t2 = st.date_input("Başlangıç Tarihi")
        if st.form_submit_button("GÖNDER") and ad:
            dt = datetime.now().strftime("%d/%m/%Y")
            b_s = t2.strftime('%d/%m/%Y')
            d = {"tarih":dt,"tc":tc,"ad":ad,"brans":"P","tur":t1,"bas":b_s,"bit":b_s}
            requests.post(URL, data=json.dumps(d))
            st.success("Talebiniz Gönderildi")

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "1234":
        df = yukle()
        t = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel Kayıt", "📅 Yıllık İzin Takip"])
        
        with t[0]:
            if not df.empty:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                ay = st.selectbox("Ay Seç", ays)
                st.table(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum())
        
        with t[1]:
            if not df.empty:
                ps = sorted(df['Ad Soyad'].unique())
                p = st.selectbox("Personel Seç", ps)
                st.dataframe(df[df['Ad Soyad']==p])

        with t[2]:
            ma = st.text_input("Personel İsmi")
            with st.form("m_f"):
                m_t = st.selectbox("Tür ", IZ)
                m_b = st.date_input("Başlangıç ")
                if st.form_submit_button("SİSTEME KAYDET") and ma:
                    st.success("Kaydedildi")

        with t[4 if len(t)>4 else 3]:
            st.subheader("Yıllık İzin Hak ediş Hesaplama")
            if not df.empty:
                plist = sorted(df['Ad Soyad'].unique())
                py = st.selectbox("Personel Seç", plist, key="y_p")
                gr = st.date_input("İşe Giriş Tarihi")
                kd = (datetime.now().year - gr.year)
                hk = 14 if kd < 5 else 20 if kd < 15 else 26
                mask = (df['Ad Soyad'] == py) & (df['Tür'].str.contains("Yıllık"))
                ku = df[mask]['G'].sum()
                st

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- FORM METINLERI ---
F1 = "1. KIMLIK: ___\n2. TUR: [ ] Yillik [ ] Mazeret\n3. IMZA: ___"
F2 = "Mudurluge,\n\nUcretsiz izin istiyorum.\n\nImza: ___"
F3 = "Mudurluge,\n\nYillik izin istiyorum.\n\nImza: ___"

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Dogru Rakam", layout="wide")

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Eğitim"]

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

def yazdir(bas, ic):
    ht = f"<html><body onload='window.print()'><h3>{bas}</h3><pre>{ic}</pre></body></html>"
    st.components.v1.html(ht, height=0)

m = st.sidebar.radio("MENU", ["PERSONEL", "YONETICI"])

if m == "PERSONEL":
    st.title("DOĞRU RAKAM İZİN")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No")
    with st.form("p"):
        t1 = st.selectbox("Tür", IZ)
        t2 = st.date_input("Tarih")
        if st.form_submit_button("GONDER") and ad:
            d = {"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":t1,"bas":t2.strftime('%d/%m/%Y'),"bit":t2.strftime('%d/%m/%Y')}
            requests.post(URL, data=json.dumps(d))
            st.success("Gonderildi")

else:
    st.title("YONETICI PANELI")
    if st.sidebar.text_input("Sifre", type="password") == "1234":
        df = yukle()
        tabs = st.tabs(["Karne", "Sicil", "Manuel", "Formlar", "Yillik Izin"])
        
        with tabs[0]:
            if not df.empty:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                ay = st.selectbox("Ay Sec", ays)
                st.table(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum())
        
        with tabs[1]:
            if not df.empty:
                ps = sorted(df['Ad Soyad'].unique())
                p = st.selectbox("Kisi", ps)
                st.dataframe(df[df['Ad Soyad']==p])

        with tabs[2]:
            ma = st.text_input("Isim")
            if st.button("KAYDET") and ma: st.success("Ok")

        with tabs[3]:
            c1, c2, c3 = st.columns(3)
            if c1.button("IZIN FORMU"): yazdir("IZIN FORMU", F1)
            if c2.button("UCRETSIZ"): yazdir("UCRETSIZ IZIN", F2)
            if c3.button("YILLIK"): yazdir("YILLIK IZIN", F3)

        with tabs[4]:
            if not df.empty:
                plist = sorted(
                    df['Ad Soyad'].unique()
                )
                py = st.selectbox("Personel Sec", plist)
                gr = st.date_input("Giris")
                kd = (datetime.now().year - gr.year)
                hk = 14 if kd < 5 else 20 if kd < 15 else 26
                ku = df[(

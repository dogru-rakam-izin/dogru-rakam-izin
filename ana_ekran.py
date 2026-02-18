import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- FORM METINLERI ---
F1 = "1. KIMLIK: ___\n2. TUR: [ ] Yillik [ ] Mazeret\n3. IMZA: ___"
F2 = "Mudurluge,\nUcretsiz izin istiyorum.\nImza: ___"
F3 = "Mudurluge,\nYillik izin istiyorum.\nImza: ___"

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
            dt = datetime.now().strftime("%d/%m/%Y")
            b_s = t2.strftime('%d/%m/%Y')
            d = {"tarih":dt,"tc":tc,"ad":ad,"brans":"P","tur":t1,"bas":b_s,"bit":b_s}
            requests.post(URL, data=json.dumps(d))
            st.success("Gonderildi")
else:

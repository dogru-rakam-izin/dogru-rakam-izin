import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Doğru Rakam İzin", layout="wide")

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                ts = str(r['Tür'])
                f = "%d/%m/%Y %H:%M" if "Saatlik" in ts else "%d/%m/%Y"
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

m = st.sidebar.radio("MENÜ", ["PERSONEL", "YONETICI"])

if m == "PERSONEL":
    st.title("DOĞRU RAKAM İZİN")
    ad, tc = st.text_input("Ad Soyad"), st.text_input("TC No")
    tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("Tür", IZ), st.date_input("Tarih")
        fmt = t2.strftime('%d/%m/%Y')
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{fmt} {s1.strftime('%H:%M')}", f"{fmt} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("İş Başı")
            b, d = fmt, dn.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER") and ad:
            now = datetime.now().strftime("%d/%m/%Y")
            pay = {"tarih":now,"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}
            requests.post(URL, data=json.dumps(pay))
            st.success("İletildi!")

else:
    st.title("YÖNETİCİ PANELİ")
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        if not df.empty:
            t = st.tabs(["Karne", "Sicil", "Manuel", "Yıllık İzin"])
            with t[0]:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ays:
                    ay = st.selectbox("Ay Seç", ays)
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum()
                    st.table(kn.style.format("{:.1f}"))
            with t[1]:
                p = st.selectbox("Kişi", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])
            with t[2]:
                m_ad = st.text_input("İsim")
                m_tp = st.radio("Tip", ["Tam Gün", "Saatlik

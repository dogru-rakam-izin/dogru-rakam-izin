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
                tur_str = str(r['Tür'])
                f = "%d/%m/%Y %H:%M" if "Saatlik" in tur_str else "%d/%m/%Y"
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in tur_str:
                    return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0], res[1]
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

menu = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if menu == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No", max_chars=11)
    tp = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("Tür", IZ), st.date_input("Tarih")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t2.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{t2.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("İş Başı")
            b, d = t2.strftime('%d/%m/%Y'), dn.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER") and ad:
            payload = {"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}
            requests.post(URL, data=json.dumps(payload))
            st.success("İletildi!")

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        if df.empty:
            st.warning("Veri bulunamadı.")
        else:
            tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin"])
            with tabs[0]:
                aylar = sorted(df['Ay'].dropna().unique(), reverse=True)
                if aylar:
                    ay = st.selectbox("Ay", aylar)
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                    st.table(kn)
            with tabs[1]:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])
            with tabs[2]:
                ma = st.text_input("İsim")
                mtp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
                with st.form("m"):
                    tr, ta = st.selectbox("Tür ", IZ), st.date_input("Tarih ")
                    if mtp == "Saatlik":
                        ms1, ms2 = st.time_input("Çıkış "), st.time_input("Dönüş ")
                        mb, md = f"{ta.strftime('%d/%m/%Y')} {ms

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Izin", layout="wide")

TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret", "Sağlık", "Saatlik", "Ücretsiz", "Evlilik", "Vefat", "Babalık", "Eğitim"]

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b, d = datetime.strptime(str(r['Başlangıç']), f), datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): return 0, round((d-b).seconds/3600,1)
                return (d-b).days, 0
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['Ay'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True).dt.strftime('%B').map(TR)
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 İZİN TALEBİ")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC", max_chars=11)
    tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1 = st.selectbox("Tür", IZ)
        t2 = st.date_input("Tarih")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t2.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{t2.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("Dönüş")
            b, d = t2.strftime('%d/%m/%Y'), dn.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER") and ad:
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
            st.success("İletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ")
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "1234":
        df = yukle()
        tab1, tab2, tab3 = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel"])
        with tab1:
            if not df.empty:
                ay = st.selectbox("Ay", sorted(df['Ay'].dropna().unique()))
                kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                st.table(kn)
        with tab2:
            if not df.empty:
                kisi = st.selectbox("Kişi", sorted(df['Ad Soyad'].unique()))
                f = df[df['Ad Soyad']==kisi]
                st.metric("Toplam Gün", int(f['G'].sum()))
                st.dataframe(f[['Başlangıç','Dönüş','Tür','G','S']])
        with tab3:
            mad = st.text_input("İsim")
            mtp = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"])
            with st.form("m"):
                mtr = st.selectbox("İzin Nedeni", IZ)
                mta = st.date_input("İzin Tarihi")
                if mtp == "Saatlik":
                    m1, m2 = st.time_input("Başla"), st.time_input("Bitir")
                    mb, mi = f"{mta.strftime('%d/%m/%Y')} {m1.strftime('%H:%M')}", f"{mta.strftime('%d/%m/%Y')} {m2.strftime('%H:%M')}"
                else:
                    mdn = st.date_input("İş Başı")
                    mb, mi = mta.strftime('%d/%m/%Y'), mdn.strftime('%d/%m/%Y')
                if st.form_submit_button("KAYDET") and mad:
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":mad,"brans":"Y","tur":f"{mtr} ({mtp})","bas":mb,"bit":mi}))
                    st.success("Eklendi!"); st.rerun()

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
        if df.empty or "Ad Soyad" not in df.columns: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def h(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b, d = datetime.strptime(str(r['Başlangıç']), f), datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): return 0, round((d-b).seconds/3600,1)
                return (d-b).days, 0
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 İZİN TALEBİ")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC", max_chars=11)
    tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("Tür", IZ), st.date_input("Tarih")
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
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        if not df.empty:
            tab1, tab2, tab3 = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel"])
            with tab1:
                ay_sec = st.selectbox("Ay Seçin", sorted(df['Ay'].dropna().unique(), reverse=True))
                kn = df[df['Ay']==ay_sec].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                st.write(f"### {ay_sec} Özeti")
                st.table(kn)
            with tab2:
                kisi = st.selectbox("Personel Seç", sorted(df['Ad Soyad'].unique()))
                f = df[df['Ad Soyad']==kisi]
                st.metric("Toplam Gün İzni", int(f['G'].sum()))
                st.dataframe(f[['Başlangıç','Dönüş','Tür','G','S']])
            with tab3:
                mad = st.text_input("İsim")
                mtp = st.radio("İp", ["Tam Gün", "Saatlik"])
                with st.form("m"):
                    mtr, mta = st.selectbox("İzin Nedeni", IZ), st.date_input("İzin Tarihi")
                    if mtp == "Saatlik":
                        m1, m2 = st.time_input("B-Saat"), st.time_input("D-Saat")
                        mb, mi = f"{mta.strftime('%d/%m/%Y')} {m1.strftime('%H:%M')}", f"{mta.strftime('%d/%m/%Y')} {m2.strftime('%H:%M')}"
                    else:
                        mdn = st.date_input("İş Başı")
                        mb, mi = mta.strftime('%d/%m/%Y'), mdn.strftime('%d/%m/%Y')
                    if st.form_submit_button("KAYDET") and mad:
                        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":mad,"brans":"Y","tur":f"{mtr} ({mtp})","bas":mb,"bit":mi}))
                        st.success("Eklendi!"); st.rerun()
        else:
            st.warning("Veritaban

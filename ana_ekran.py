import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- YAPILANDIRMA ---
URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="İzin Sistemi", layout="wide")

TR_A = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZINLER = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim"]

def verileri_yukle():
    try:
        df = pd.read_csv(CSV_URL)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def hesapla(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b, d = datetime.strptime(str(r['Başlangıç']), f), datetime.strptime(str(r['Dönüş']), f)
                return (0, float(round((d-b).seconds/3600,1))) if "Saatlik" in str(r['Tür']) else (int((d-b).days), 0)
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(hesapla(r)), axis=1)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR_A) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad, tc = st.text_input("Ad Soyad"), st.text_input("TC", max_chars=11)
    tp = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p_f"):
        c1, c2 = st.columns(2)
        tur, tar = c1.selectbox("Tür", IZINLER), c1.date_input("Tarih")
        if tp == "Saatlik":
            s1, s2 = c2.time_input("Çıkış"), c2.time_input("Dönüş")
            b_s, d_s = f"{tar.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{tar.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = c2.date_input("Dönüş")
            b_s, d_s = tar.strftime('%d/%m/%Y'), dn.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER"):
            if ad and tc:
                dt = {"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":str(tc),"ad":ad,"brans":"P","tur":f"{tur} ({tp})","bas":b_s,"bit":d_s}
                requests.post(URL, data=json.dumps(dt))
                st.success("İletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    ps = st.sidebar.text_input("Şifre", type="password")
    if ps == "1234":
        df = verileri_yukle()
        t1, t2, t3 = st.tabs(["📊 Aylık Karne", "👤 Personel Sicili", "📝 Manuel Kayıt"])
        with t1:
            if not df.empty:
                al = sorted(df['Ay'].dropna().unique(), reverse=True)
                sa = st.selectbox("Ay Seç", al)
                adf = df[df['Ay'] == sa].copy()
                kn = adf.groupby(['Ad Soyad', 'Tür']).agg({'G':'sum', 'S':'sum'}).reset_index()
                st.table(kn)
                st.download_button("📥 İndir", kn.to_csv(index=False).encode('utf-8-sig'), f"{sa}.csv")
            else: st.info("Veri yok.")
        with t2:
            if not df.empty:
                sl = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                pg = df[df['Ad Soyad'] == sl].copy()
                st.metric("Toplam Gün", int(pg['G'].sum()))
                st.dataframe(pg[['Başlangıç', 'Dönüş', 'Tür', 'G', 'S']])
            else: st.info("Veri yok.")
        with t3:
            ma = st.text_input("Personel İsmi")
            mt = st.radio("Tip", ["Tam Gün", "Saatlik"], key="mt")
            with st.form("m_f"):
                mtu, mta = st.selectbox("Tür", IZINLER), st.date_input("Tarih")
                if mt == "Saatlik":
                    m1, m2 = st.time_input("Başla"), st.time_input("Bitir")
                    mb, mi = f"{mta.strftime('%d/%m/%Y')} {m1.strftime('%H:%M')}", f"{mta.strftime('%d/%m/%Y')} {m2.strftime('%H:%M')}"
                else:
                    md = st.date_input("D

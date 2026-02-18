import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- FORM METİNLERİ (Hata almamak için kısa satırlar halinde) ---
F1_METIN = "1. KIMLIK: ________\n2. IZIN: [ ] Yillik [ ] Mazeret\n3. TARIH: ..../..../2026\n4. IMZA: ________"
F2_METIN = "Dogru Rakam Mudurlugu’ne\n\nUcretsiz izin istiyorum.\n\nIsim/Imza: ____________"
F3_METIN = "Dogru Rakam Mudurlugu’ne\n\nYillik izin hakkimi kullanmak istiyorum.\n\nImza: ____________"

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
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
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

def yazdir_html(bas, ic):
    ht = f"<html><body onload='window.print()'><h3>{bas}</h3><pre>{ic}</pre></body></html>"
    st.components.v1.html(ht, height=0)

menu = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if menu == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC", max_chars=11)
    with st.form("p"):
        t1 = st.selectbox("Tür", IZ)
        t2 = st.date_input("Başla")
        if st.form_submit_button("GÖNDER") and ad:
            d = {"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":t1,"bas":t2.strftime('%d/%m/%Y'),"bit":t2.strftime('%d/%m/%Y')}
            requests.post(URL, data=json.dumps(d))
            st.success("İletildi!")

else:
    st.title("🔐 YÖNETİCİ")
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Karne", "Sicil", "Manuel", "Formlar", "Yıllık İzin"])
        
        with tab1:
            if not df.empty:
                ay = st.selectbox("Ay", sorted(df['Ay'].dropna().unique(), reverse=True))
                st.table(df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum())
        
        with tab2:
            if not df.empty:
                p = st.selectbox("Seç", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p])

        with tab3:
            m_ad = st.text_input("İsim")
            with st.form("m"):
                if st.form_submit_button("EKLE") and m_ad:
                    st.success("Kaydedildi")

        with tab4:
            c1, c2, c3 = st.columns(3)
            if c1.button("📄 İZİN FORMU"): yazdir_html("İZİN FORMU", F1_METIN)
            if c2.button("📄 ÜCRETSİZ"): yazdir_html("ÜCRETSİZ İZİN", F2_METIN)
            if c3.button("📄 YILLIK"): yazdir_html("YILLIK İZİN", F3_METIN)

        with tab5:
            if not df.empty:
                p_y = st.selectbox("Personel", sorted(df['Ad

import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- YAPILANDIRMA ---
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
                b, d = datetime.strptime(str(r['Başlangıç']), f), datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No", max_chars=11)
    tp = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("Tür", IZ), st.date_input("Başlangıç")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t2.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{t2.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("İş Başı")
            b, d = t2.strftime('%d/%m/%Y'), dn.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER") and ad:
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
            st.success("İletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        # Formlar sekmesi kaldırıldı, sadece 4 sekme kaldı
        tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin Takip"])
        
        with tabs[0]: # Karne
            if not df.empty:
                ay = st.selectbox("Ay", sorted(df['Ay'].dropna().unique(), reverse=True))
                kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                st.table(kn.style.format({"G": "{:.1f}", "S": "{:.1f}"}))

        with tabs[1]: # Sicil
            if not df.empty:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])

        with tabs[2]: # Manuel Kayıt
            ma = st.text_input("İsim")
            with st.form("m"):
                tr, ta, dn = st.selectbox("Tür ", IZ), st.date_input("Başla "), st.date_input("Dönüş ")
                if st.form_submit_button("SİSTEME İŞLE") and ma:
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":ma,"brans":"Y","tur":tr,"bas":ta.strftime('%d/%m/%Y'),"bit":dn.strftime('%d/%m/%Y')}))
                    st.success("Eklendi!"); st.rerun()

        with tabs[3]: # Yıllık İzin Takip
            st.subheader("Yıllık İzin Hak ediş Hesaplama")
            if not df.empty:
                personel_listesi = sorted(df['Ad Soyad'].unique())
                secilen_p = st.selectbox("Personel Seçiniz", personel_listesi)
                giris_tarihi = st.date_input("İşe Giriş Tarihi", value=datetime(2023, 1, 1))
                
                bugun = datetime.now()
                kidem = (bugun.year - giris_tarihi.year) - ((bugun.month, bugun.day) < (giris_tarihi.month, giris_tarihi.day))
                
                if kidem < 1: hak = 0
                elif 1 <= kidem < 5: hak = 14
                elif 5 <= kidem < 15: hak = 20
                else: hak = 26
                
                kullanilan = df[(df['Ad Soyad'] == secilen_p) & (df['Tür'].str.contains("Yıllık"))]['G'].sum()
                kalan = hak - kullanilan
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Çalışma Yılı", f"{kidem} Yıl")
                c2.metric("Toplam Hak", f"{hak} Gün")
                c3.metric("Kullanılan", f"{kullanilan:.1f} Gün")
                c4.metric("Kalan İzin", f"{kalan:.1f} Gün")
                
                st.info(f"💡 Not: 1-5 yıl arası 14 gün, 5-15 yıl arası 20 gün, 15+ yıl 26 gün izin hak edilir.")

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
        # Veriyi çek ve sütun başlıklarındaki boşlukları temizle
        df = pd.read_csv(CSV)
        if df.empty: 
            return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        
        # Hesaplama fonksiyonu
        def h(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b = datetime.strptime(str(r['Başlangıç']), f)
                d = datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): 
                    return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: 
                return 0, 0

        # Yeni sütunları ekle
        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0], res[1]
        
        # Tarih ve Ay işlemleri
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except Exception as e:
        st.sidebar.error(f"Veri yükleme hatası: {e}")
        return pd.DataFrame()

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
        
        if df.empty:
            st.warning("⚠️ Google Sheets'ten veri alınamadı. Lütfen tablonuzun boş olmadığından ve paylaşıma açık olduğundan emin olun.")
        else:
            tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📅 Yıllık İzin Takip"])
            
            with tabs[0]: # Karne
                ay_listesi = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ay_listesi:
                    ay = st.selectbox("Ay Seçin", ay_listesi)
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                    st.table(kn.style.format({"G": "{:.1f}", "S": "{:.1f}"}))
                else:
                    st.info("Bu ay için henüz kayıtlı veri yok.")

            with tabs[1]: # Sicil
                ps = sorted(df['Ad Soyad'].unique())
                p = st.selectbox("Personel Listesi", ps)
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])

            with tabs[2]: # Manuel Kayıt
                ma = st.text_input("İsim")
                mtp = st.radio("İzin Tipi", ["Tam Gün", "Saatlik"], horizontal=True)
                with st.form("m"):
                    tr, ta = st.selectbox("Tür ", IZ), st.date_input("Tarih ")
                    if mtp == "Saatlik":
                        ms1, ms2 = st.time_input("Çıkış "), st.time_input("Dönüş ")
                        mb, md = f"{ta.strftime('%d/%m/%Y')} {ms1.strftime('%H:%M')}", f"{ta.strftime('%d/%m/%Y')} {ms2.strftime('%H:%M')}"
                    else:
                        tdn = st.date_input("İş Başı ")
                        mb, md = ta.strftime('%d/%m/%Y'), tdn.strftime('%d/%m/%Y')
                    if st.form_submit_button("SİSTEME İŞLE") and ma:
                        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":ma,"brans":"Y","tur":f"{tr} ({mtp})","bas":mb,"bit":md}))
                        st.success("Eklendi!"); st.rerun()

            with tabs[3]: # Yıllık İzin Takip
                st.subheader("Yıllık İzin Hak ediş")
                personel_listesi = sorted(df['Ad Soyad'].unique())
                secilen_p = st.selectbox("Personel", personel_listesi, key="y_p")
                giris_tarihi = st.date_input("İşe Giriş", value=datetime(2023, 1, 1))
                bugun = datetime.now()
                kidem = (bugun.year -

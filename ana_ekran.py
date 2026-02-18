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
IZ = ["Yıllık", "Mazeret", "Sağlık", "Saatlik", "Ücretsiz", "Evlilik", "Vefat", "Babalık", "Eğitim"]

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        
        def h(r):
            try:
                f = "%d/%m/%Y %H:%M" if "Saatlik" in str(r['Tür']) else "%d/%m/%Y"
                b, d = datetime.strptime(str(r['Başlangıç']), f), datetime.strptime(str(r['Dönüş']), f)
                if "Saatlik" in str(r['Tür']): 
                    return 0, round((d-b).total_seconds()/3600, 1)
                return (d-b).days, 0
            except: return 0, 0
            
        df[['G', 'S']] = df.apply(lambda r: pd.Series(h(r)), axis=1)
        # Ondalıkları temizle (2.0000 yerine 2 yap)
        df['G'] = df['G'].astype(float)
        df['S'] = df['S'].astype(float)
        
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except Exception as e:
        st.error(f"Hata: {e}")
        return pd.DataFrame()

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 İZİN TALEBİ")
    ad, tc = st.text_input("Ad Soyad"), st.text_input("TC", max_chars=11)
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
                ay_l = df['Ay'].dropna().unique()
                if len(ay_l) > 0:
                    ay = st.selectbox("Ay Seç", sorted(ay_l, reverse=True))
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                    # Rakamları güzelleştir
                    kn.columns = ['Ad Soyad', 'Tür', 'Gün', 'Saat']
                    st.table(kn.style.format({"Gün": "{:.1f}", "Saat": "{:.1f}"}))
                else: st.info("Veri yok.")
            with tab2:
                p = st.selectbox("Kişi", sorted(df['Ad Soyad'].unique()))
                f = df[df['Ad Soyad']==p]
                st.metric("Toplam Gün", f"{f['G'].sum():.1f}")
                st.dataframe(f[['Başlangıç','Dönüş','Tür','G','S']].style.format({"G": "{:.1f}", "S": "{:.1f}"}))
            with tab3:
                ma, mt = st.text_input("İsim"), st.radio("Tip", ["Tam Gün", "Saatlik"])
                with st.form("m"):
                    tr, ta = st.selectbox("Tür", IZ), st.date_input("Tarih")
                    if mt == "Saatlik":
                        m1, m2 = st.time_input("B-Saat"), st.time_input("D-Saat")
                        mb, mi = f"{ta.strftime('%d/%m/%Y')} {m1.strftime('%H:%M')}", f"{ta.strftime('%d/%m/%Y')} {m2.strftime('%H:%M')}"
                    else:
                        md = st.date_input("Dönüş")
                        mb, mi = ta.strftime('%d/%m/%Y'), md.strftime('%d/%m/%Y')
                    if st.form_submit_button("KAYDET") and ma:
                        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":ma,"brans":"Y","tur":f"{tr} ({mt})","bas":mb,"bit":mi}))
                        st.success("Eklendi!"); st.rerun()
        else: st.warning("Veritabanı boş veya sütunlar hatalı.")

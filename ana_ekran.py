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
TABS = ["Karne", "Sicil", "Manuel", "Yıllık İzin Takibi"]

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
        df['G'], df['S'] = res[0], res[1]
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

menu = st.sidebar.radio("MENÜ", ["PERSONEL", "YONETICI"])

if menu == "PERSONEL":
    st.title("DOĞRU RAKAM İZİN")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No")
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
            st.success("Gönderildi!")

else:
    st.title("YÖNETİCİ PANELİ")
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        if df.empty:
            st.warning("Veri yok.")
        else:
            tabs = st.tabs(TABS)
            with tabs[0]:
                ays = sorted(df['Ay'].dropna().unique(), reverse=True)
                if ays:
                    ay = st.selectbox("Ay Seç", ays)
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum()
                    st.table(kn)
            with tabs[1]:
                ps = sorted(df['Ad Soyad'].unique())
                p = st.selectbox("Kişi Seç", ps)
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])
            with tabs[2]:
                m_ad = st.text_input("İsim")
                m_tp = st.radio("Tip", ["Tam Gün", "Saatlik"], key="mt")
                with st.form("m"):
                    tr, ta = st.selectbox("Tür", IZ), st.date_input("Tarih")
                    t_f = ta.strftime('%d/%m/%Y')
                    if m_tp == "Saatlik":
                        ms1, ms2 = st.time_input("C1"), st.time_input("C2")
                        mb, md = f"{t_f} {ms1.strftime('%H:%M')}", f"{t_f} {ms2.strftime('%H:%M')}"
                    else:
                        m_don = st.date_input("Dönüş")
                        mb, md = t_f, m_don.strftime('%d/%m/%Y')
                    if st.form_submit_button("KAYDET") and m_ad:
                        now = datetime.now().strftime("%d/%m/%Y")
                        p_m = {"tarih":now,"tc":"0","ad":m_ad,"brans":"Y","tur":f"{tr} ({m_tp})","bas":mb,"bit":md}
                        requests.post(URL, data=json.dumps(p_m))
                        st.success("Kaydedildi!"); st.rerun()
            with tabs[3]:
                st.subheader("Yıllık İzin Detaylı Takip")
                py = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()), key="py")
                gt = st.date_input("İşe Giriş", value=datetime(2023, 1, 1))
                # --- GÜNCEL YIL: 2026 ---
                kd = (2026 - gt.year)
                hk = 14 if kd < 5 else 20 if kd < 15 else 26
                if kd < 1: hk = 0
                
                yil_filtre = (df['Ad Soyad'] == py) & (df['Tür'].str.contains("Yıllık İzin", na=False))
                df_yil = df[yil_filtre].copy()
                ku = df_yil['G'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Toplam Hak", f"{hk} Gün")
                c2.metric("Kullanılan", f"{ku:.1f} Gün")
                c3.metric("Kalan", f"{hk-ku:.1f} Gün")
                
                if not df_yil.empty:
                    st.write("Kullanılan İzinlerin Listesi:")
                    st.dataframe(df_yil[['Başlangıç', 'Dönüş', '

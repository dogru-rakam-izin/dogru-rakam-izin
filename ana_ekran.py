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

def yazdir_html(bas, ic):
    ht = f"<html><head><style>body{{font-family:'Times New Roman';padding:40px;line-height:1.6;}} .h{{text-align:center;font-weight:bold;margin-bottom:20px;border-bottom:2px solid #000;}} .c{{white-space:pre-wrap;}}</style></head><body onload='window.print()'><div class='h'>{bas}</div><div class='c'>{ic}</div></body></html>"
    st.components.v1.html(ht, height=0)

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No", max_chars=11)
    tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("Tür", IZ), st.date_input("Başla")
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
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "1234":
        df = yukle()
        tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📄 Formlar", "📅 Yıllık İzin Takip"])
        
        with tabs[0]: # KARNE
            if not df.empty:
                ay_secenek = df['Ay'].dropna().unique()
                if len(ay_secenek) > 0:
                    ay = st.selectbox("Ay", sorted(ay_secenek, reverse=True))
                    kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                    st.table(kn.style.format({"G": "{:.1f}", "S": "{:.1f}"}))
                else: st.warning("İşlenecek ay verisi bulunamadı.")
            else: st.warning("Google Sheets verisi alınamadı veya dosya boş.")

        with tabs[1]: # SİCİL
            if not df.empty:
                p_list = sorted(df['Ad Soyad'].unique())
                p = st.selectbox("Personel Seç", p_list)
                st.dataframe(df[df['Ad Soyad']==p][['Başlangıç','Dönüş','Tür','G','S']])

        with tabs[2]: # MANUEL
            ma = st.text_input("Personel İsmi")
            with st.form("m_form"):
                tr, ta, dn = st.selectbox("İzin Türü", IZ), st.date_input("Başla Tarihi"), st.date_input("Dönüş Tarihi")
                if st.form_submit_button("KAYDET") and ma:
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":ma,"brans":"Y","tur":tr,"bas":ta.strftime('%d/%m/%Y'),"bit":dn.strftime('%d/%m/%Y')}))
                    st.success("Eklendi!"); st.rerun()

        with tabs[3]: # FORMLAR
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📄 PERSONEL İZİN"):
                    yazdir_html

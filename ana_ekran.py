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
    ht = f"""<html><head><style>
    body{{font-family:'Times New Roman';padding:40px;line-height:1.6;}}
    .h{{text-align:center;font-weight:bold;margin-bottom:20px;border-bottom:2px solid #000;}}
    .c{{white-space:pre-wrap;text-align:justify;}}
    </style></head><body onload='window.print()'>
    <div class='h'>{bas}</div><div class='c'>{ic}</div>
    </body></html>"""
    st.components.v1.html(ht, height=0)

menu = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if menu == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad = st.text_input("Ad Soyad")
    tc = st.text_input("TC No", max_chars=11)
    tp = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1 = st.selectbox("Tür", IZ)
        t2 = st.date_input("Başla")
        if tp == "Saatlik":
            s1 = st.time_input("Çıkış")
            s2 = st.time_input("Dönüş")
            b = f"{t2.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}"
            d = f"{t2.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("İş Başı")
            b = t2.strftime('%d/%m/%Y')
            d = dn.strftime('%d/%m/%Y')
        
        if st.form_submit_button("GÖNDER") and ad:
            data = {
                "tarih": datetime.now().strftime("%d/%m/%Y"),
                "tc": tc, "ad": ad, "brans": "P",
                "tur": f"{t1} ({tp})", "bas": b, "bit": d
            }
            requests.post(URL, data=json.dumps(data))
            st.success("İletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    sifre = st.sidebar.text_input("Şifre", type="password")
    
    if sifre == "1234":
        df = yukle()
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Karne", "👤 Sicil", "📝 Manuel Kayıt", "📄 Formlar", "📅 Yıllık İzin Takip"
        ])
        
        with tab1: # KARNE
            if not df.empty:
                ay_list = df['Ay'].dropna().unique()
                if len(ay_list) > 0:
                    sel_ay = st.selectbox("Ay Seç", sorted(ay_list, reverse=True))
                    kn = df[df['Ay']==sel_ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                    st.table(kn.style.format({"G": "{:.1f}", "S": "{:.1f}"}))
            else: st.warning("Veri yok.")

        with tab2: # SİCİL
            if not df.empty:
                p_sec = st.selectbox("Personel Seç", sorted(df['Ad Soyad'].unique()))
                st.dataframe(df[df['Ad Soyad']==p_sec][['Başlangıç','Dönüş','Tür','G','S']])

        with tab3: # MANUEL
            m_ad = st.text_input("Manuel İsim")
            with st.form("m_form"):
                m_t = st.selectbox("İzin Türü", IZ)
                m_b = st.date_input("Başlangıç ")
                m_d = st.date_input("Dönüş ")
                if st.form_submit_button("KAYDET") and m_ad:
                    payload = {
                        "tarih": datetime.now().strftime("%d/%m/%Y"),
                        "tc": "0", "ad": m_ad, "brans": "Y", "tur": m_t,
                        "bas": m_b.strftime('%d/%m/%Y'),
                        "bit": m_d.strftime('%d/%m/%Y')
                    }
                    requests.post(URL, data=json.dumps(payload))
                    st.success("İşlendi!"); st.rerun()

        with tab4: # FORMLAR
            st.subheader("Kurumsal Formlar")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📄 PERSONEL İZİN FOR

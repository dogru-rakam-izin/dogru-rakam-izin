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

m = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if m == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad, tc = st.text_input("Ad Soyad"), st.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p"):
        t1, t2 = st.selectbox("İzin Türü", IZ), st.date_input("İzin Başlangıç")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış Saati"), st.time_input("Dönüş Saati")
            b, d = f"{t2.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{t2.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
        else:
            dn = st.date_input("İşe Başlama Tarihi")
            b, d = t2.strftime('%d/%m/%Y'), dn.strftime('%d/%m/%Y')
        if st.form_submit_button("TALEBİ GÖNDER") and ad:
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
            st.success("Talebiniz iletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    if st.sidebar.text_input("Giriş Şifresi", type="password") == "1234":
        df = yukle()
        tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel Kayıt", "📄 Formlar & Dilekçeler"])
        
        with tabs[0]: # KARNE
            if not df.empty:
                ay = st.selectbox("Görüntülenecek Ay", sorted(df['Ay'].dropna().unique(), reverse=True))
                kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                kn.columns = ['Ad Soyad', 'İzin Türü', 'Gün', 'Saat']
                st.table(kn.style.format({"Gün": "{:.1f}", "Saat": "{:.1f}"}))
            else: st.warning("Veri bulunamadı.")

        with tabs[1]: # SİCİL
            if not df.empty:
                p = st.selectbox("Personel Seç", sorted(df['Ad Soyad'].unique()))
                f = df[df['Ad Soyad']==p]
                st.metric("Toplam Kullanılan Gün", f"{f['G'].sum():.1f}")
                st.dataframe(f[['Başlangıç','Dönüş','Tür','G','S']].style.format({"G": "{:.1f}", "S": "{:.1f}"}))

        with tabs[2]: # MANUEL
            ma, mt = st.text_input("Kayıt Edilecek İsim"), st.radio("Tip", ["Tam Gün", "Saatlik"])
            with st.form("m"):
                tr, ta = st.selectbox("Tür", IZ), st.date_input("Tarih")
                if mt == "Saatlik":
                    m1, m2 = st.time_input("Başla"), st.time_input("Bitir")
                    mb, mi = f"{ta.strftime('%d/%m/%Y')} {m1.strftime('%H:%M')}", f"{ta.strftime('%d/%m/%Y')} {m2.strftime('%H:%M')}"
                else:
                    md = st.date_input("Dönüş")
                    mb, mi = ta.strftime('%d/%m/%Y'), md.strftime('%d/%m/%Y')
                if st.form_submit_button("SİSTEME İŞLE") and ma:
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime("%d/%m/%Y"),"tc":"0","ad":ma,"brans":"Y","tur":f"{tr} ({mt})","bas":mb,"bit":mi}))
                    st.success("Kayıt eklendi!"); st.rerun()

        with tabs[3]: # FORMLAR
            st.subheader("Kurumsal İzin Formları Şablonları")
            st.info("İlgili belgenin üzerine sağ tıklayıp yazdırabilir veya kopyalayabilirsiniz.")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📄 Genel İzin Formu"):
                    st.markdown("""**PERSONEL İZİN FORMU** [cite: 2]
                    * Adı Soyadı: .................... [cite: 5]
                    * İzin Türü: Yıllık/Mazeret/Sağlık/Ücretsiz [cite: 9]
                    * Tarih: ..../..../2026 [cite: 10]""")
            with c2:
                if st.button("📄 Ücretsiz İzin Dilekçesi"):
                    st.markdown("""**ÜCRETSİZ İZİN FORMU** [cite: 29]
                    * Şahsi nedenlerimle ücretsiz izin kullanmak istiyorum. [cite: 30]
                    * Ücret ödenmeyeceğini kabul ederim. [cite: 31]""")
            with c3:
                if st.button("📄 Yıllık İzin Dilekçesi"):
                    st.markdown("""**YILLIK İZİN DİLEKÇESİ** [cite: 36]
                    * 4857 Sayılı Kanun uyarınca yıllık izin talebi. [cite: 38]
                    * İzin Başlangıç: ..../..../2026 [cite: 40]""")

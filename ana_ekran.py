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

def yazdir_html(baslik, icerik):
    html = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 20mm; }}
            body {{ font-family: 'Times New Roman', serif; line-height: 1.6; color: #000; }}
            .paper {{ padding: 10px; }}
            .header {{ text-align: center; font-weight: bold; font-size: 16px; margin-bottom: 30px; text-transform: uppercase; }}
            .content {{ white-space: pre-wrap; font-size: 14px; text-align: justify; }}
            .footer {{ margin-top: 50px; }}
            @media print {{ 
                header, footer, .no-print {{ display: none !important; }} 
                body {{ margin: 0; }}
            }}
        </style>
    </head>
    <body onload="window.print();">
        <div class="paper">
            <div class="header">{baslik}</div>
            <div class="content">{icerik}</div>
        </div>
    </body>
    </html>
    """
    st.components.v1.html(html, height=0)

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
    if st.sidebar.text_input("Şifre", type="password") == "1234":
        df = yukle()
        tabs = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "📄 Formlar"])
        
        with tabs[0]:
            if not df.empty:
                ay = st.selectbox("Ay", sorted(df['Ay'].dropna().unique(), reverse=True))
                kn = df[df['Ay']==ay].groupby(['Ad Soyad','Tür'])[['G','S']].sum().reset_index()
                st.table(kn.style.format({"G": "{:.1f}", "S": "{:.1f}"}))

        with tabs[1]:
            if not df.empty:
                p = st.selectbox("Personel", sorted(df['Ad Soyad'].unique()))
                f = df[df['Ad Soyad']==p]
                st.metric("Toplam Gün", f"{f['G'].sum():.1f}")
                st.dataframe(f[['Başlangıç','Dönüş','Tür','G','S']])

        with tabs[2]:
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

        with tabs[3]:
            st.subheader("Kurumsal Form Yazdır")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📄 PERSONEL İZİN FORMU"):
                    m = """1. PERSONEL KİMLİK BİLGİLERİ\nAdı Soyadı: __________________________\nGörevi / Branşı: ______________________\nTC Kimlik No: ________________________\n\n2. İZİN / MAZERET BİLGİLERİ\nİzin Türü: [ ] Yıllık  [ ] Mazeret  [ ] Sağlık Raporu [ ] Ücretsiz\nAyrılış: .... / .... / 2026 - Saat: ____\nDönüş: .... / .... / 2026 - Saat: ____\nToplam Süre: ________ Gün ________ Saat\n\n3. EĞİTİM VE SEANS PLANLAMASI\n[ ] Telafi dersleri planlanmıştır.  [ ] Öğrenci velilerine bilgi verilmiştir.\n\n4. İLETİŞİM\nTelefon: __________________\nAdres: __________________________________________\n\n5. ONAY VE İMZA\nPersonel İmza: __________    Müdür/Kurucu Onay: [ ] [ ]"""
                    yazdir_html("DOĞRU RAKAM ÖZEL EĞİTİM VE REHABİLİTASYON MERKEZİ", m)
            with c2:
                if st.button("📄 ÜCRETSİZ İZİN"):
                    m = """Doğru Rakam Özel Eğitim ve Rehabilitasyon Merkezi Müdürlüğü’ne\n\nKurumunuzun .......................... branşındaki personelliyim. ... / ... / 2026 ile ... / ... / 2026 tarihleri arasında, şahsi nedenlerim dolayısıyla ÜCRETSİZ İZİN kullanmak istiyorum. Bu süre zarfında tarafıma herhangi bir ücret ödenmeyeceğini kabul ediyorum. İzin süresince seans planlamaları yapılmış olup derslerin aksamaması için gerekli önlemler alınmıştır.\n\nGereğini bilgilerinize arz ederim.\n\nTarih: ... / ... / 2026\nİsim/İmza: __________________________"""
                    yazdir_html("ÜCRETSİZ İZİN DİLEKÇESİ", m)
            with c3:
                if st.button("📄 YILLIK İZİN"):
                    m = """DOĞRU RAKAM ÖZEL EĞİTİM VE REHABİLİTASYON MERKEZİ MÜDÜRLÜĞÜ’NE\n\nKurumunuzda .................................... T.C. Kimlik numarası ile görev yapmaktayım. 4857 Sayılı İş Kanunu’ndan doğan yıllık ücretli izin hakkımın aşağıda belirtilen tarihler arasında kullandırılmasını talep etmekteyim.\n\nİzin Başlangıç Tarihi: .... / .... / 2026\nİşe Başlama Tarihi: .... / .... / 2026\n\nİletişim Bilgileri:\nTelefon: ................................\nAdres: .............................................................\n\nTarih: .... / .... / 2026\nAd Soyad: ........................  İmza: .....................\n\nONAY: [ ] Uygun Görülmüştür [ ] Uygun Görülmemiştir"""
                    yazdir_html("YILLIK İZİN DİLEKÇESİ", m)

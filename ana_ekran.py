import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import urllib.parse

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbxYuY8PRJq1QUysnPqU8t50onoEMWHHBbi1PbQaYIA0HepRpvuA478nRS_PuQbu-oZL/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin", layout="wide", page_icon=LOGO_URL)

# --- PERSONEL VERİTABANI ---
PERSONEL_GIRISLERI = {
    "ARİF EMRE YILDIZ": "2024-10-09", "AYŞE KOLBAŞ": "2022-03-04",
    "AYŞE GÜLLÜ ÇIRAY": "2023-04-27", "BURAK ÖZAYDIN": "2025-09-11",
    "BUSE MEYRİLİ": "2025-02-07", "ERSİN KALSEN": "2023-06-06",
    "FERİDE CIKKAN": "2025-03-13", "GÖKÇE DÖNMEZKOL": "2025-06-24",
    "HİDAYET ARZU ER": "2025-02-07", "HÜSEYİN KIZIL": "2025-11-18",
    "İBRAHİM SOYLU": "2020-09-17", "MERVE ANAYURT": "2025-03-11",
    "MİZGİN BİDER": "2025-09-15", "NEFİSE NUR HOŞGÖR": "2025-06-09",
    "ÖZLEM KAPLAN": "2024-08-01", "PINAR TANRIVERDİ": "1900-01-01",
    "SAMET DEMİREL": "2024-02-27", "GÜNAY AKTEPE": "2025-09-24",
    "ŞERİFE ŞENGÜL": "2025-05-20", "TANER DOĞAN": "2026-02-01",
    "ARZU ÖZELMİŞ": "2025-11-17", "SİDAL ZENGİN": "2025-11-17",
    "SELEN ŞEN": "2025-11-03"
}

F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim", "Geç Kalma"]

def hakedis_bul(yil):
    if yil < 1: return 0
    if yil < 5: return 14
    if yil < 15: return 20
    return 26

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame(), "Ad Soyad"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), "Ad Soyad")
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        def h(r):
            try:
                ts, b_str, d_str = str(r['Tür']), str(r['Başlangıç']).strip(), str(r['Dönüş']).strip()
                if "Saatlik" in ts or "Geç Kalma" in ts:
                    b, d = datetime.strptime(b_str, F_TAM), datetime.strptime(d_str, F_TAM)
                    diff_seconds = (d - b).total_seconds()
                    saat = int(diff_seconds // 3600)
                    dakika = int((diff_seconds % 3600) // 60)
                    
                    # Düzenlenmiş Boşluklu Format
                    if saat > 0 and dakika > 0:
                        return 0, f"{saat} Sa {dakika} Dk"
                    elif saat > 0:
                        return 0, f"{saat} Sa"
                    else:
                        return 0, f"{dakika} Dk"
                else:
                    b, d = datetime.strptime(b_str[:10], F_TARIH), datetime.strptime(d_str[:10], F_TARIH)
                    return (d-b).days, 0
            except: return 0, 0

        res = df.apply(lambda r: pd.Series(h(r)), axis=1)
        df['G'], df['S'] = res[0], res[1]
        df['T'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay'] = df['T'].dt.strftime('%B').map(TR) + " " + df['T'].dt.strftime('%Y')
        return df, ad_col
    except: return pd.DataFrame(), "Ad Soyad"

st.markdown(f"<style>[data-testid='stSidebarNav'] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }} .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; text-align: center; }} div.stButton > button {{ background-color: #25D366 !important; color: white !important; font-weight: bold; }} </style>", unsafe_allow_html=True)

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if m == "👤 PERSONEL GİRİŞİ":
    st.markdown('<p class="main-title">DOĞRU RAKAM ÖZEL EĞİTİM</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad").upper(); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    
    with st.form("p_f"):
        t1 = st.selectbox("Tür", IZ[:-1]); t2 = st.date_input("İzin Günü")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
        else:
            dn = st.date_input("İş Başı"); b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
        kaydet = st.form_submit_button("SİSTEME KAYDET")
        
    if kaydet and ad:
        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d}))
        st.session_state['p_wa'] = f"🔔 *YENİ İZİN TALEBİ*\n👤 *Personel:* {ad}\n📋 *Tür:* {t1} ({tp})\n🕒 *Başlangıç:* {b}\n🏠 *Dönüş:* {d}"
        st.success("Kayıt Başarılı.")

    if 'p_wa' in st.session_state:
        st.link_button("🟢 WHATSAPP İLE BİLDİR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['p_wa'])}", use_container_width=True)

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        df, ad_sutunu = yukle()
        t = st.tabs(["📊 Karne", "👤 Sicil", "📝 Manuel", "⏰ Geç Kalma", "📅 Yıllık İzin", "🗑️ Liste & Sil"])
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

        with t[0]: # KARNE
            st.subheader("📊 Aylık Personel Karnesi")
            if not df.empty and 'Ay' in df.columns:
                ay_secim = st.selectbox("Ay Seçiniz", sorted(df['Ay'].dropna().unique(), reverse=True))
                # Saatlik verileri birleştirirken araya boşluk ekle
                karne_data = df[df['Ay']==ay_secim].groupby([ad_sutunu,'Tür'])[['G','S']].sum()
                st.dataframe(karne_data, use_container_width=True)
                
                csv_karne = karne_data.to_csv(index=True, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 Karneyi Excel Olarak İndir", data=csv_karne, file_name=f"Karne_{ay_secim}.csv", mime="text/csv")
            else: st.info("Veri bulunamadı.")

        with t[1]: # SİCİL
            st.subheader("👤 Personel Sicil Özeti")
            p_sicil = st.selectbox("Personel Seçiniz", p_listesi)
            if not df.empty:
                sicil_df = df[df[ad_sutunu]==p_sicil][['Başlangıç','Dönüş','Tür','G','S']]
                st.dataframe(sicil_df, use_container_width=True)
                csv_sicil = sicil_df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(f"📥 {p_sicil} Sicilini İndir", data=csv_sicil, file_name=f"Sicil_{p_sicil}.csv", mime="text/csv")

        with t[2]: # MANUEL GİRİŞ
            st.subheader("📝 Manuel Kayıt")
            with st.form("m_f"):
                m_ad = st.selectbox("Personel", p_listesi); m_tp = st.selectbox("Tip", ["Tam Gün", "Saatlik"])
                m_tr = st.selectbox("Tür", IZ[:-1]); m_tarih = st.date_input("Tarih")
                ms1, ms2 = st.time_input("Çıkış"), st.time_input("Dönüş"); m_db = st.date_input("İş Başı")
                m_kaydet = st.form_submit_button("MANUEL EKLE")
            
            if m_kaydet:
                mb, md = (f"{m_tarih.strftime(F_TARIH)} {ms1.strftime(F_SAAT)}", f"{m_tarih.strftime(F_TARIH)} {ms2.strftime(F_SAAT)}") if m_tp == "Saatlik" else (m_tarih.strftime(F_TARIH), m_db.strftime(F_TARIH))
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} ({m_tp})","bas":mb,"bit":md}))
                st.session_state['m_wa'] = f"✅ *MANUEL İZİN KAYDI*\n👤 *Personel:* {m_ad}\n📋 *Tür:* {m_tr} ({m_tp})\n🕒 *Başlangıç:* {mb}\n🏠 *Dönüş:* {md}"
                st.success("Kayıt eklendi.")

            if 'm_wa' in st.session_state:
                st.link_button("🟢 WHATSAPP İLE BİLDİR (MANUEL)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['m_wa'])}", use_container_width=True)

        with t[3]: # GEÇ KALMA
            st.subheader("⏰ Geç Kalma Girişi")
            with st.form("g_f"):
                g_ad, g_tar = st.selectbox("Personel", p_listesi), st.date_input("Geç Kalınan Gün")
                g_dak = st.slider("Dakika", 1, 60, 15)
                if st.form_submit_button("GEÇ KALMA KAYDET"):
                    g_bas, g_bit = f"{g_tar.strftime(F_TARIH)} 09:00", f"{g_tar.strftime(F_TARIH)} 09:{g_dak:02d}"
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":g_ad,"brans":"Y","tur":"Geç Kalma","bas":g_bas,"bit":g_bit}))
                    st.success("Kayıt yapıldı.")

        with t[4]: # YILLIK İZİN
            py = st.selectbox("Hakediş Sorgula", p_listesi)
            varsay_t = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            gt = st.date_input("İşe Giriş", value=varsay_t)
            kidem = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk, ku = hakedis_bul(max(0, kidem)), (pd.to_numeric(df[(df[ad_sutunu]==py) & (df['Tür'].str.contains("Yıllık"))]['G'], errors='coerce').sum() if not df.empty else 0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")

        with t[5]: # LİSTE & SİL
            if not df.empty:
                df_sil = df.copy(); df_sil.insert(0, "SİLME_ID", df_sil.index + 2)
                st.dataframe(df_sil.tail(30), use_container_width=True)
                csv_full = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 Tüm Ham Veriyi İndir", data=csv_full, file_name="Tum_Liste.csv")
                st.divider()
                sid = st.number_input("Silinecek No:", min_value=2, step=1)
                if st.button("❌ SEÇİLİ KAYDI SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sid)}))
                    st.success(f"{sid} numaralı satır silindi.")
    else: st.warning("Lütfen Yönetici Şifresini Giriniz.")

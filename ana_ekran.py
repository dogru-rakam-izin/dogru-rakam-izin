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

st.set_page_config(page_title="Doğru Rakam İzin Sistemi", layout="wide", page_icon=LOGO_URL)

# --- PERSONEL VERİTABANI ---
PERSONEL_GIRISLERI = {
    "ARİF EMRE YILDIZ": "2024-10-09", "AYŞE KOLBAŞ": "2022-03-04", "AYŞE GÜLLÜ ÇIRAY": "2023-04-27", 
    "BURAK ÖZAYDIN": "2025-09-11", "BUSE MEYRİLİ": "2025-02-07", "ERSİN KALSEN": "2023-06-06",
    "FERİDE CIKKAN": "2025-03-13", "GÖKÇE DÖNMEZKOL": "2025-06-24", "HİDAYET ARZU ER": "2025-02-07", 
    "HÜSEYİN KIZIL": "2025-11-18", "İBRAHİM SOYLU": "2020-09-17", "MERVE ANAYURT": "2025-03-11",
    "MİZGİN BİDER": "2025-09-15", "NEFİSE NUR HOŞGÖR": "2025-06-09", "ÖZLEM KAPLAN": "2024-08-01", 
    "PINAR TANRIVERDİ": "1900-01-01", "SAMET DEMİREL": "2024-02-27", "GÜNAY AKTEPE": "2025-09-24",
    "ŞERİFE ŞENGÜL": "2025-05-20", "TANER DOĞAN": "2026-02-01", "ARZU ÖZELMİŞ": "2025-11-17", 
    "SİDAL ZENGİN": "2025-11-17", "SELEN ŞEN": "2025-11-03"
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
        if df.empty: return pd.DataFrame(), pd.DataFrame(), "Ad Soyad", "Durum"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), "Ad Soyad")
        durum_col = next((c for c in df.columns if "DURUM" in c.upper()), "Durum")
        
        if durum_col not in df.columns:
            df[durum_col] = "Onaylandı" # Sütun yoksa herkesi onaylı say (Eskiler gelsin diye)
        
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        # Sadece Onaylananlar Karneye/Sicile
        df_onayli = df[df[durum_col].astype(str).str.contains("Onaylandı", case=False, na=False)].copy()
        
        def h(r):
            try:
                ts, b_str, d_str = str(r['Tür']), str(r['Başlangıç']).strip(), str(r['Dönüş']).strip()
                if "Saatlik" in ts or "Geç Kalma" in ts:
                    b, d = datetime.strptime(b_str, F_TAM), datetime.strptime(d_str, F_TAM)
                    return 0, round((d-b).total_seconds()/3600, 2)
                else:
                    b, d = datetime.strptime(b_str[:10], F_TARIH), datetime.strptime(d_str[:10], F_TARIH)
                    return (d-b).days, 0
            except: return 0, 0

        if not df_onayli.empty:
            res = df_onayli.apply(lambda r: pd.Series(h(r)), axis=1)
            df_onayli['G'], df_onayli['S'] = res[0].astype(float), res[1].astype(float)
            df_onayli['T'] = pd.to_datetime(df_onayli['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
            df_onayli['Ay'] = df_onayli['T'].dt.strftime('%B').map(TR) + " " + df_onayli['T'].dt.strftime('%Y')
        
        return df, df_onayli, ad_col, durum_col
    except: return pd.DataFrame(), pd.DataFrame(), "Ad Soyad", "Durum"

st.markdown(f"<style>[data-testid='stSidebarNav'] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }} .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; text-align: center; }} div.stButton > button {{ background-color: #25D366 !important; color: white !important; font-weight: bold; }} </style>", unsafe_allow_html=True)

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ ONAY PANELİ"])

if m == "👤 PERSONEL İZİN TALEBİ":
    st.markdown('<p class="main-title">DOĞRU RAKAM İZİN TALEBİ</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad").upper(); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    
    with st.form("p_f"):
        t1, t2 = st.selectbox("İzin Türü", IZ[:-1]), st.date_input("İzin Başlangıç")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış Saati"), st.time_input("Dönüş Saati")
            b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
            detay = f"⏰ *Saat:* {s1.strftime(F_SAAT)} - {s2.strftime(F_SAAT)}"
        else:
            dn = st.date_input("İş Başı")
            b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
            detay = f"📅 *Tarih:* {b} - {d}"
        
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad:
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d, "durum": "Onay Bekliyor"}))
                st.session_state['wa_msg'] = f"🔔 *İİZİN TALEP BİLDİRİMİ*\n👤 *Personel:* {ad}\n📋 *Tür:* {t1} ({tp})\n{detay}\n\n📝 *Not:* İzniniz onaylandığında; programı düzenleyip dilekçenizi iletmeyi unutmayınız."
                st.success("Talep gönderildi. WhatsApp ile gruba bildirmeyi unutmayın.")

    if 'wa_msg' in st.session_state:
        msg = urllib.parse.quote(st.session_state['wa_msg'])
        st.link_button("🟢 WHATSAPP İLE GRUBA YAZ", f"https://api.whatsapp.com/send?text={msg}", use_container_width=True)

else:
    if st.sidebar.text_input("Yönetici Şifresi", type="password") == "2020":
        df_all, df_onayli, ad_sutunu, durum_sutunu = yukle()
        t = st.tabs(["🔔 Onay Bekleyenler", "📊 Karne", "👤 Sicil", "📝 Manuel", "⏰ Geç Kalma", "📅 Yıllık İzin", "🗑️ Liste"])
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

        with t[0]: # Onay Bekleyenler
            st.subheader("Onay Bekleyen İstekler")
            if not df_all.empty:
                bekleyen = df_all[df_all[durum_sutunu] == "Onay Bekliyor"].copy()
                if not bekleyen.empty:
                    bekleyen.insert(0, "SATIR_NO", bekleyen.index + 2)
                    st.dataframe(bekleyen[["SATIR_NO", ad_sutunu, "Tür", "Başlangıç", "Dönüş"]], use_container_width=True)
                    st.info("Onaylamak için Sheets dosyasında 'Durum' sütununu 'Onaylandı' yapın.")
                else: st.success("Bekleyen talep yok.")

        with t[1]: # Karne
            if not df_onayli.empty:
                ay_secim = st.selectbox("Ay Seç", sorted(df_onayli['Ay'].dropna().unique(), reverse=True))
                st.dataframe(df_onayli[df_onayli['Ay']==ay_secim].groupby([ad_sutunu,'Tür'])[['G','S']].sum())
            else: st.warning("Onaylanmış veri yok.")

        with t[3]: # Manuel
            with st.form("m_f"):
                m_ad = st.selectbox("Personel", p_listesi)
                m_tr = st.selectbox("Tür", IZ[:-1])
                m_tar = st.date_input("İzin Günü")
                m_db = st.date_input("Dönüş Günü")
                if st.form_submit_button("MANUEL EKLE (DİREKT ONAYLI)"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} (Tam Gün)","bas":m_tar.strftime(F_TARIH),"bit":m_db.strftime(F_TARIH), "durum": "Onaylandı"}))
                    st.success("Kayıt başarıyla eklendi ve onaylandı.")

        with t[4]: # Geç Kalma
            with st.form("g_f"):
                g_ad = st.selectbox("Personel", p_listesi); g_t = st.date_input("Tarih"); g_d = st.slider("Dakika", 1, 60, 15)
                if st.form_submit_button("GEÇ KALMA KAYDET (DİREKT ONAYLI)"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":g_ad,"brans":"Y","tur":"Geç Kalma","bas":f"{g_t.strftime(F_TARIH)} 09:00","bit":f"{g_t.strftime(F_TARIH)} 09:{g_d:02d}", "durum": "Onaylandı"}))
                    st.success("Geç kalma işlendi.")

        with t[5]: # Yıllık İzin
            py = st.selectbox("Hakediş", p_listesi)
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kidem = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk, ku = hakedis_bul(max(0, kidem)), (df_onayli[(df_onayli[ad_sutunu]==py) & (df_onayli['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_onayli.empty else 0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")

        with t[6]: # Liste
            st.dataframe(df_all, use_container_width=True)

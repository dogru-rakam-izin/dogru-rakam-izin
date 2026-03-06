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
        
        # Sütun isimlerini temizle
        df.columns = [str(c).strip() for c in df.columns]
        
        # Sütunları Tespit Et
        ad_col = next((c for c in df.columns if "AD" in c.upper()), df.columns[2])
        durum_col = next((c for c in df.columns if "DURUM" in c.upper()), None)
        
        # Eğer Durum sütunu yoksa, son sütunu Durum kabul et veya oluştur
        if durum_col is None:
            df["Durum"] = "Onaylandı" # Varsayılan
            durum_col = "Durum"
            
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        df[durum_col] = df[durum_col].astype(str).str.strip()
        
        # Onay Bekleyenler Filtresi (Büyük/Küçük harf duyarsız)
        df_bekleyen = df[df[durum_col].str.contains("Bekliyor", case=False, na=False)].copy()
        
        # Onaylananlar Filtresi
        df_onayli = df[df[durum_col].str.contains("Onaylandı", case=False, na=False)].copy()
        
        # Hesaplama fonksiyonu
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
        
        return df_bekleyen, df_onayli, ad_col, durum_col
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        return pd.DataFrame(), pd.DataFrame(), "Ad Soyad", "Durum"

st.markdown(f"<style>[data-testid='stSidebarNav'] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }} .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; text-align: center; }} div.stButton > button {{ background-color: #25D366 !important; color: white !important; font-weight: bold; }} </style>", unsafe_allow_html=True)

menu = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL İZİN TALEBİ":
    st.markdown('<p class="main-title">DOĞRU RAKAM İZİN TALEBİ</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2); ad = c1.text_input("Ad Soyad").upper(); tc = c2.text_input("TC No", max_chars=11)
    tp = st.radio("İzin Süresi", ["Tam Gün", "Saatlik"], horizontal=True)
    
    with st.form("p_f"):
        t1, t2 = st.selectbox("İzin Türü", IZ[:-1]), st.date_input("İzin Başlangıç")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t2.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t2.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
            detay = f"⏰ *Saat:* {s1.strftime(F_SAAT)} - {s2.strftime(F_SAAT)}"
        else:
            dn = st.date_input("İş Başı")
            b, d = t2.strftime(F_TARIH), dn.strftime(F_TARIH)
            detay = f"📅 *Tarih:* {b} - {d}"
        
        if st.form_submit_button("TALEBİ SİSTEME GÖNDER"):
            if ad:
                # ÖNEMLİ: Google Sheets'e "Onay Bekliyor" metnini gönderiyoruz
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d, "durum": "Onay Bekliyor"}))
                st.session_state['wa_msg'] = f"🔔 *YENİ İZİN TALEBİ*\n👤 *Personel:* {ad}\n📋 *Tür:* {t1} ({tp})\n{detay}\n\n📝 *Not:* İzniniz onaylandığında; programı düzenleyip dilekçenizi iletmeyi unutmayınız."
                st.success("Talebiniz kaydedildi. Lütfen WhatsApp butonuna basın.")

    if 'wa_msg' in st.session_state:
        msg = urllib.parse.quote(st.session_state['wa_msg'])
        st.link_button("🟢 WHATSAPP İLE GRUBA BİLDİR", f"https://api.whatsapp.com/send?text={msg}", use_container_width=True)

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        df_bekleyen, df_onayli, ad_sutunu, durum_sutunu = yukle()
        t = st.tabs(["🔔 Onay Bekleyenler", "📊 Karne", "👤 Sicil", "📝 Manuel", "⏰ Geç Kalma", "📅 Yıllık İzin"])
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

        with t[0]: # Onay Bekleyenler
            st.subheader("Onay Bekleyen İstekler")
            if not df_bekleyen.empty:
                df_b_goster = df_bekleyen.copy()
                df_b_goster.insert(0, "SATIR_NO", df_b_goster.index + 2)
                st.dataframe(df_b_goster[["SATIR_NO", ad_sutunu, "Tür", "Başlangıç", "Dönüş"]], use_container_width=True)
                st.info("💡 **Onaylama:** Google Sheets'te bu satırın 'Durum' hücresine 'Onaylandı' yazın.")
            else:
                st.success("Harika! Bekleyen hiçbir talep yok.")

        with t[1]: # Karne
            if not df_onayli.empty:
                ay_secim = st.selectbox("Ay Seç", sorted(df_onayli['Ay'].dropna().unique(), reverse=True))
                st.dataframe(df_onayli[df_onayli['Ay']==ay_secim].groupby([ad_sutunu,'Tür'])[['G','S']].sum())
            else: st.warning("Onaylanmış kayıt bulunamadı.")

        with t[2]: # Sicil
            ps = st.selectbox("Personel", p_listesi)
            if not df_onayli.empty:
                st.dataframe(df_onayli[df_onayli[ad_sutunu]==ps][['Başlangıç','Dönüş','Tür','G','S']])

        with t[3]: # Manuel
            with st.form("m_f"):
                m_ad = st.selectbox("Personel", p_listesi); m_tr = st.selectbox("Tür", IZ[:-1]); m_tar = st.date_input("Tarih")
                if st.form_submit_button("EKLE"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"0","ad":m_ad,"brans":"Y","tur":f"{m_tr} (Tam)","bas":m_tar.strftime(F_TARIH),"bit":m_tar.strftime(F_TARIH), "durum": "Onaylandı"}))
                    st.success("Eklendi.")

        with t[5]: # Yıllık İzin
            py = st.selectbox("Sorgula", p_listesi)
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kidem = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk = hakedis_bul(max(0, kidem))
            ku = (df_onayli[(df_onayli[ad_sutunu]==py) & (df_onayli['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_onayli.empty else 0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")

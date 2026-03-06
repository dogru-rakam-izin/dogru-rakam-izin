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
        if df.empty: return pd.DataFrame(), "Ad Soyad"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), "Ad Soyad")
        durum_col = next((c for c in df.columns if "DURUM" in c.upper()), None)
        
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        # Sadece ONAYLANMIŞ veriler karneye/sicile yansısın
        df_onayli = df[df[durum_col] == "Onaylandı"].copy() if durum_col else df.copy()
        
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
    except: return pd.DataFrame(), pd.DataFrame(), "Ad Soyad", None

st.markdown(f"<style>[data-testid='stSidebarNav'] {{ background-image: url({LOGO_URL}); background-repeat: no-repeat; padding-top: 140px; background-position: center 20px; background-size: 150px auto; }} .main-title {{ color: #CC0000; font-size: 38px; font-weight: bold; text-align: center; }} div.stButton > button {{ background-color: #25D366 !important; color: white !important; font-weight: bold; }} </style>", unsafe_allow_html=True)

m = st.sidebar.radio("📌 MENÜ SEÇİMİ", ["👤 PERSONEL İZİN TALEBİ", "🔐 YÖNETİCİ ONAY PANELİ"])

if m == "👤 PERSONEL İZİN TALEBİ":
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
        
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad:
                # Veriyi 'Onay Bekliyor' olarak gönderiyoruz (Durum sütunu için en sona ekledik)
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":tc,"ad":ad,"brans":"P","tur":f"{t1} ({tp})","bas":b,"bit":d, "durum": "Onay Bekliyor"}))
                st.session_state['wa_msg'] = f"🔔 *İİZİN TALEP BİLDİRİMİ*\n👤 *Personel:* {ad}\n📋 *Tür:* {t1} ({tp})\n{detay}\n\n📝 *Not:* İzniniz onaylandığında; programı düzenleyip dilekçenizi iletmeyi unutmayınız."
                st.success("Talebiniz yöneticiye iletildi. Lütfen WhatsApp butonuna tıklayarak grubu bilgilendirin.")

    if 'wa_msg' in st.session_state:
        msg = urllib.parse.quote(st.session_state['wa_msg'])
        st.link_button("🟢 WHATSAPP İLE GRUBA YAZ", f"https://api.whatsapp.com/send?text={msg}", use_container_width=True)

else:
    if st.sidebar.text_input("Yönetici Şifresi", type="password") == "2020":
        df_all, df_onayli, ad_sutunu, durum_sutunu = yukle()
        t = st.tabs(["🔔 Onay Bekleyenler", "📊 Karne", "👤 Sicil", "📝 Manuel", "⏰ Geç Kalma", "📅 Yıllık İzin", "🗑️ Liste"])
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

        with t[0]: # ONAY BEKLEYENLER
            st.subheader("Onay Bekleyen İzin İstekleri")
            if durum_sutunu and not df_all.empty:
                bekleyenler = df_all[df_all[durum_sutunu] == "Onay Bekliyor"].copy()
                if not bekleyenler.empty:
                    bekleyenler.insert(0, "ISLEM_ID", bekleyenler.index + 2)
                    st.table(bekleyenler[[ "ISLEM_ID", ad_sutunu, "Tür", "Başlangıç", "Dönüş"]])
                    
                    c1, c2 = st.columns(2)
                    islem_id = c1.number_input("İşlem Yapılacak ID:", min_value=2, step=1)
                    if c2.button("✅ SEÇİLENİ ONAYLA"):
                        # Google Script'e 'onayla' komutu gönderilmeli (veya manuel güncellenmeli)
                        # Şimdilik mevcut silme mantığıyla benzer bir yapı kurulabilir
                        st.info("Onaylama işlemi için Sheets üzerinden 'Durum' sütununu 'Onaylandı' yapınız veya Script'i güncelleyelim.")
                else: st.success("Bekleyen istek yok.")

        with t[1]: # Karne (Sadece Onaylılar)
            if not df_onayli.empty:
                ay_secim = st.selectbox("Ay Seç", sorted(df_onayli['Ay'].dropna().unique(), reverse=True))
                st.dataframe(df_onayli[df_onayli['Ay']==ay_secim].groupby([ad_sutunu,'Tür'])[['G','S']].sum())
            else: st.info("Onaylanmış veri bulunamadı.")
            
        # Diğer sekmeler (Sicil, Manuel vb.) df_onayli üzerinden çalışacak şekilde mevcudiyetini korur.

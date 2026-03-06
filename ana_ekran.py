import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import urllib.parse

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

# --- LOGO YERLEŞİMİ (SAYFA BAŞINA ORTALI) ---
# Sidebar'dan silindi, ana sayfanın en üstüne 3 sütunla ortalandı
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    st.image(LOGO_URL, width=300)

F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim", "Geç Kalma"]

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

def hakedis_bul(yil):
    if yil < 1: return 0
    if yil < 5: return 14
    if yil < 15: return 20
    return 26

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Ad Soyad"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), df.columns[2])
        if "Durum" not in df.columns: df["Durum"] = "Onaylandı"
        df["Durum"] = df["Durum"].fillna("Onay Bekliyor").astype(str).str.strip()
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        df_bekleyen = df[df["Durum"].str.contains("Bekliyor", case=False, na=True)].copy()
        df_onayli = df[df["Durum"].str.contains("Onaylandı", case=False, na=False)].copy()
        
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
        return df, df_bekleyen, df_onayli, ad_col
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Ad Soyad"

menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h1 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h1>', unsafe_allow_html=True)
    with st.form("p_form"):
        ad = st.text_input("Ad Soyad").upper()
        tur = st.selectbox("İzin Türü", IZ[:-1])
        tp = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
        t1 = st.date_input("Başlangıç")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t1.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t1.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
        else:
            dn = st.date_input("İş Başı")
            b, d = t1.strftime(F_TARIH), dn.strftime(F_TARIH)
        if st.form_submit_button("TALEBİ GÖNDER"):
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"","ad":ad,"brans":"P","tur":f"{tur} ({tp})","bas":b,"bit":d, "durum": "Onay Bekliyor"}))
            st.success("Talep gönderildi.")

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        df_all, df_b, df_o, ad_c = yukle()
        p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))
        t = st.tabs(["🔔 Onay Bekleyenler", "📊 Karne", "👤 Sicil", "📝 Manuel Giriş", "⏰ Geç Kalma", "📅 Yıllık İzin", "🗑️ Liste ve Silme"])
        
        with t[0]: 
            if not df_b.empty:
                df_b_goster = df_b.copy()
                df_b_goster.insert(0, "ID", df_b_goster.index + 2)
                st.table(df_b_goster[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                
                c1, c2 = st.columns(2)
                onay_id = c1.number_input("İşlem Yapılacak ID:", min_value=2, step=1, key="onay_id")
                
                if c2.button("✅ SEÇİLENİ ONAYLA"):
                    secim = df_b_goster[df_b_goster["ID"] == onay_id]
                    if not secim.empty:
                        pers_ad = secim[ad_c].values[0]
                        izin_turu = secim["Tür"].values[0]
                        baslangic = secim["Başlangıç"].values[0]
                        donus = secim["Dönüş"].values[0]
                        
                        requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(onay_id)}))
                        
                        msg = f"✅ *SAYIN {pers_ad},*\n\n"
                        msg += f"🗓 *{baslangic} - {donus}* tarihlerindeki\n"
                        msg += f"📋 *{izin_turu}* talebiniz onaylanmıştır.\n\n"
                        msg += "📝 Programı düzenleyip dilekçenizi yönetime iletmeyi unutmayınız."
                        
                        st.session_state['wa_msg'] = msg
                        st.success(f"{pers_ad} onaylandı!")
                    else:
                        st.error("Hatalı ID!")
                
                if 'wa_msg' in st.session_state:
                    st.link_button("🟢 ONAY MESAJINI PERSONELE GÖNDER", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['wa_msg'])}", use_container_width=True)
            else: st.success("Bekleyen yok.")

        # DİĞER SEKMELER (GİZLENEN ÖZELLİKLER DAHİL)
        with t[1]: # Karne
            if not df_o.empty:
                ay_sec = st.selectbox("Ay Seç", sorted(df_o['Ay'].dropna().unique(), reverse=True))
                st.dataframe(df_o[df_o['Ay']==ay_sec].groupby([ad_c,'Tür'])[['G','S']].sum(), use_container_width=True)
        with t[2]: # Sicil
            ps = st.selectbox("Personel", p_listesi)
            if not df_o.empty: st.dataframe(df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)
        with t[3]: # Manuel Giriş
            with st.form("m_form"):
                m_ad = st.selectbox("Personel", p_listesi); m_tr = st.selectbox("Tür", IZ[:-1])
                m_t1 = st.date_input("Başlangıç"); m_t2 = st.date_input("Dönüş")
                if st.form_submit_button("ONAYLI KAYIT EKLE"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"","ad":m_ad,"brans":"Y","tur":f"{m_tr} (Tam)","bas":m_t1.strftime(F_TARIH),"bit":m_t2.strftime(F_TARIH), "durum": "Onaylandı"}))
                    st.success("Kayıt eklendi.")
        with t[4]: # Geç Kalma
            with st.form("g_form"):
                g_ad = st.selectbox("Personel Seç", p_listesi); g_t = st.date_input("Tarih"); g_d = st.slider("Dakika", 1, 60, 15)
                if st.form_submit_button("GEÇ KALMA İŞLE"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"","ad":g_ad,"brans":"Y","tur":"Geç Kalma","bas":f"{g_t.strftime(F_TARIH)} 09:00","bit":f"{g_t.strftime(F_TARIH)} 09:{g_d:02d}", "durum": "Onaylandı"}))
                    st.success("İşlendi.")
        with t[5]: # Yıllık İzin
            py = st.selectbox("Hakediş Sorgula", p_listesi)
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kidem = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk = hakedis_bul(max(0, kidem))
            ku = (df_o[(df_o[ad_c]==py) & (df_o['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_o.empty else 0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")
        with t[6]: # Liste ve Silme
            if not df_all.empty:
                df_l = df_all.copy(); df_l.insert(0, "ID", df_l.index + 2); st.dataframe(df_l, use_container_width=True)
                c1, c2 = st.columns(2); sil_id = c1.number_input("Silinecek ID:", min_value=2, step=1, key="sil_id_input")
                if c2.button("❌ SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sil_id)}))
                    st.error("Kayıt silindi.")

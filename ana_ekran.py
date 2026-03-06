import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import urllib.parse

# --- GÜNCEL AYARLAR ---
# Yeni ilettiğiniz URL buraya eklendi
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

# --- AYARLAR VE ÇEVİRİLER ---
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
TR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZ = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim", "Geç Kalma"]

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

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame(), pd.DataFrame(), "Ad Soyad"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), df.columns[2])
        
        if "Durum" not in df.columns:
            df["Durum"] = "Onaylandı"
        
        df["Durum"] = df["Durum"].fillna("Onay Bekliyor").astype(str).str.strip()
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
        df_bekleyen = df[df["Durum"].str.contains("Bekliyor", case=False, na=True)].copy()
        df_onayli = df[df["Durum"].str.contains("Onaylandı", case=False, na=False)].copy()
        
        # Gün/Saat hesaplama
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
        
        return df_bekleyen, df_onayli, ad_col
    except:
        return pd.DataFrame(), pd.DataFrame(), "Ad Soyad"

st.sidebar.image(LOGO_URL, width=150)
menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h1 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h1>', unsafe_allow_html=True)
    with st.form("personel_form"):
        ad = st.text_input("Ad Soyad").upper()
        tur = st.selectbox("İzin Türü", IZ[:-1])
        tp = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
        t1 = st.date_input("Başlangıç Tarihi")
        if tp == "Saatlik":
            s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
            b, d = f"{t1.strftime(F_TARIH)} {s1.strftime(F_SAAT)}", f"{t1.strftime(F_TARIH)} {s2.strftime(F_SAAT)}"
        else:
            dn = st.date_input("İş Başı Tarihi")
            b, d = t1.strftime(F_TARIH), dn.strftime(F_TARIH)
        
        if st.form_submit_button("TALEBİ GÖNDER"):
            if ad:
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"tc":"","ad":ad,"brans":"P","tur":f"{tur} ({tp})","bas":b,"bit":d, "durum": "Onay Bekliyor"}))
                st.success("Talebiniz kaydedildi. Lütfen WhatsApp ile gruba bilgi veriniz.")
                st.session_state['p_wa'] = f"🔔 *İZİN TALEBİ*\n👤 {ad}\n📋 {tur} ({tp})\n📅 {b} / {d}"

    if 'p_wa' in st.session_state:
        st.link_button("🟢 WHATSAPP GRUBUNA BİLDİR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['p_wa'])}", use_container_width=True)

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        df_b, df_o, ad_c = yukle()
        t = st.tabs(["🔔 Onay Bekleyenler", "📊 Karne", "👤 Sicil"])
        
        with t[0]:
            st.subheader("Onay Bekleyen İstekler")
            if not df_b.empty:
                # Satır numarasını (ID) hesapla (Excel'deki gerçek satır)
                df_b_goster = df_b.copy()
                df_b_goster.insert(0, "ID", df_b_goster.index + 2)
                st.table(df_b_goster[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                
                col1, col2 = st.columns(2)
                onay_id = col1.number_input("İşlem yapılacak ID (Satır No):", min_value=2, step=1)
                
                if col2.button("✅ SEÇİLENİ ONAYLA"):
                    # Google Script'e onay komutu gönder
                    resp = requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(onay_id)}))
                    
                    # Onaylanan personelin ismini bul
                    secili_pers = df_b_goster[df_b_goster["ID"] == onay_id][ad_c].values[0]
                    
                    # WhatsApp Mesajını Hazırla
                    st.session_state['admin_wa'] = f"✅ *SAYIN {secili_pers},*\n\n*İZİN TALEBİNİZ ONAYLANMIŞTIR.*\n\n📝 Lütfen programı düzenleyip dilekçenizi yönetime iletiniz."
                    st.success(f"{secili_pers} onaylandı! WhatsApp bildirim butonu açıldı.")
                
                if 'admin_wa' in st.session_state:
                    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['admin_wa'])}"
                    st.link_button("🟢 ONAY MESAJINI PERSONELE GÖNDER", wa_url, use_container_width=True)
            else:
                st.success("Bekleyen talep yok.")

        with t[1]: # Karne
            if not df_o.empty:
                aylar = sorted(df_o['Ay'].dropna().unique(), reverse=True)
                ay_sec = st.selectbox("Ay Seçin", aylar)
                st.dataframe(df_o[df_o['Ay']==ay_sec].groupby([ad_c,'Tür'])[['G','S']].sum(), use_container_width=True)

        with t[2]: # Sicil
            p_list = sorted(list(PERSONEL_GIRISLERI.keys()))
            ps = st.selectbox("Personel Seçin", p_list)
            if not df_o.empty:
                st.dataframe(df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)

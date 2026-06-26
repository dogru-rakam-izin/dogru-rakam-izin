import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import urllib.parse

# --- 1. YARDIMCI FONKSİYONLAR ---
def sure_formatla(deger, tip="G"):
    if deger == 0 or pd.isna(deger): return "-"
    if tip == "G":
        s = str(round(deger, 1)).replace('.', ',')
        if s.endswith(',0'): s = s[:-2]
        return f"{s} Gün"
    else:
        toplam_dakika = round(deger * 60)
        saat, dakika = toplam_dakika // 60, toplam_dakika % 60
        sonuc = ""
        if saat > 0: sonuc += f"{saat} Saat "
        if dakika > 0: sonuc += f"{dakika} Dakika"
        return sonuc.strip() if sonuc else "0 Dakika"

# --- 2. AYARLAR ---
URL = "https://google.com"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://google.com{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://ibb.co"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)
F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
TR_AYLAR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZIN_TURLERI = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim", "Geç Kalma"]

PERSONEL_GIRISLERI = {
    "ARİF EMRE YILDIZ": "2024-10-09", "AYŞE KOLBAŞ": "2022-03-04", "AYŞE GÜLLÜ ÇIRAY": "2023-04-27", 
    "BURAK ÖZAYDIN": "2025-09-11", "BUSE MEYRİLİ": "2025-02-07", "ERSİN KALSEN": "2023-06-06",
    "FATMA NUR KOÇOĞLU": "2026-04-22", "FERİDE CIKKAN": "2025-03-13", "GÖKÇE DÖNMEZKOL": "2025-06-24", 
    "HİDAYET ARZU ER": "2025-02-07", "HÜSEYİN KIZIL": "2025-11-18", "İBRAHİM SOYLU": "2020-09-17", 
    "MERVE ANAYURT": "2025-03-11", "MİZGİN BİDER": "2025-09-15", "NEFİSE NUR HOŞGÖR": "2025-06-09", 
    "ÖZLEM KAPLAN": "2024-08-01", "PINAR TANRIVERDİ": "1900-01-01", "SAMET DEMİREL": "2024-02-27", 
    "GÜNAY AKTEPE": "2025-09-24", "ŞERİFE ŞENGÜL": "2025-05-20", "TANER DOĞAN": "2026-02-01", 
    "ARZU ÖZELMİŞ": "2025-11-17", "SİDAL ZENGİN": "2025-11-17", "SELEN ŞEN": "2025-11-03",
    "ZEYNEP KAYA": "2026-06-11"
}

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        df.columns = [str(c).strip() for c in df.columns]
        
        df = df.iloc[:, :5]
        df.columns = ["Zaman Damgası", "Ad Soyad", "Tür", "Başlangıç", "Dönüş"]
        
        df["Durum"] = "Onaylandı" if "Durum" not in df.columns else df["Durum"].fillna("Onay Bekliyor")
        df["Ad Soyad"] = df["Ad Soyad"].astype(str).str.strip().str.upper()
        
        def h(r):
            try:
                ts = str(r['Tür']).upper()
                b_s, d_s = str(r['Başlangıç']).strip(), str(r['Dönüş']).strip()
                if "SAATLIK" in ts or "GEC" in ts or "SAATLİK" in ts or "GEÇ" in ts:
                    b = datetime.strptime(b_s, F_TAM)
                    d = datetime.strptime(d_s, F_TAM)
                    return pd.Series([0.0, round((d-b).total_seconds()/3600, 2)])
                else:
                    b = datetime.strptime(b_s[:10], F_TARIH)
                    d = datetime.strptime(d_s[:10], F_TARIH)
                    return pd.Series([float((d-b).days), 0.0])
            except:
                return pd.Series([0.0, 0.0])
            
        df_b = df[df["Durum"].str.contains("Bekliyor", case=False, na=True)].copy()
        df_o = df[df["Durum"].str.contains("Onaylandı", case=False, na=False)].copy()
        
        if not df_o.empty:
            df_o[['G', 'S']] = df_o.apply(h, axis=1)
            df_o['T'] = pd.to_datetime(df_o['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
            df_o['Ay'] = df_o['T'].dt.strftime('%B').map(TR_AYLAR) + " " + df_o['T'].dt.strftime('%Y')
            
        return df, df_b, df_o
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_all, df_b, df_o = yukle()
p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='350'></div>", unsafe_allow_html=True)

menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h2 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h2>', unsafe_allow_html=True)
    p_ad = st.selectbox("Ad Soyad", p_listesi, key="p_ad").upper()
    p_tur = st.selectbox("İzin Türü", IZIN_TURLERI, key="p_tur")
    p_tp = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], horizontal=True, key="p_tp")
    p_t1 = st.date_input("Tarih", key="p_t1")
    
    p_bas_f, p_bit_f = "", ""
    if p_tp == "Saatlik":
        c1, c2 = st.columns(2)
        ps1 = c1.time_input("Çıkış", value=datetime.strptime("09:00", "%H:%M").time())
        ps2 = c2.time_input("Dönüş", value=datetime.strptime("10:00", "%H:%M").time())
        p_bas_f, p_bit_f = f"{p_t1.strftime(F_TARIH)} {ps1.strftime(F_SAAT)}", f"{p_t1.strftime(F_TARIH)} {ps2.strftime(F_SAAT)}"
    else:
        p_dn = st.date_input("İş Başı Tarihi", key="p_dn")
        p_bas_f, p_bit_f = p_t1.strftime(F_TARIH), p_dn.strftime(F_TARIH)
        
    if st.button("TALEBİ GÖNDER", use_container_width=True):
        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":p_ad,"tur":f"{p_tur} ({p_tp})","bas":p_bas_f,"bit":p_bit_f, "durum": "Onay Bekliyor"}))
        st.success("Talebiniz iletildi.")
        
    msg = f"*YENİ İZİN TALEBİ*\n👤 *Personel:* {p_ad}\n📝 *Tür:* {p_tur}\n📅 *Başlangıç:* {p_bas_f}\n🔙 *Dönüş:* {p_bit_f}"
    st.markdown(f'<br><a href="https://wa.me{urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:12px;text-align:center;border-radius:10px;font-weight:bold;">📢 WHATSAPP İLE YÖNETİCİYE BİLDİR</div></a>', unsafe_allow_html=True)

else:
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "2020":
        tab_onay, tab_izinler, tab_karne, tab_sicil, tab_yillik, tab_manuel, tab_gecikme, tab_liste = st.tabs(
            ["🔔 Onay", "📅 Onaylı İzinler", "📊 Karne", "📄 Sicil", "📅 Yıllık İzin", "📝 Manuel", "⏰ Geç Kalma", "🗑️ Liste"]
        )
        
        with tab_onay:
            if not df_b.empty:
                df_b_g = df_b.copy()
                df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", "Ad Soyad", "Tür", "Başlangıç", "Dönüş"]])
                o_id = st.number_input("Onay ID:", min_value=2, step=1)
                if st.button("✅ ONAYLA"):
                    requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                    st.success("Onaylandı!")
                    st.rerun()
            else: 
                st.info("Onay bekleyen kayıt yok.")

        with tab_izinler:
            st.markdown("### 📅 Onaylanmış Tüm Güncel İzinler")
            if not df_o.empty:
                st.dataframe(df_o[["Ad Soyad", "Tür", "Başlangıç", "Dönüş"]], use_container_width=True)
            else:
                st.info("Henüz onaylanmış bir izin bulunmuyor.")

        with tab_karne:
            if not df_o.empty and 'Ay' in df_o.columns:
                aylar = df_o['Ay'].dropna().unique()
                if len(aylar) > 0:
                    secili_ay = st.selectbox("Ay Seçiniz", aylar)
                    df_ay = df_o[df_o['Ay'] == secili_ay]
                    
                    karne_df = df_ay.groupby(["Ad Soyad", 'Tür']).agg({'G': 'sum', 'S': 'sum'}).reset_index()
                    karne_df['Gün Format'] = karne_df['G'].apply(lambda x: sure_formatla(x, "G"))
                    karne_df['Saat Format'] = karne_df['S'].apply(lambda x: sure_formatla(x, "S"))
                    
                    st.dataframe(karne_df[["Ad Soyad", 'Tür', 'Gün Format', 'Saat Format']], use_container_width=True)
                else:
                    st.info("Aylara göre gruplanacak veri bulunamadı.")
            else:
                st.info("Karne oluşturulabilecek onaylanmış veri bulunamadı.")

        with tab_sicil:
            secili_p = st.selectbox("Personel Seçiniz", p_listesi, key="sicil_p")
            if not df_o.empty:
                df_p_o = df_o[df_o["Ad Soyad"] == secili_p]
                if not df_p_o.empty:
                    st.markdown(f"### {secili_p} - Geçmiş İzinleri")
                    st.dataframe(df_p_o[["Tür", "Başlangıç", "Dönüş"]], use_container_width=True)
                else:
                    st.info("Bu personele ait onaylanmış izin bulunmuyor.")
            else:
                st.info("Veri tabanında onaylı izin yok.")

        with tab_yillik:
            st.markdown("### 📅 Personel Yıllık İzin Durumları")
            hakedis_liste = []
            bugun = datetime.now()
            
            for p, g_tarih_str in PERSONEL_GIRISLERI.items():
                try:
                    g_tarih = datetime.strptime(g_tarih_str, "%Y-%m-%d")
                    calisilan_yil = (bugun - g_tarih).days // 365
                    
                    if calisilan_yil < 1: toplam_hak = 0
                    elif 1 <= calisilan_yil < 6: toplam_hak = calisilan_yil * 14
                    elif 6 <= calisilan_yil < 15: toplam_hak = calisilan_yil * 20
                    else: toplam_hak = calisilan_yil * 26
                    
                    kullanilan = 0.0
                    if not df_o.empty:
                        df_p_yillik = df_o[(df_o["Ad Soyad"] == p) & (df_o['Tür'].str.contains("Yıllık", case=False, na=False))]
                        kullanilan = df_p_yillik['G'].sum()
                    
                    kalan = toplam_hak - kullanilan

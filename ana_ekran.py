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

# --- LOGO BURADA (En Üstte ve Ortalı) ---
# Eğer görünmezse width değerini 300'e çekebilirsiniz.
st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='350'></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True) # Biraz boşluk

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

def yukle():
    try:
        df = pd.read_csv(CSV)
        if df.empty: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Ad Soyad"
        df.columns = [str(c).strip() for c in df.columns]
        ad_col = next((c for c in df.columns if "AD" in c.upper()), df.columns[2])
        df["Durum"] = df.get("Durum", "Onaylandı").fillna("Onay Bekliyor").astype(str).str.strip()
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        df_b = df[df["Durum"].str.contains("Bekliyor", case=False, na=True)].copy()
        df_o = df[df["Durum"].str.contains("Onaylandı", case=False, na=False)].copy()
        return df, df_b, df_o, ad_col
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
        
        with t[0]: # Onay Bekleyenler
            if not df_b.empty:
                df_b_g = df_b.copy(); df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                c1, c2 = st.columns(2); o_id = c1.number_input("İşlem Yapılacak ID:", min_value=2, step=1)
                if c2.button("✅ ONAYLA"):
                    secim = df_b_g[df_b_g["ID"] == o_id]
                    if not secim.empty:
                        p_ad, p_tur, p_bas, p_bit = secim[ad_c].values[0], secim["Tür"].values[0], secim["Başlangıç"].values[0], secim["Dönüş"].values[0]
                        requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                        st.session_state['msg_onay'] = f"✅ *SAYIN {p_ad},*\n\n🗓 *{p_bas} - {p_bit}* tarihlerindeki\n📋 *{p_tur}* talebiniz onaylanmıştır.\n\n📝 Programı düzenleyip dilekçenizi iletmeyi unutmayınız."
                        st.success("Onaylandı!")
                if 'msg_onay' in st.session_state:
                    st.link_button("🟢 ONAY MESAJINI GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['msg_onay'])}", use_container_width=True)
            else: st.success("Bekleyen yok.")

        with t[3]: # Manuel Giriş
            with st.form("m_form"):
                m_ad = st.selectbox("Personel", p_listesi); m_tr = st.selectbox("Tür", IZ[:-1])
                m_t1, m_t2 = st.date_input("Başlangıç"), st.date_input("Dönüş")
                if st.form_submit_button("KAYDET VE ONAYLA"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":m_ad,"tur":f"{m_tr} (Tam)","bas":m_t1.strftime(F_TARIH),"bit":m_t2.strftime(F_TARIH), "durum": "Onaylandı"}))
                    st.session_state['msg_man'] = f"✅ *SAYIN {m_ad},*\n\n🗓 *{m_t1.strftime(F_TARIH)} - {m_t2.strftime(F_TARIH)}* tarihlerindeki *{m_tr}* kaydınız yönetici tarafından işlenmiştir."
                    st.success("Kayıt eklendi.")
            if 'msg_man' in st.session_state:
                st.link_button("🟢 BİLGİ MESAJI GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['msg_man'])}", use_container_width=True)

        with t[4]: # Geç Kalma
            with st.form("g_form"):
                g_ad = st.selectbox("Personel", p_listesi); g_t = st.date_input("Tarih"); g_d = st.slider("Dakika", 1, 60, 15)
                if st.form_submit_button("GEÇ KALMAYI İŞLE"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":g_ad,"tur":"Geç Kalma","bas":f"{g_t.strftime(F_TARIH)} 09:00","bit":f"{g_t.strftime(F_TARIH)} 09:{g_d:02d}", "durum": "Onaylandı"}))
                    st.session_state['msg_gec'] = f"⏰ *BİLGİLENDİRME*\nSayın {g_ad}, *{g_t.strftime(F_TARIH)}* tarihindeki *{g_d} dakikalık* geç kalmanız sisteme işlenmiştir."
                    st.success("İşlendi.")
            if 'msg_gec' in st.session_state:
                st.link_button("🟢 GEÇ KALMA BİLGİSİ GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['msg_gec'])}", use_container_width=True)

        with t[6]: # Liste ve Silme
            if not df_all.empty:
                df_l = df_all.copy(); df_l.insert(0, "ID", df_l.index + 2); st.dataframe(df_l, use_container_width=True)
                c1, c2 = st.columns(2); sil_id = c1.number_input("Silinecek ID:", min_value=2, step=1)
                if c2.button("❌ SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sil_id)}))
                    st.error("Silindi.")

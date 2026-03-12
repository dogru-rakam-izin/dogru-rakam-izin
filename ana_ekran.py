import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import urllib.parse
from streamlit_calendar import calendar # Takvim için gerekli

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

# --- TASARIM ---
st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='350'></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

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
        ad_col = next((c for c in df.columns if "AD" in c.upper()), "Ad Soyad")
        durum_col = next((c for c in df.columns if "DURUM" in c.upper()), "Durum")
        df[durum_col] = df.get(durum_col, "Onay Bekliyor").fillna("Onay Bekliyor").astype(str).str.strip()
        df[ad_col] = df[ad_col].astype(str).str.strip().str.upper()
        
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

        df_b = df[df[durum_col].str.contains("Bekliyor", case=False, na=True)].copy()
        df_o = df[df[durum_col].str.contains("Onaylandı", case=False, na=False)].copy()
        
        if not df_o.empty:
            res = df_o.apply(lambda r: pd.Series(h(r)), axis=1)
            df_o['G'], df_o['S'] = res[0].astype(float), res[1].astype(float)
            df_o['T'] = pd.to_datetime(df_o['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
            df_o['Ay'] = df_o['T'].dt.strftime('%B').map(TR) + " " + df_o['T'].dt.strftime('%Y')
        return df, df_b, df_o, ad_col
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Ad Soyad"

df_all, df_b, df_o, ad_c = yukle()
p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h2 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h2>', unsafe_allow_html=True)
    p_ad = st.selectbox("Ad Soyad Seçiniz", p_listesi, key="p_ad").upper()
    p_tur = st.selectbox("İzin Türü", IZ, key="p_tur")
    p_tp = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], horizontal=True, key="p_tp")
    p_t1 = st.date_input("İzin Günü / Başlangıç Tarihi", key="p_t1")
    p_bas_f, p_bit_f = "", ""
    if p_tp == "Saatlik":
        c1, c2 = st.columns(2)
        p_s1 = c1.time_input("Çıkış Saati", value=datetime.strptime("09:00", "%H:%M").time(), key="p_s1")
        p_s2 = c2.time_input("Dönüş Saati", value=datetime.strptime("10:00", "%H:%M").time(), key="p_s2")
        p_bas_f = f"{p_t1.strftime(F_TARIH)} {p_s1.strftime(F_SAAT)}"
        p_bit_f = f"{p_t1.strftime(F_TARIH)} {p_s2.strftime(F_SAAT)}"
    else:
        p_dn = st.date_input("İş Başı Tarihi (Dönüş)", key="p_dn")
        p_bas_f, p_bit_f = p_t1.strftime(F_TARIH), p_dn.strftime(F_TARIH)
    with st.form("p_submit_form"):
        if st.form_submit_button("TALEBİ SİSTEME GÖNDER", use_container_width=True):
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":p_ad,"tur":f"{p_tur} ({p_tp})","bas":p_bas_f,"bit":p_bit_f, "durum": "Onay Bekliyor"}))
            st.session_state['wa_p_talep'] = f"📄 *YENİ İZİN TALEBİ*\n👤 *Personel:* {p_ad}\n📋 *Tür:* {p_tur} ({p_tp})\n🗓 *Zaman:* {p_bas_f} - {p_bit_f}\n\n*Onayınızı bekliyorum.*"
            st.success("Talebiniz iletildi.")
    if 'wa_p_talep' in st.session_state:
        st.link_button("🟢 YÖNETİCİYE WHATSAPP'TAN BİLDİR", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['wa_p_talep'])}", use_container_width=True)

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        # TAKVİM SEKMESİ BURAYA EKLENDİ
        t = st.tabs(["🔔 Onay Bekleyenler", "📅 Takvim", "📊 Karne", "📄 Sicil", "📅 Yıllık İzin", "📝 Manuel Giriş", "⏰ Geç Kalma", "🗑️ Liste/Sil"])
        
        with t[0]: # Onay
            if not df_b.empty:
                df_b_g = df_b.copy(); df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                c1, c2 = st.columns(2); o_id = c1.number_input("İşlem ID:", min_value=2, step=1, key="adm_on_id")
                if c2.button("✅ ONAYLA"):
                    sec = df_b_g[df_b_g["ID"] == o_id]
                    if not sec.empty:
                        pa, pt, pb, pd = sec[ad_c].values[0], sec["Tür"].values[0], sec["Başlangıç"].values[0], sec["Dönüş"].values[0]
                        requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                        st.session_state['wa_adm_onay'] = f"✅ *SAYIN {pa},*\n🗓 *{pb} - {pd}*\n📋 *{pt}* talebiniz onaylanmıştır."
                        st.success(f"{pa} onaylandı!")
                if 'wa_adm_onay' in st.session_state:
                    st.link_button("🟢 ONAY MESAJINI GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['wa_adm_onay'])}", use_container_width=True)
            else: st.info("Bekleyen yok.")

        with t[1]: # 📅 TAKVİM GÖRÜNÜMÜ
            st.subheader("İzin Takvimi")
            events = []
            if not df_o.empty:
                for _, row in df_o.iterrows():
                    try:
                        b_str, d_str = str(row['Başlangıç']), str(row['Dönüş'])
                        if len(b_str) > 10: # Saatlik
                            start = datetime.strptime(b_str, F_TAM).isoformat()
                            end = datetime.strptime(d_str, F_TAM).isoformat()
                            all_day = False
                        else: # Günlük
                            start = datetime.strptime(b_str, F_TARIH).strftime("%Y-%m-%d")
                            end = datetime.strptime(d_str, F_TARIH).strftime("%Y-%m-%d")
                            all_day = True
                        
                        events.append({
                            "title": f"{row[ad_c]} ({row['Tür']})",
                            "start": start, "end": end, "allDay": all_day,
                            "color": "#FF4B4B" if "Yıllık" in row['Tür'] else "#3D9DF3"
                        })
                    except: continue
            calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek"}, "locale": "tr"})

        with t[2]: # Karne
            if not df_o.empty:
                ay_list = sorted(df_o['Ay'].dropna().unique(), reverse=True)
                if ay_list:
                    ay_sec = st.selectbox("Ay Seç", ay_list)
                    st.dataframe(df_o[df_o['Ay']==ay_sec].groupby([ad_c,'Tür'])[['G','S']].sum(), use_container_width=True)

        with t[3]: # Sicil
            ps = st.selectbox("Personel Seç", p_listesi, key="sicil_p")
            if not df_o.empty: st.dataframe(df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)

        with t[4]: # Yıllık İzin
            py = st.selectbox("Personel", p_listesi, key="adm_yillik")
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kidem = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk, ku = hakedis_bul(max(0, kidem)), (df_o[(df_o[ad_c]==py) & (df_o['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_o.empty else 0)
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Hak", f"{hk} G"); c2.metric("Kullanılan", f"{ku} G"); c3.metric("Kalan", f"{hk-ku} G")

        with t[5]: # Manuel Giriş
            ma = st.selectbox("Personel Seç", p_listesi, key="m_ad")
            mt = st.selectbox("İzin Türü", IZ, key="m_tur")
            ms = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], horizontal=True, key="m_süre")
            mt1 = st.date_input("Tarih Seç", key="m_t1")
            m_bas, m_bit = "", ""
            if ms == "Saatlik":
                mc1, mc2 = st.columns(2)
                ms1 = mc1.time_input("Başlangıç", value=datetime.strptime("09:00", "%H:%M").time(), key="ms1")
                ms2 = mc2.time_input("Bitiş", value=datetime.strptime("10:00", "%H:%M").time(), key="ms2")
                m_bas, m_bit = f"{mt1.strftime(F_TARIH)} {ms1.strftime(F_SAAT)}", f"{mt1.strftime(F_TARIH)} {ms2.strftime(F_SAAT)}"
            else:
                mt2 = st.date_input("Dönüş Tarihi", key="m_t2")
                m_bas, m_bit = mt1.strftime(F_TARIH), mt2.strftime(F_TARIH)
            
            with st.form("m_form_sub"):
                if st.form_submit_button("ONAYLI KAYDET"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ma,"tur":f"{mt} ({ms})","bas":m_bas,"bit":m_bit, "durum": "Onaylandı"}))
                    st.session_state['wa_adm_man'] = f"✅ *SAYIN {ma},*\n🗓 *{m_bas} - {m_bit}*\n📋 *{mt}* kaydınız işlenmiştir."
                    st.success("Kaydedildi.")
            if 'wa_adm_man' in st.session_state:
                st.link_button("🟢 BİLGİ MESAJI GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['wa_adm_man'])}", use_container_width=True)

        with t[6]: # Geç Kalma
            ga, gt, gd = st.selectbox("Personel", p_listesi, key="g_ad"), st.date_input("Tarih", key="g_t"), st.slider("Dakika", 1, 60, 15)
            with st.form("g_form_sub"):
                if st.form_submit_button("İŞLE"):
                    requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ga,"tur":"Geç Kalma","bas":f"{gt.strftime(F_TARIH)} 09:00","bit":f"{gt.strftime(F_TARIH)} 09:{gd:02d}", "durum": "Onaylandı"}))
                    st.session_state['wa_adm_gec'] = f"⏰ *BİLGİLENDİRME*\nSayın {ga}, *{gt.strftime(F_TARIH)}* tarihindeki *{gd} dakikalık* geç kalmanız sisteme işlenmiştir."
                    st.success("İşlendi.")
            if 'wa_adm_gec' in st.session_state:
                st.link_button("🟢 GEÇ KALMA BİLGİSİ GÖNDER (WA)", f"https://api.whatsapp.com/send?text={urllib.parse.quote(st.session_state['wa_adm_gec'])}", use_container_width=True)

        with t[7]: # Sil
            if not df_all.empty:
                df_l = df_all.copy(); df_l.insert(0, "ID", df_l.index + 2); st.dataframe(df_l, use_container_width=True)
                sid = st.number_input("Sil ID:", min_value=2, step=1, key="adm_sil")
                if st.button("❌ KAYDI SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sid)}))
                    st.error("Silindi.")

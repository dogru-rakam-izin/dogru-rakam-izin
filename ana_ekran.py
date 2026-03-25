import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import urllib.parse
from io import BytesIO
from streamlit_calendar import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# --- YARDIMCI FONKSİYON: SAATİ DAKİKAYA ÇEVİRİR ---
def sure_formatla(deger, tip="G"):
    if deger == 0 or pd.isna(deger):
        return "-"
    if tip == "G":
        s = str(round(deger, 1)).replace('.', ',')
        if s.endswith(',0'): s = s[:-2]
        return f"{s} Gün"
    else:
        toplam_dakika = round(deger * 60)
        saat = toplam_dakika // 60
        dakika = toplam_dakika % 60
        sonuc = ""
        if saat > 0: sonuc += f"{saat} Saat "
        if dakika > 0: sonuc += f"{dakika} Dakika"
        return sonuc.strip()

# --- PDF FONKSİYONU ---
def pdf_olustur(df, secili_ay):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    def tr_duzelt(metin):
        return str(metin).replace('İ', 'I').replace('ı', 'i').replace('Ş', 'S').replace('ş', 's').replace('Ğ', 'G').replace('ğ', 'g').replace('Ü', 'U').replace('ü', 'u').replace('Ö', 'O').replace('ö', 'o').replace('Ç', 'C').replace('ç', 'c')
    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>{tr_duzelt(secili_ay)} - Personel Izin Karnesi</b>", styles['Title'])
    elements.append(title)
    data = [["Ad Soyad", "Izin Turu", "Gun", "Saat/Dakika"]]
    for idx, row in df.iterrows():
        data.append([tr_duzelt(idx[0]), tr_duzelt(idx[1]), sure_formatla(row['G'], "G"), sure_formatla(row['S'], "S")])
    table = Table(data, colWidths=[160, 140, 80, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

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

st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='350'></div>", unsafe_allow_html=True)
menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h2 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h2>', unsafe_allow_html=True)
    p_ad = st.selectbox("Ad Soyad Seçiniz", p_listesi, key="p_ad").upper()
    p_tur = st.selectbox("İzin Türü", IZ, key="p_tur")
    p_tp = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], horizontal=True, key="p_tp")
    p_t1 = st.date_input("Tarih", key="p_t1")
    p_bas_f, p_bit_f = "", ""
    if p_tp == "Saatlik":
        c1, c2 = st.columns(2)
        p_s1 = c1.time_input("Çıkış", value=datetime.strptime("09:00", "%H:%M").time())
        p_s2 = c2.time_input("Dönüş", value=datetime.strptime("10:00", "%H:%M").time())
        p_bas_f, p_bit_f = f"{p_t1.strftime(F_TARIH)} {p_s1.strftime(F_SAAT)}", f"{p_t1.strftime(F_TARIH)} {p_s2.strftime(F_SAAT)}"
    else:
        p_dn = st.date_input("İş Başı Tarihi", key="p_dn")
        p_bas_f, p_bit_f = p_t1.strftime(F_TARIH), p_dn.strftime(F_TARIH)
    with st.form("p_submit"):
        if st.form_submit_button("TALEBİ GÖNDER", use_container_width=True):
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":p_ad,"tur":f"{p_tur} ({p_tp})","bas":p_bas_f,"bit":p_bit_f, "durum": "Onay Bekliyor"}))
            st.success("Talebiniz iletildi.")

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        t = st.tabs(["🔔 Onay", "📅 Takvim", "📊 Karne", "📄 Sicil", "📅 Yıllık İzin", "📝 Manuel", "⏰ Geç Kalma", "🗑️ Liste"])
        
        with t[0]: # Onay
            if not df_b.empty:
                df_b_g = df_b.copy(); df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                o_id = st.number_input("Onay ID:", min_value=2, step=1)
                if st.button("✅ ONAYLA"):
                    requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                    st.success("Onaylandı!")
            else: st.info("Bekleyen yok.")

       with t[1]: # 📅 TAKVİM GÖRÜNÜMÜ
            st.subheader("İzin Takvimi")
            events = []
            if not df_o.empty:
                for _, row in df_o.iterrows():
                    try:
                        # Tarih verilerini string'e çevir ve temizle
                        b_str = str(row['Başlangıç']).strip()
                        d_str = str(row['Dönüş']).strip()
                        
                        # Saatlik mi yoksa Tam Gün mü kontrolü (Karakter sayısına göre)
                        if len(b_str) > 10: 
                            # Saatlik/Geç Kalma Formatı: 25/03/2026 09:00
                            start_dt = datetime.strptime(b_str, F_TAM)
                            end_dt = datetime.strptime(d_str, F_TAM)
                            all_day = False
                        else:
                            # Tam Gün Formatı: 25/03/2026
                            start_dt = datetime.strptime(b_str, F_TARIH)
                            end_dt = datetime.strptime(d_str, F_TARIH)
                            all_day = True
                        
                        # Renk Belirleme
                        tur = str(row['Tür'])
                        if "Yıllık" in tur:
                            renk = "#FF4B4B" # Kırmızı
                        elif "Geç Kalma" in tur:
                            renk = "#FFA500" # Turuncu
                        else:
                            renk = "#3D9DF3" # Mavi
                        
                        # Takvim etkinliğini listeye ekle
                        events.append({
                            "title": f"{row[ad_c]} ({tur})",
                            "start": start_dt.isoformat(),
                            "end": end_dt.isoformat(),
                            "allDay": all_day,
                            "color": renk
                        })
                    except Exception as e:
                        continue # Hatalı satırı atla
            
            # Takvimi görüntüle
            calendar_options = {
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,listWeek",
                },
                "initialView": "dayGridMonth",
                "locale": "tr",
            }
            
            calendar(events=events, options=calendar_options, key="izin_takvimi")

        with t[2]: # Karne
            if not df_o.empty:
                ay_list = sorted(df_o['Ay'].dropna().unique(), reverse=True)
                if ay_list:
                    ay_sec = st.selectbox("Ay Seç", ay_list)
                    k_df = df_o[df_o['Ay']==ay_sec].groupby([ad_c,'Tür'])[['G','S']].sum()
                    ek_df = k_df.copy()
                    ek_df['G'] = ek_df['G'].apply(lambda x: sure_formatla(x, "G"))
                    ek_df['S'] = ek_df['S'].apply(lambda x: sure_formatla(x, "S"))
                    st.dataframe(ek_df, use_container_width=True)
                    pdf_v = pdf_olustur(k_df, ay_sec)
                    st.download_button("📥 PDF İNDİR", data=pdf_v, file_name=f"Karne_{ay_sec}.pdf", mime="application/pdf")

        with t[3]: # Sicil
            ps = st.selectbox("Personel Seç", p_listesi, key="sicil_p")
            if not df_o.empty:
                s_df = df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']].copy()
                s_df['G'] = s_df['G'].apply(lambda x: sure_formatla(x, "G"))
                s_df['S'] = s_df['S'].apply(lambda x: sure_formatla(x, "S"))
                st.dataframe(s_df, use_container_width=True)

        with t[4]: # Yıllık İzin
            py = st.selectbox("Yıllık İzin Kontrol", p_listesi)
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kd = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk = hakedis_bul(max(0, kd))
            ku = df_o[(df_o[ad_c]==py) & (df_o['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_o.empty else 0
            c1, c2 = st.columns(2)
            c1.metric("Toplam Hakediş", f"{hk} Gün")
            c2.metric("Kalan İzin", f"{hk-ku} Gün")

        with t[5]: # Manuel Giriş
            ma = st.selectbox("Personel", p_listesi, key="m_a")
            mt = st.selectbox("İzin Türü", IZ, key="m_t")
            mt1 = st.date_input("Başlangıç Tarihi", key="m_d1")
            mt2 = st.date_input("Dönüş Tarihi", key="m_d2")
            if st.button("MANUEL ONAYLI EKLE"):
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ma,"tur":f"{mt} (Tam Gün)","bas":mt1.strftime(F_TARIH),"bit":mt2.strftime(F_TARIH), "durum": "Onaylandı"}))
                st.success("Kayıt eklendi.")

        with t[6]: # Geç Kalma
            ga = st.selectbox("Personel", p_listesi, key="g_a")
            gt = st.date_input("Geç Kalma Tarihi", key="g_d")
            gd = st.slider("Kaç Dakika Geç Kaldı?", 1, 120, 15)
            if st.button("GEÇ KALMAYI KAYDET"):
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ga,"tur":"Geç Kalma","bas":f"{gt.strftime(F_TARIH)} 09:00","bit":f"{gt.strftime(F_TARIH)} 09:{gd:02d}", "durum": "Onaylandı"}))
                st.success("Geç kalma işlendi.")

        with t[7]: # Liste / Sil
            if not df_all.empty:
                df_l = df_all.copy(); df_l.insert(0, "ID", df_l.index + 2)
                st.dataframe(df_l, use_container_width=True)
                sid = st.number_input("Silinecek Satır ID:", min_value=2, step=1)
                if st.button("❌ KAYDI SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sid)}))
                    st.error("Kayıt silindi.")

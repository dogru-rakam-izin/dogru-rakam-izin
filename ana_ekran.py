import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from io import BytesIO
from streamlit_calendar import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import urllib.parse

# --- 1. YARDIMCI FONKSİYONLAR ---
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

def pdf_olustur(df, secili_ay):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    def tr(metin):
        return str(metin).replace('İ', 'I').replace('ı', 'i').replace('Ş', 'S').replace('ş', 's').replace('Ğ', 'G').replace('ğ', 'g').replace('Ü', 'U').replace('ü', 'u').replace('Ö', 'O').replace('ö', 'o').replace('Ç', 'C').replace('ç', 'c')
    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>{tr(secili_ay)} - Personel Izin Karnesi</b>", styles['Title'])
    elements.append(title)
    data = [["Ad Soyad", "Izin Turu", "Gun", "Saat/Dakika"]]
    for idx, row in df.iterrows():
        data.append([tr(idx[0]), tr(idx[1]), sure_formatla(row['G'], "G"), sure_formatla(row['S'], "S")])
    table = Table(data, colWidths=[160, 140, 80, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()

# --- 2. AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

F_TARIH, F_SAAT, F_TAM = '%d/%m/%Y', '%H:%M', '%d/%m/%Y %H:%M'
TR_AYLAR = {"January":"Ocak","February":"Şubat","March":"Mart","April":"Nisan","May":"Mayıs","June":"Haziran","July":"Temmuz","August":"Ağustos","September":"Eylül","October":"Ekim","November":"Kasım","December":"Aralık"}
IZIN_TURLERI = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim", "Geç Kalma"]

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
                if any(x in ts for x in ["Saatlik", "Geç Kalma"]):
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
            df_o['Ay'] = df_o['T'].dt.strftime('%B').map(TR_AYLAR) + " " + df_o['T'].dt.strftime('%Y')
        return df, df_b, df_o, ad_col
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), "Ad Soyad"

df_all, df_b, df_o, ad_c = yukle()
p_listesi = sorted(list(PERSONEL_GIRISLERI.keys()))

st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='350'></div>", unsafe_allow_html=True)

# --- 3. ANA MANTIK ---
menu = st.sidebar.radio("📌 MENÜ", ["👤 PERSONEL GİRİŞİ", "🔐 YÖNETİCİ PANELİ"])

if menu == "👤 PERSONEL GİRİŞİ":
    st.markdown('<h2 style="text-align:center; color:#CC0000;">İZİN TALEP FORMU</h2>', unsafe_allow_html=True)
    p_ad = st.selectbox("Ad Soyad Seçiniz", p_listesi, key="p_ad").upper()
    p_tur = st.selectbox("İzin Türü", IZIN_TURLERI, key="p_tur")
    p_tp = st.radio("Süre Tipi", ["Tam Gün", "Saatlik"], horizontal=True, key="p_tp")
    p_t1 = st.date_input("Tarih", key="p_t1")
    
    p_bas_f, p_bit_f = "", ""
    if p_tp == "Saatlik":
        c1, c2 = st.columns(2)
        p_s1 = c1.time_input("Çıkış", value=datetime.strptime("09:00", "%H:%M").time())
        p_s2 = c2.time_input("Dönüş", value=datetime.strptime("10:00", "%H:%M").time())
        p_bas_f = f"{p_t1.strftime(F_TARIH)} {p_s1.strftime(F_SAAT)}"
        p_bit_f = f"{p_t1.strftime(F_TARIH)} {p_s2.strftime(F_SAAT)}"
    else:
        p_dn = st.date_input("İş Başı Tarihi", key="p_dn")
        p_bas_f, p_bit_f = p_t1.strftime(F_TARIH), p_dn.strftime(F_TARIH)
        
    if st.button("TALEBİ GÖNDER", use_container_width=True):
        requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":p_ad,"tur":f"{p_tur} ({p_tp})","bas":p_bas_f,"bit":p_bit_f, "durum": "Onay Bekliyor"}))
        st.success("Talebiniz başarıyla iletildi.")
        
    # WHATSAPP BUTONU (HER ZAMAN GÖRÜNÜR)
    mesaj = f"*YENİ İZİN TALEBİ*\n👤 *Personel:* {p_ad}\n📝 *Tür:* {p_tur}\n📅 *Başlangıç:* {p_bas_f}\n🔙 *Dönüş:* {p_bit_f}"
    wp_url = f"https://wa.me/?text={urllib.parse.quote(mesaj)}"
    st.markdown(f'<br><a href="{wp_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:12px;text-align:center;border-radius:10px;font-weight:bold;font-size:16px;">📢 WHATSAPP İLE YÖNETİCİYE BİLDİR</div></a>', unsafe_allow_html=True)

else:
    sifre = st.sidebar.text_input("Yönetici Şifresi", type="password")
    if sifre == "2020":
        t = st.tabs(["🔔 Onay", "📅 Takvim", "📊 Karne", "📄 Sicil", "📅 Yıllık İzin", "📝 Manuel", "⏰ Geç Kalma", "🗑️ Liste"])
        
        with t[0]: # Onay
            if not df_b.empty:
                df_b_g = df_b.copy()
                df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                o_id = st.number_input("Onay ID:", min_value=2, step=1)
                if st.button("✅ ONAYLA"):
                    requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                    st.success("Onaylandı!")
                    st.rerun()
            else: st.info("Bekleyen onay yok.")

        with t[1]: # Takvim (GÜVENLİ YÜKLEME)
            st.subheader("İzin Takvimi")
            evs = []
            if not df_o.empty:
                for _, r in df_o.iterrows():
                    try:
                        b_s, d_s = str(r['Başlangıç']).strip(), str(r['Dönüş']).strip()
                        is_all = len(b_s) <= 10
                        evs.append({
                            "title": f"{r[ad_c]} ({r['Tür']})",
                            "start": datetime.strptime(b_s, F_TARIH if is_all else F_TAM).isoformat(),
                            "end": datetime.strptime(d_s, F_TARIH if is_all else F_TAM).isoformat(),
                            "allDay": is_all,
                            "color": "#FF4B4B" if "Yıllık" in str(r['Tür']) else "#FFA500" if "Geç Kalma" in str(r['Tür']) else "#3D9DF3"
                        })
                    except: continue
            calendar(events=evs, options={"locale":"tr", "headerToolbar":{"left":"prev,next today","center":"title","right":"dayGridMonth,timeGridWeek"}}, key="takvim_v4")

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
            ps = st.selectbox("Personel Seç", p_listesi, key="s_p")
            if not df_o.empty:
                s_df = df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']].copy()
                s_df['G'] = s_df['G'].apply(lambda x: sure_formatla(x, "G"))
                s_df['S'] = s_df['S'].apply(lambda x: sure_formatla(x, "S"))
                st.dataframe(s_df, use_container_width=True)

        with t[4]: # Yıllık İzin
            py = st.selectbox("Personel", p_listesi, key="y_p")
            gt_s = PERSONEL_GIRISLERI.get(py, "2024-01-01")
            gt = datetime.strptime(gt_s, "%Y-%m-%d")
            kd = datetime.now().year - gt.year - ((datetime.now().month, datetime.now().day) < (gt.month, gt.day))
            hk = hakedis_bul(max(0, kd))
            ku = df_o[(df_o[ad_c]==py) & (df_o['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_o.empty else 0
            st.metric("Kalan İzin", f"{hk-ku} Gün")

        with t[5]: # Manuel (Saatli İzin Desteği Mevcut)
            ma = st.selectbox("Personel", p_listesi, key="m_a")
            mt = st.selectbox("İzin Türü", IZIN_TURLERI, key="m_t")
            m_tip = st.radio("Tip", ["Tam Gün", "Saatlik"], horizontal=True, key="m_tip")
            mt1 = st.date_input("Başlangıç Tarihi", key="m_d1")
            
            m_bas, m_bit = "", ""
            if m_tip == "Saatlik":
                c1, c2 = st.columns(2)

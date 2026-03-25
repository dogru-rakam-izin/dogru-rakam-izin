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

# --- AYARLAR ---
URL = "https://script.google.com/macros/s/AKfycbwp1CNfE5Lp9kKbFF99MvwX3PAwO2Y85NAWu5SCdj5TnhNnan7r-VBDEW9ONF9OqkuV/exec"
S_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
CSV = f"https://docs.google.com/spreadsheets/d/{S_ID}/gviz/tq?tqx=out:csv"
LOGO_URL = "https://i.ibb.co/8LG243NJ/LOGO.png"

st.set_page_config(page_title="Doğru Rakam İzin Paneli", layout="wide", page_icon=LOGO_URL)

# --- PDF OLUŞTURMA FONKSİYONU ---
def pdf_olustur(df, secili_ay):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Başlık
    title = Paragraph(f"<b>{secili_ay} - Personel Izin Karnesi</b>", styles['Title'])
    elements.append(title)
    
    data = [["Ad Soyad", "Izin Turu", "Gun", "Saat"]]
    for idx, row in df.iterrows():
        # Değer 0'dan büyükse yanına birim ekle, 0 ise boş bırak veya - koy
        g_deger = float(row['G'])
        s_deger = float(row['S'])
        
        gun_metin = f"{str(round(g_deger, 1)).replace('.', ',')} Gun" if g_deger > 0 else "-"
        saat_metin = f"{str(round(s_deger, 2)).replace('.', ',')} Saat" if s_deger > 0 else "-"
        
        data.append([idx[0], idx[1], gun_metin, saat_metin])
    
    table = Table(data, colWidths=[180, 150, 70, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
    styles = getSampleStyleSheet()
    # Başlık
    title_text = f"<b>{secili_ay} - Personel Izin Karnesi</b>"
    title = Paragraph(tr_duzelt(title_text), styles['Title'])
    elements.append(title)
    
    # Tablo verisi hazırlama
    data = [["Ad Soyad", "Izin Turu", "Gun", "Saat"]]
    for idx, row in df.iterrows():
        # Sayıları virgüllü formata çevirme (Örn: 0.67 -> 0,67)
        gun_v = str(row['G']).replace('.', ',')
        saat_v = str(row['S']).replace('.', ',')
        
        data.append([
            tr_duzelt(idx[0]), # Personel Adı
            tr_duzelt(idx[1]), # İzin Türü
            gun_v, 
            saat_v
        ])
    
    table = Table(data, colWidths=[180, 150, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()

# --- TASARIM VE AYARLAR ---
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
    p_t1 = st.date_input("Başlangıç Tarihi", key="p_t1")
    p_bas_f, p_bit_f = "", ""
    if p_tp == "Saatlik":
        c1, c2 = st.columns(2)
        p_s1 = c1.time_input("Çıkış", value=datetime.strptime("09:00", "%H:%M").time(), key="p_s1")
        p_s2 = c2.time_input("Dönüş", value=datetime.strptime("10:00", "%H:%M").time(), key="p_s2")
        p_bas_f = f"{p_t1.strftime(F_TARIH)} {p_s1.strftime(F_SAAT)}"
        p_bit_f = f"{p_t1.strftime(F_TARIH)} {p_s2.strftime(F_SAAT)}"
    else:
        p_dn = st.date_input("İş Başı Tarihi", key="p_dn")
        p_bas_f, p_bit_f = p_t1.strftime(F_TARIH), p_dn.strftime(F_TARIH)
    with st.form("p_submit"):
        if st.form_submit_button("TALEBİ GÖNDER", use_container_width=True):
            requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":p_ad,"tur":f"{p_tur} ({p_tp})","bas":p_bas_f,"bit":p_bit_f, "durum": "Onay Bekliyor"}))
            st.success("İletildi.")

else:
    if st.sidebar.text_input("Şifre", type="password") == "2020":
        t = st.tabs(["🔔 Onay", "📅 Takvim", "📊 Karne", "📄 Sicil", "📅 Yıllık İzin", "📝 Manuel", "⏰ Geç Kalma", "🗑️ Liste"])
        
        with t[0]: # Onay
            if not df_b.empty:
                df_b_g = df_b.copy(); df_b_g.insert(0, "ID", df_b_g.index + 2)
                st.table(df_b_g[["ID", ad_c, "Tür", "Başlangıç", "Dönüş"]])
                o_id = st.number_input("İşlem ID:", min_value=2, step=1)
                if st.button("✅ ONAYLA"):
                    requests.post(URL, data=json.dumps({"islem": "onayla", "satir": int(o_id)}))
                    st.success("Onaylandı!")
            else: st.info("Bekleyen yok.")

        with t[1]: # Takvim (Renkli)
            events = []
            if not df_o.empty:
                for _, row in df_o.iterrows():
                    try:
                        b_str, d_str = str(row['Başlangıç']), str(row['Dönüş'])
                        all_day = len(b_str) <= 10
                        start = datetime.strptime(b_str, F_TARIH if all_day else F_TAM).isoformat()
                        end = datetime.strptime(d_str, F_TARIH if all_day else F_TAM).isoformat()
                        renk = "#FF4B4B" if "Yıllık" in row['Tür'] else "#FFA500" if "Geç Kalma" in row['Tür'] else "#3D9DF3"
                        events.append({"title": f"{row[ad_c]} ({row['Tür']})", "start": start, "end": end, "allDay": all_day, "color": renk})
                    except: continue
            calendar(events=events, options={"locale": "tr"})

       with t[2]: # Karne
            if not df_o.empty:
                ay_list = sorted(df_o['Ay'].dropna().unique(), reverse=True)
                if ay_list:
                    ay_sec = st.selectbox("Ay Seç", ay_list)
                    k_df = df_o[df_o['Ay']==ay_sec].groupby([ad_c,'Tür'])[['G','S']].sum()
                    
                    # --- EKRAN FORMATLAMA ---
                    ekran_df = k_df.copy()
                    ekran_df['G'] = ekran_df['G'].apply(lambda x: f"{str(round(x,1)).replace('.',',')} Gün" if x > 0 else "-")
                    ekran_df['S'] = ekran_df['S'].apply(lambda x: f"{str(round(x,2)).replace('.',',')} Saat" if x > 0 else "-")
                    
                    st.dataframe(ekran_df, use_container_width=True)
                    
                    # PDF İndirme
                    pdf = pdf_olustur(k_df, ay_sec)
                    st.download_button("📥 PDF OLARAK İNDİR", data=pdf, file_name=f"Karne_{ay_sec}.pdf", mime="application/pdf")

        with t[3]: # Sicil
            ps = st.selectbox("Personel", p_listesi)
            if not df_o.empty: st.dataframe(df_o[df_o[ad_c]==ps][['Başlangıç','Dönüş','Tür','G','S']], use_container_width=True)

        with t[4]: # Yıllık İzin
            py = st.selectbox("Personel Seç", p_listesi)
            gt = datetime.strptime(PERSONEL_GIRISLERI.get(py, "2024-01-01"), "%Y-%m-%d")
            kidem = datetime.now().year - gt.year
            hk, ku = hakedis_bul(kidem), (df_o[(df_o[ad_c]==py) & (df_o['Tür'].str.contains("Yıllık"))]['G'].sum() if not df_o.empty else 0)
            st.metric("Kalan İzin", f"{hk-ku} Gün")

        with t[5]: # Manuel
            ma = st.selectbox("Personel", p_listesi, key="m_a")
            mt = st.selectbox("Tür", IZ, key="m_t")
            mt1 = st.date_input("Tarih", key="m_d1")
            mt2 = st.date_input("Dönüş", key="m_d2")
            if st.button("KAYDET"):
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ma,"tur":f"{mt} (Tam Gün)","bas":mt1.strftime(F_TARIH),"bit":mt2.strftime(F_TARIH), "durum": "Onaylandı"}))
                st.success("Eklendi.")

        with t[6]: # Geç Kalma
            ga, gt, gd = st.selectbox("Personel", p_listesi, key="g_a"), st.date_input("Tarih", key="g_d"), st.slider("Dakika", 1, 60, 15)
            if st.button("İŞLE"):
                requests.post(URL, data=json.dumps({"tarih":datetime.now().strftime(F_TARIH),"ad":ga,"tur":"Geç Kalma","bas":f"{gt.strftime(F_TARIH)} 09:00","bit":f"{gt.strftime(F_TARIH)} 09:{gd:02d}", "durum": "Onaylandı"}))
                st.success("İşlendi.")

        with t[7]: # Liste/Sil
            if not df_all.empty:
                df_l = df_all.copy(); df_l.insert(0, "ID", df_l.index + 2); st.dataframe(df_l, use_container_width=True)
                sid = st.number_input("Silinecek ID:", min_value=2)
                if st.button("SİL"):
                    requests.post(URL, data=json.dumps({"islem": "sil", "satir": int(sid)}))
                    st.error("Silindi.")

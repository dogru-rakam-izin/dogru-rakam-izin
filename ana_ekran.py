import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- YAPILANDIRMA ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyz1FkOaVRpkSAQoJrhaZcXsu_qQuYN-Y18S-yQblLIUqGBlFgoryoNW4eLfw8d0DZ1/exec"
SHEET_ID = "1Ic8IMlsCZrCyUiTw6_aECivCa98Z32iNsHomq52g3CA"
SHEET_READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Doğru Rakam İzin Sistemi", layout="wide")

TR_AYLAR = {
    "January": "Ocak", "February": "Şubat", "March": "Mart", "April": "Nisan",
    "May": "Mayıs", "June": "Haziran", "July": "Temmuz", "August": "Ağustos",
    "September": "Eylül", "October": "Ekim", "November": "Kasım", "December": "Aralık"
}

IZIN_LISTESI = ["Yıllık İzin", "Mazeret İzni", "Sağlık Raporu", "Saatlik İzin", "Ücretsiz İzin", "Evlilik İzni", "Vefat İzni", "Babalık İzni", "Eğitim / Seminer"]

def verileri_yukle():
    try:
        df = pd.read_csv(SHEET_READ_URL)
        if df.empty: return pd.DataFrame()
        df.columns = [c.strip() for c in df.columns]
        def sure_ayristir(row):
            try:
                if "Saatlik" in str(row['Tür']):
                    fmt = "%d/%m/%Y %H:%M"
                    bas, bit = datetime.strptime(str(row['Başlangıç']), fmt), datetime.strptime(str(row['Dönüş']), fmt)
                    return 0, float(round((bit - bas).seconds / 3600, 1))
                else:
                    fmt = "%d/%m/%Y"
                    bas, bit = datetime.strptime(str(row['Başlangıç']), fmt), datetime.strptime(str(row['Dönüş']), fmt)
                    return int((bit - bas).days), 0
            except: return 0, 0
        df[['Gun_Deger', 'Saat_Deger']] = df.apply(lambda r: pd.Series(sure_ayristir(r)), axis=1)
        df['Tarih_Obj'] = pd.to_datetime(df['Başlangıç'].str[:10], dayfirst=True, errors='coerce')
        df['Ay_Ismi'] = df['Tarih_Obj'].dt.strftime('%B').map(TR_AYLAR) + " " + df['Tarih_Obj'].dt.strftime('%Y')
        return df
    except: return pd.DataFrame()

menu = st.sidebar.radio("MENÜ", ["⬇️ PERSONEL", "🔐 YÖNETİCİ"])

if menu == "⬇️ PERSONEL":
    st.title("🏢 DOĞRU RAKAM ÖZEL EĞİTİM")
    ad, tc = st.text_input("Ad Soyad"), st.text_input("TC", max_chars=11)
    tip = st.radio("Süre", ["Tam Gün", "Saatlik"], horizontal=True)
    with st.form("p_form"):
        f1, f2 = st.columns(2)
        with f1: tur, tar = st.selectbox("Tür", IZIN_LISTESI), st.date_input("Tarih")
        with f2:
            if tip == "Saatlik":
                s1, s2 = st.time_input("Çıkış"), st.time_input("Dönüş")
                bas_str, bit_str = f"{tar.strftime('%d/%m/%Y')} {s1.strftime('%H:%M')}", f"{tar.strftime('%d/%m/%Y')} {s2.strftime('%H:%M')}"
            else:
                don = st.date_input("İş Başı")
                bas_str, bit_str = tar.strftime('%d/%m/%Y'), don.strftime('%d/%m/%Y')
        if st.form_submit_button("GÖNDER"):
            if ad and tc:
                p_data = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": str(tc), "ad": ad, "brans": "Personel", "tur": f"{tur} ({tip})", "bas": bas_str, "bit": bit_str}
                requests.post(APPS_SCRIPT_URL, data=json.dumps(p_data))
                st.success("İletildi!"); st.balloons()

else:
    st.title("🔐 YÖNETİCİ PANELİ")
    sifre = st.sidebar.text_input("Şifre", type="password")
    if sifre == "1234":
        df = verileri_yukle()
        t1, t2 = st.tabs(["📊 Karne", "📝 Manuel Kayıt"])
        with t1:
            if not df.empty:
                aylar = sorted(df['Ay_Ismi'].dropna().unique(), reverse=True)
                sec_ay = st.selectbox("Ay", aylar)
                ay_df = df[df['Ay_Ismi'] == sec_ay].copy()
                karne = ay_df.groupby('Ad Soyad').agg({'Gun_Deger': 'sum', 'Saat_Deger': 'sum', 'Tür': 'count'})
                karne.columns = ['Gün', 'Saat', 'Adet']
                for c in ['Gün', 'Saat']: karne[c] = karne[c].apply(lambda x: int(x) if x == int(x) else round(x, 1))
                st.table(karne)
                st.download_button("📥 Karneyi İndir", karne.to_csv().encode('utf-8-sig'), f"Karne_{sec_ay}.csv", "text/csv")
                st.write("---"); st.dataframe(ay_df[['Ad Soyad', 'Tür', 'Başlangıç', 'Dönüş', 'Gun_Deger', 'Saat_Deger']])
            else: st.info("Veri yok.")
        with t2:
            m_ad = st.text_input("Personel")
            m_tip = st.radio("İp", ["Tam Gün", "Saatlik"], key="m_tip")
            with st.form("m_form"):
                m_tur, m_tar = st.selectbox("Tür", IZIN_LISTESI), st.date_input("Tarih")
                if m_tip == "Saatlik":
                    ms1, ms2 = st.time_input("Başla"), st.time_input("Bitir")
                    m_bas, m_bit = f"{m_tar.strftime('%d/%m/%Y')} {ms1.strftime('%H:%M')}", f"{m_tar.strftime('%d/%m/%Y')} {ms2.strftime('%H:%M')}"
                else:
                    mdon = st.date_input("İş Başı")
                    m_bas, m_bit = m_tar.strftime('%d/%m/%Y'), mdon.strftime('%d/%m/%Y')
                if st.form_submit_button("Kaydet"):
                    if m_ad:
                        m_data = {"tarih": datetime.now().strftime("%d/%m/%Y"), "tc": "000", "ad": m_ad, "brans": "Yön", "tur": f"{m_tur} ({m_tip})", "bas": m_bas, "bit": m_bit}
                        requests.post(APPS_SCRIPT_URL, data=json.dumps(m_data))
                        st.success("Eklendi!"); st.rerun()
    elif sifre != "": st.error("Hatalı!")

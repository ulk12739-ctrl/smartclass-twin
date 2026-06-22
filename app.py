import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import streamlit as st
import matplotlib.pyplot as plt
from sklearn import tree
from streamlit_extras.let_it_rain import rain
import plotly.graph_objects as go

# ==================================================
# SAYFA AYARLARI (En üstte kalmalı)
# ==================================================
st.set_page_config(page_title="SmartClass Twin", page_icon="🏫", layout="centered")

# ==================================================
# SABİT ÜST BİLGİ (HEADER) - HER EKRANDA GÖRÜNÜR
# ==================================================
col_logo_sol, col_baslik, col_logo_sag = st.columns([1, 3, 1])

with col_logo_sol:
    st.image("kesapfenlogo-removebg-preview.png", width=80)

with col_baslik:
    st.markdown("<h1 style='text-align: center; color: #FF4B4B; margin-bottom: 0;'>🚀 SmartClass Twin</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>Yapay Zeka Destekli Öğrenci Risk Analiz Sistemi</p>", unsafe_allow_html=True)

with col_logo_sag:
    st.image("meblogo-removebg-preview.png", width=100)

st.markdown("---")

# ==================================================
# GİRİŞ KONTROLÜ (SESSION STATE)
# ==================================================
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

# ==================================================
# 1. EKRAN: GİRİŞ PANELİ
# ==================================================
if not st.session_state["giris_yapildi"]:
    st.markdown("<h3 style='text-align: center;'>🔐 Sistem Girişi</h3>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True, type="primary"):
            if k_adi == "ogretmen" and sifre == "1234":
                st.session_state["giris_yapildi"] = True
                st.rerun()
            else:
                st.error("🚨 Hatalı kullanıcı adı veya şifre!")

# ==================================================
# 2. EKRAN: ANA UYGULAMA (Giriş Yapılınca)
# ==================================================
else:
    # HESAPLAMA MOTORU
    def risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi):
        nedenler = []
        not_ort = (ilk_not + ikinci_not) / 2
        performans_dususu = ilk_not - ikinci_not
        puan = 90.0 + (devamsizlik * 0.5) - (not_ort * 0.5) - (odev_yuzdesi * 0.2) - (katilim_yuzdesi * 0.2) + (performans_dususu * 0.1)
        
        if puan > 100: puan = 100
        if puan < 0: puan = 0
        puan = round(puan, 2)
        
        if not_ort < 70: nedenler.append("Düşük Akademik Başarı")
        if devamsizlik >= 10: nedenler.append("Devamsızlık Riski")
        if odev_yuzdesi < 85: nedenler.append("Ödev Eksikliği")
        if katilim_yuzdesi < 75: nedenler.append("Düşük Katılım")
        if performans_dususu > 0: nedenler.append(f"Performans Düşüşü ({ilk_not} -> {ikinci_not})")
        
        if puan >= 70: durum = "Yüksek Risk"
        elif puan >= 45: durum = "Riskli"
        elif puan >= 20: durum = "Düşük Risk"
        else: durum = "Risk Yok"
        
        gerekce = ", ".join(nedenler) if nedenler else "Belirgin bir risk faktörü bulunamadı."
        return puan, durum, gerekce

    # ARKA PLAN: YAPAY ZEKA MODELİNİN EĞİTİLMESİ
    @st.cache_resource
    def modeli_egit():
        veri_egitim = {
            'Son_Hafta_Devamsizlik': [1, 5, 0, 4, 1, 6, 2, 12],
            'Sinav_1': [80, 50, 95, 60, 75, 40, 90, 55],
            'Sinav_2': [90, 40, 85, 40, 65, 20, 92, 45],
            'Odev_Tamamlama_Yuzdesi': [90, 40, 100, 50, 80, 20, 95, 30],
            'Risk_Durumu': [0, 1, 0, 1, 0, 1, 0, 1]
        }
        df = pd.DataFrame(veri_egitim)
        df['Not_Ortalamasi'] = (df['Sinav_1'] + df['Sinav_2']) / 2
        X = df[['Son_Hafta_Devamsizlik', 'Not_Ortalamasi', 'Odev_Tamamlama_Yuzdesi']]
        y = df['Risk_Durumu']
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit(X, y)
        return model

    model = modeli_egit()

    # SOL MENÜ (SIDEBAR)
    st.sidebar.header("⚙️ Veri Giriş Paneli")
    ogrenci_adi = st.sidebar.text_input("Öğrenci Tanımlayıcı", value="Öğrenci Örnek")
    ilk_not = st.sidebar.number_input("1. Sınav Notu", 0, 100, 95)
    ikinci_not = st.sidebar.number_input("2. Sınav Notu", 0, 100, 85)
    odev_yuzdesi = st.sidebar.slider("Ödev Tamamlama (%)", 0, 100, 100)
    katilim_yuzdesi = st.sidebar.slider("Derse Katılım (%)", 0, 100, 90)
    devamsizlik = st.sidebar.number_input("Devamsızlık (Gün)", 0, 100, 5)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sistemden Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

    # ANA PANEL İÇERİĞİ
    st.subheader(f"📊 Analiz Paneli")
    if st.button("🔍 Analizi Başlat", type="primary", use_container_width=True):
        puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
        
        st.subheader(f"📋 {ogrenci_adi} Analiz Sonucu")
        st.metric(label="Risk Skoru", value=f"{puan} / 100")
        
        if durum == "Yüksek Risk": st.error(f"🚨 DURUM: {durum}")
        elif durum == "Riskli": st.warning(f"⚠️ DURUM: {durum}")
        elif durum == "Düşük Risk": st.info(f"💡 DURUM: {durum}")
        else: 
            st.success(f"✅ DURUM: {durum}")
            rain(emoji="🎉", font_size=40, falling_speed=5, animation_length=3)
            
        st.write(f"🔍 **Gerekçeler:** {gerekce}")

        # GRAFİKLER
        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Performans Sütunları**")
            st.bar_chart(pd.DataFrame({"Puan": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]}, 
                        index=["1. Sınav", "2. Sınav", "Ödev", "Katılım"]))
        with col_g2:
            st.markdown("**Profil Radarı**")
            devam_p = max(0, 100 - (devamsizlik * 2))
            fig = go.Figure(data=go.Scatterpolar(
                r=[ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi, devam_p, ilk_not],
                theta=['1. Sınav', '2. Sınav', 'Ödev', 'Katılım', 'Devamlılık', '1. Sınav'],
                fill='toself', line_color='#FF4B4B'
            ))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=30, r=30, t=30, b=30))
            st.plotly_chart(fig, use_container_width=True)

    # TOPLU ANALİZ
    st.markdown("---")
    st.header("📁 Toplu Sınıf Analizi")
    yuklenen = st.file_uploader("Şablonu buraya yükleyin", type=["csv", "xlsx"])

    if yuklenen is not None:
        try:
            df = pd.read_csv(yuklenen, sep=';') if yuklenen.name.endswith('.csv') else pd.read_excel(yuklenen)
            res = [risk_hesapla(r["İlk Not"], r["İkinci Not"], r["Devamsızlık"], r["Ödev Yüzdesi"], r["Katılım Yüzdesi"]) for i, r in df.iterrows()]
            df["Risk Puanı"], df["Risk Durumu"], df["Öneri"] = zip(*res)
            
            st.success("✅ Sınıf analizi tamamlandı!")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mevcut", len(df))
            m2.metric("🚨 Yüksek Risk", list(df["Risk Durumu"]).count("Yüksek Risk"))
            m3.metric("⚠️ Riskli", list(df["Risk Durumu"]).count("Riskli"))
            m4.metric("✅ Risk Yok", list(df["Risk Durumu"]).count("Risk Yok"))
            
            def renk_ver(val):
                if val == "Yüksek Risk": return 'background-color: rgba(255, 75, 75, 0.4)'
                elif val == "Riskli": return 'background-color: rgba(255, 165, 0, 0.4)'
                elif val == "Düşük Risk": return 'background-color: rgba(255, 255, 0, 0.2)'
                elif val == "Risk Yok": return 'background-color: rgba(0, 128, 0, 0.4)'
                return ''

            if hasattr(df.style, "map"):
                st.dataframe(df.style.map(renk_ver, subset=['Risk Durumu']))
            else:
                st.dataframe(df.style.applymap(renk_ver, subset=['Risk Durumu']))

            csv_analiz = df.to_csv(index=False, sep=';')
            
            ozet_rapor_metni = (
                "\n\n"
                "=== YAPAY ZEKA SINIF GENEL RİSK ÖZETİ ===\n"
                f"Toplam Analiz Edilen Öğrenci Sayısı;{len(df)}\n"
                f"🚨 Yüksek Riskli Öğrenci Sayısı;{list(df['Risk Durumu']).count('Yüksek Risk')}\n"
                f"⚠️ Riskli Öğrenci Sayısı;{list(df['Risk Durumu']).count('Riskli')}\n"
                f"💡 Düşük Riskli Öğrenci Sayısı;{list(df['Risk Durumu']).count('Düşük Risk')}\n"
                f"✅ Risk Faktörü Bulunmayan Öğrenci Sayısı;{list(df['Risk Durumu']).count('Risk Yok')}\n"
            )
            
            indirme_verisi = (csv_analiz + ozet_rapor_metni).encode('utf-8-sig')

            st.download_button("📥 Raporu İndir (Özet Verileri Dahil)", indirme_verisi, "SmartClass_Analiz.csv", mime='text/csv')
        except Exception as e:
            st.error(f"Format hatası! Lütfen şablonu kontrol edin. Detay: {e}")

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
    st.image("kesapfenlogo-removebg-preview.png", width=90)

with col_baslik:
    st.markdown("<h2 style='text-align: center; color: #FF4B4B; margin-bottom: 0;'>🏫 SmartClass Twin</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; font-style: italic;'>Öğrenci Risk Analiz Paneli</h4>", unsafe_allow_html=True)

with col_logo_sag:
    st.image("meblogo-removebg-preview.png", width=120)

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
    # HESAPLAMA MOTORU (Risk Puanı)
    def risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi):
        nedenler = []
        not_ort = (ilk_not + ikinci_not) / 2
        puan = 90.0 + (devamsizlik * 0.5) - (not_ort * 0.5) - (odev_yuzdesi * 0.2) - (katilim_yuzdesi * 0.2)
        
        if puan > 100: puan = 100
        if puan < 0: puan = 0
        puan = round(puan, 2)

        if not_ort < 70: nedenler.append("Düşük Akademik Başarı")
        if devamsizlik >= 10: nedenler.append("Devamsızlık Riski")
        if odev_yuzdesi < 85: nedenler.append("Ödev Eksikliği")
        if katilim_yuzdesi < 75: nedenler.append("Düşük Katılım")

        if puan >= 70: durum = "Yüksek Risk"
        elif puan >= 45: durum = "Riskli"
        elif puan >= 20: durum = "Düşük Risk"
        else: durum = "Risk Yok"
            
        gerekce = ", ".join(nedenler) if nedenler else "Belirgin bir risk faktörü bulunamadı."
        return puan, durum, gerekce

    # OTURMA DÜZENİ VE PERFORMANS EĞRİSİ ÖNERİ MOTORU
    def oturma_onerisi_yap(ilk_not, ikinci_not, duzen2):
        # Performans Eğrisi Hesaplama: 1. Sınav - 2. Sınav
        # Sonuç Pozitifse (+) : Düşüş var
        # Sonuç Negatifse (-) : Artış var
        performans_egrisi = ilk_not - ikinci_not
        mesaj = ""
        ikon = "💡"
        durum_analizi = ""

        if performans_egrisi > 0: # PERFORMANS DÜŞÜŞÜ (+)
            durum_analizi = f"📉 Performans Eğrisi: +{performans_egrisi} (Düşüş Tespit Edildi)"
            if duzen2 == "Geleneksel Sıra":
                mesaj = "Geleneksel düzende başarı kaybı yaşanmış. Sosyal etkileşimi artırmak için üst verim kademeleri olan 'Yarım Daire' veya 'Küme Düzeni'ne geçiş önerilir."
                ikon = "🚨"
            elif duzen2 == "Yarım Daire":
                mesaj = "Yarım daire düzeninde performans düşüşü sürüyor. En üst etkileşim seviyesi olan 'Küme Düzeni'ne geçiş yapılması tavsiye edilir."
                ikon = "⚠️"
            else: # Zaten Küme Düzenindeyse
                mesaj = "En verimli düzen olan Küme Düzeninde dahi düşüş gözlemleniyor. Durumun akademik değil psikolojik/rehberlik kaynaklı olduğu düşünülerek rehberlik servisine bilgi verilmelidir."
                ikon = "🛑"
        
        elif performans_egrisi < 0: # PERFORMANS ARTIŞI (-)
            durum_analizi = f"📈 Performans Eğrisi: {performans_egrisi} (Artış Tespit Edildi)"
            mesaj = f"Başarı artışı sağlandı! Mevcut '{duzen2}' yerleşimi öğrenci üzerinde pozitif etki yaratmış. Bu düzenin bir süre daha korunması önerilir."
            ikon = "✅"
        
        else: # SABİT
            durum_analizi = "📊 Performans Eğrisi: 0 (Değişim Yok)"
            mesaj = "Başarı durumu stabil. Öğrenciyi daha aktif kılmak adına bir üst etkileşimli oturma düzeni denenebilir."
            ikon = "ℹ️"
            
        return durum_analizi, mesaj, ikon

    # ARKA PLAN: YAPAY ZEKA MODELİ
    @st.cache_resource
    def modeli_egit():
        veri_egitim = {'Son_Hafta_Devamsizlik': [1, 5, 0, 4, 12], 'Sinav_1': [80, 50, 95, 60, 55], 'Sinav_2': [90, 40, 85, 40, 45], 'Odev_Tamamlama_Yuzdesi': [90, 40, 100, 50, 30], 'Risk_Durumu': [0, 1, 0, 1, 1]}
        df = pd.DataFrame(veri_egitim)
        df['Not_Ortalamasi'] = (df['Sinav_1'] + df['Sinav_2']) / 2
        model = DecisionTreeClassifier(max_depth=3, random_state=42)
        model.fit(df[['Son_Hafta_Devamsizlik', 'Not_Ortalamasi', 'Odev_Tamamlama_Yuzdesi']], df['Risk_Durumu'])
        return model

    model = modeli_egit()

    # SOL MENÜ (SIDEBAR)
    st.sidebar.header("⚙️ Veri Giriş Paneli")
    ogrenci_adi = st.sidebar.text_input("Öğrenci Tanımlayıcı", value="Öğrenci Örnek")
    
    ilk_not = st.sidebar.number_input("1. Sınav Notu", 0, 100, 95)
    ikinci_not = st.sidebar.number_input("2. Sınav Notu", 0, 100, 85)
    
    st.sidebar.markdown("---")
    st.sidebar.write("📌 **Sınıf Fiziksel Verisi**")
    duzen2 = st.sidebar.selectbox("Güncel Oturma Düzeni", ["Geleneksel Sıra", "Yarım Daire", "Küme Düzeni"])
    
    st.sidebar.markdown("---")
    odev_yuzdesi = st.sidebar.slider("Ödev Tamamlama (%)", 0, 100, 100)
    katilim_yuzdesi = st.sidebar.slider("Derse Katılım (%)", 0, 100, 90)
    devamsizlik = st.sidebar.number_input("Devamsızlık (Gün)", 0, 100, 5)
    
    if st.sidebar.button("🚪 Sistemden Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

    # ANA PANEL
    if st.button("📊 Analiz ve Stratejik Öneriyi Göster", type="primary", use_container_width=True):
        puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
        egri_metni, oneri_mesaji, oneri_ikon = oturma_onerisi_yap(ilk_not, ikinci_not, duzen2)
        
        st.subheader(f"📋 {ogrenci_adi} Analiz Sonucu")
        st.metric(label="Hesaplanan Risk Skoru", value=f"{puan} / 100")
        
        if durum == "Yüksek Risk": st.error(f"🚨 GENEL DURUM: {durum}")
        elif durum == "Riskli": st.warning(f"⚠️ GENEL DURUM: {durum}")
        elif durum == "Düşük Risk": st.info(f"💡 GENEL DURUM: {durum}")
        else: 
            st.success(f"✅ GENEL DURUM: {durum}")
            rain(emoji="🎉", font_size=40, falling_speed=5, animation_length=3)
            
        st.info(f"🔍 **Risk Faktörleri:** {gerekce}")

        # YENİ: STRATEJİK ÖNERİ VE PERFORMANS EĞRİSİ
        st.subheader("🎯 Stratejik Yerleşim Önerisi")
        st.info(f"**{egri_metni}**")
        st.success(f"{oneri_ikon} **Yerleşim Tavsiyesi:** {oneri_mesaji}")
        
        # PEDAGOJİK ÖNERİLER (ESKİLER KORUNDU)
        st.subheader("📋 Profil Yorumlama ve Öneriler")
        not_ort = (ilk_not + ikinci_not) / 2
        uyari_sayisi = 0

        if devamsizlik >= 18:
            st.error("🚨 KRİTİK DEVAMSIZLIK: Devamsızlık sınırı aşılmış. Veli ivedilikle aranmalı.")
            uyari_sayisi += 1
        elif devamsizlik >= 10:
            st.warning("⚠️ DEVAMSIZLIK SINIRDA: Devamsızlık sınırda. Öğrenciye uyarı verilmeli.")
            uyari_sayisi += 1

        if not_ort < 50 and odev_yuzdesi < 50:
            st.error("🔴 AKADEMİK & ÖDEV ALARMI: Öğrenci başarısız ve ödev teslim etmiyor. Ek etüt planlanmalı.")
            uyari_sayisi += 1
        else:
            if not_ort < 70:
                st.warning("🟠 AKADEMİK DESTEK: Not ortalaması zayıf. Soru çözüm ofislerine katılım zorunlu tutulmalı.")
                uyari_sayisi += 1
            if odev_yuzdesi < 85:
                st.warning("🟡 ÖDEV DİSİPLİNİ: Ödev istikrarı düşük. Haftalık ödev takip çizelgesi verilmeli.")
                uyari_sayisi += 1

        if katilim_yuzdesi < 75:
            st.info("🔵 DERSE KATILIM RİSKİ: Öğrenci derste pasif. Derste söz hakkı verilerek teşvik edilmeli.")
            uyari_sayisi += 1

        if uyari_sayisi == 0:
            st.success("🟢 BAŞARILI PROFİL: Tüm kriterler hedef seviyede. Öğrenci tebrik edilmeli.")

        # GRAFİKLER
        st.markdown("---")
        st.subheader("📊 Gelişim & Profil Radarı")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Akademik Veriler**")
            st.bar_chart(pd.DataFrame({"Değerler": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]}, index=["1. Sınav", "2. Sınav", "Ödev", "Katılım"]))
        with col_g2:
            st.markdown("**Yetkinlik Radarı**")
            devam_p = max(0, 100 - (devamsizlik * 2))
            fig = go.Figure(data=go.Scatterpolar(r=[ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi, devam_p, ilk_not], theta=['1. Sınav', '2. Sınav', 'Ödev', 'Katılım', 'Devamlılık', '1. Sınav'], fill='toself', line_color='#FF4B4B'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # TOPLU ANALİZ
    st.markdown("---")
    st.header("📁 Toplu Sınıf Analizi")
    ornek_df = pd.DataFrame({"Öğrenci Adı": ["Örn 1"], "İlk Not": [90], "İkinci Not": [80], "Devamsızlık": [2], "Ödev Yüzdesi": [90], "Katılım Yüzdesi": [80]})
    st.download_button(label="📥 Örnek Şablonu İndir", data=ornek_df.to_csv(index=False, sep=';').encode('utf-8-sig'), file_name='SmartClass_Ornek.csv')
    
    yuklenen = st.file_uploader("Listeyi Yükleyin", type=["csv", "xlsx"])
    if yuklenen:
        try:
            df_y = pd.read_csv(yuklenen, sep=';') if yuklenen.name.endswith('.csv') else pd.read_excel(yuklenen)
            res = [risk_hesapla(r["İlk Not"], r["İkinci Not"], r["Devamsızlık"], r["Ödev Yüzdesi"], r["Katılım Yüzdesi"]) for i, r in df_y.iterrows()]
            df_y["Risk Puanı"], df_y["Risk Durumu"], df_y["Yapay Zeka Önerisi"] = zip(*res)
            st.success("✅ Sınıf analizi tamamlandı!")
            m1, m2, m3 = st.columns(3); m1.metric("Mevcut", len(df_y)); m2.metric("🚨 Yüksek Risk", list(df_y["Risk Durumu"]).count("Yüksek Risk")); m3.metric("✅ Risk Yok", list(df_y["Risk Durumu"]).count("Risk Yok"))
            st.dataframe(df_y)
            st.download_button(label="📥 Raporu İndir", data=df_y.to_csv(index=False, sep=';').encode('utf-8-sig'), file_name='Sınıf_Raporu.csv')
        except: st.error("Dosya formatı uyumsuz!")

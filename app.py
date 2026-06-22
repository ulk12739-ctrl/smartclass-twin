import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import streamlit as st
import matplotlib.pyplot as plt
from sklearn import tree
from streamlit_extras.let_it_rain import rain
import plotly.graph_objects as go

# ==================================================
# SAYFA AYARLARI
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

    # YENİ: OTURMA DÜZENİ ÖNERİ MOTORU
    def oturma_onerisi_yap(ilk_not, ikinci_not, d1, d2):
        mesaj = ""
        ikon = "💡"
        
        if ikinci_not < ilk_not: # Not düşmüşse
            if d2 == "Geleneksel Sıra":
                mesaj = "Not düşüşü gözlemlendi. Geleneksel düzenden 'Yarım Daire' veya 'Küme Düzeni' gibi daha etkileşimli bir modele geçilmesi önerilir."
                ikon = "🚨"
            elif d2 == "Yarım Daire":
                mesaj = "Yarım daire düzenine rağmen düşüş sürmekte. En üst kademe olan 'Küme Düzeni'ne (Grup Çalışması) geçiş yapılması tavsiye edilir."
                ikon = "⚠️"
            else: # Zaten Küme Düzenindeyse
                mesaj = "Öğrenci en verimli düzen olan Küme Düzeninde olmasına rağmen düşüş yaşıyor. Acil rehberlik servisine yönlendirilmeli ve bireysel destek verilmelidir."
                ikon = "🛑"
        elif ikinci_not > ilk_not: # Not artmışsa
            mesaj = f"Başarı artışı sağlandı! Mevcut '{d2}' düzeni öğrenci için verimli görünüyor, bu düzenin korunması başarının devamını sağlayabilir."
            ikon = "✅"
        else: # Not sabitse
            mesaj = "Başarı durumu sabit. Sosyal etkileşimi artırmak için bir üst kademe oturma düzeni denenebilir."
            ikon = "ℹ️"
            
        return mesaj, ikon

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

    # SOL MENÜ (SIDEBAR): VERİ GİRİŞ PANELİ
    st.sidebar.header("⚙️ Veri Giriş Paneli")
    ogrenci_adi = st.sidebar.text_input("Öğrenci Tanımlayıcı", value="Öğrenci Örnek")
    
    # --- SINAV 1 VE DÜZENİ ---
    ilk_not = st.sidebar.number_input("1. Sınav Notu", 0, 100, 95)
    duzen1 = st.sidebar.selectbox("1. Sınav Dönemi Oturma Düzeni", ["Geleneksel Sıra", "Yarım Daire", "Küme Düzeni"])
    
    # --- SINAV 2 VE DÜZENİ ---
    ikinci_not = st.sidebar.number_input("2. Sınav Notu", 0, 100, 85)
    duzen2 = st.sidebar.selectbox("2. Sınav Dönemi Oturma Düzeni", ["Geleneksel Sıra", "Yarım Daire", "Küme Düzeni"])
    
    st.sidebar.markdown("---")
    odev_yuzdesi = st.sidebar.slider("Ödev Tamamlama (%)", 0, 100, 100)
    katilim_yuzdesi = st.sidebar.slider("Derse Katılım (%)", 0, 100, 90)
    devamsizlik = st.sidebar.number_input("Devamsızlık (Gün)", 0, 100, 5)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sistemden Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

    # ANA PANEL İÇERİĞİ
    st.write("Öğrencinin akademik ve mekansal verilerini girerek analizi başlatın.")
    if st.button("📊 Analizi ve Önerileri Göster", type="primary", use_container_width=True):
        puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
        oneri_mesaji, oneri_ikon = oturma_onerisi_yap(ilk_not, ikinci_not, duzen1, duzen2)
        
        st.subheader(f"📋 {ogrenci_adi} İçin Risk Analiz Raporu")
        st.metric(label="Hesaplanan Risk Skoru", value=f"{puan} / 100")
        
        # Risk Durumu Gösterimi
        if durum == "Yüksek Risk": st.error(f"🚨 GENEL DURUM: {durum}")
        elif durum == "Riskli": st.warning(f"⚠️ GENEL DURUM: {durum}")
        elif durum == "Düşük Risk": st.info(f"💡 GENEL DURUM: {durum}")
        else: 
            st.success(f"✅ GENEL DURUM: {durum}")
            rain(emoji="🎉", font_size=40, falling_speed=5, animation_length=3)
            
        st.info(f"🔍 **Risk Gerekçeleri:** {gerekce}")

        # YENİ: OTURMA DÜZENİ ÖNERİSİ
        st.subheader("🪑 Mekansal Yerleşim Önerisi")
        st.success(f"{oneri_ikon} **Stratejik Öneri:** {oneri_mesaji}")
        
        # Profil Yorumlama ve Öneriler
        st.subheader("📋 Pedagojik Öneriler")
        not_ort = (ilk_not + ikinci_not) / 2
        uyari_sayisi = 0

        if devamsizlik >= 18:
            st.error("🚨 KRİTİK DEVAMSIZLIK: Devamsızlık sınırı aşılmış. Veli ivedilikle aranmalı.")
            uyari_sayisi += 1
        elif devamsizlik >= 10:
            st.warning("⚠️ DEVAMSIZLIK SINIRDA: Devamsızlık sınırı yakın. Öğrenciyle görüşülmeli.")
            uyari_sayisi += 1

        if not_ort < 50 and odev_yuzdesi < 50:
            st.error("🔴 AKADEMİK & ÖDEV ALARMI: Başarısızlık ve ödev eksikliği bir arada. Ek etüt planlanmalı.")
            uyari_sayisi += 1
        else:
            if not_ort < 70:
                st.warning("🟠 AKADEMİK DESTEK: Ortalamayı yükseltmek için soru çözüm ofislerine katılım sağlanmalı.")
                uyari_sayisi += 1
            if odev_yuzdesi < 85:
                st.warning("🟡 ÖDEV DİSİPLİNİ: Ödev istikrarı düşük. Haftalık takip çizelgesi verilmeli.")
                uyari_sayisi += 1

        if uyari_sayisi == 0:
            st.success("🟢 BAŞARILI PROFİL: Mevcut çalışma disiplini desteklenmeli.")

        # GRAFİKLER
        st.markdown("---")
        st.subheader("📊 Performans & Profil Radarı")
        col_grafik1, col_grafik2 = st.columns(2)
        
        with col_grafik1:
            st.markdown("**Temel Puanlar**")
            st.bar_chart(pd.DataFrame({"Puanlar": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]}, 
                        index=["1. Sınav", "2. Sınav", "Ödev", "Katılım"]))
            
        with col_grafik2:
            st.markdown("**Yetkinlik Ağı (Radar)**")
            devam_puani = max(0, 100 - (devamsizlik * 2))
            kategoriler = ['1. Sınav', '2. Sınav', 'Ödev', 'Katılım', 'Devamlılık', '1. Sınav']
            degerler = [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi, devam_puani, ilk_not]
            
            fig = go.Figure(data=go.Scatterpolar(r=degerler, theta=kategoriler, fill='toself', line_color='#FF4B4B'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(l=40, r=40, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # TOPLU SINIF ANALİZİ
    st.markdown("---")
    st.header("📁 Toplu Sınıf Analizi")
    st.write("Excel üzerinden tüm sınıfın risk ve düzen analizini yapın.")

    ornek_veri = {
        "Öğrenci Adı": ["Öğrenci 1", "Öğrenci 2"],
        "İlk Not": [95, 40],
        "İkinci Not": [100, 35],
        "Devamsızlık": [0, 15],
        "Ödev Yüzdesi": [100, 40],
        "Katılım Yüzdesi": [100, 30]
    }
    ornek_df = pd.DataFrame(ornek_veri)
    st.download_button(label="📥 Örnek Şablonu İndir", data=ornek_df.to_csv(index=False, sep=';').encode('utf-8-sig'), file_name='SmartClass_Sablon.csv')

    yuklenen_dosya = st.file_uploader("Şablonu yükleyin", type=["csv", "xlsx"])

    if yuklenen_dosya is not None:
        try:
            df_yuklenen = pd.read_csv(yuklenen_dosya, sep=';') if yuklenen_dosya.name.endswith('.csv') else pd.read_excel(yuklenen_dosya)
            
            p_list, d_list, g_list = [], [], []
            for i, row in df_yuklenen.iterrows():
                p, d, g = risk_hesapla(row["İlk Not"], row["İkinci Not"], row["Devamsızlık"], row["Ödev Yüzdesi"], row["Katılım Yüzdesi"])
                p_list.append(p); d_list.append(d); g_list.append(g)
            
            df_yuklenen["Risk Puanı"], df_yuklenen["Risk Durumu"], df_yuklenen["Öneri"] = p_list, d_list, g_list
            
            st.success("✅ Sınıf analizi tamamlandı!")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Mevcut", len(df_yuklenen))
            m2.metric("🚨 Yüksek Risk", d_list.count("Yüksek Risk"))
            m3.metric("⚠️ Riskli", d_list.count("Riskli"))
            m4.metric("💡 Düşük Risk", d_list.count("Düşük Risk"))
            m5.metric("✅ Risk Yok", d_list.count("Risk Yok"))
            
            def renk_ver(val):
                if val == "Yüksek Risk": return 'background-color: rgba(255, 75, 75, 0.4)'
                elif val == "Riskli": return 'background-color: rgba(255, 165, 0, 0.4)'
                elif val == "Düşük Risk": return 'background-color: rgba(255, 255, 0, 0.2)'
                elif val == "Risk Yok": return 'background-color: rgba(0, 128, 0, 0.4)'
                return ''

            st.dataframe(df_yuklenen.style.applymap(renk_ver, subset=['Risk Durumu']))
            
            csv_data = df_yuklenen.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button(label="📥 Analiz Raporunu İndir", data=csv_data, file_name='Sınıf_Analiz_Raporu.csv')
            
        except Exception as e:
            st.error(f"🚨 Hata: {e}")

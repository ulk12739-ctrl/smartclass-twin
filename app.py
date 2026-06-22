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
    st.write("Öğrencinin verilerini girerek yapay zeka ve ağırlıklı risk puanı analizini anında görebilirsiniz.")
    
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

    # ANALİZ BUTONU VE SONUÇLARIN GÖSTERİLMESİ
    if st.button("📊 Öğrenci Risk Analizini Yap", type="primary", use_container_width=True):
        puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
        oneri_mesaji, oneri_ikon = oturma_onerisi_yap(ilk_not, ikinci_not, duzen1, duzen2)
        
        st.subheader(f"📋 {ogrenci_adi} İçin Risk Analiz Raporu")
        st.metric(label="Hesaplanan Risk Puanı", value=f"{puan} / 100")
        
        if durum == "Yüksek Risk": st.error(f"🚨 GENEL DURUM: {durum}")
        elif durum == "Riskli": st.warning(f"⚠️ GENEL DURUM: {durum}")
        elif durum == "Düşük Risk": st.info(f"💡 GENEL DURUM: {durum}")
        else: 
            st.success(f"✅ GENEL DURUM: {durum}")
            rain(emoji="🎉", font_size=40, falling_speed=5, animation_length=3)
            
        st.info(f"🔍 **Tespit Edilen Risk Gerekçeleri:** {gerekce}")

        # YENİ: OTURMA DÜZENİ ÖNERİSİ
        st.subheader("🪑 Mekansal Yerleşim Önerisi")
        st.success(f"{oneri_ikon} **Stratejik Öneri:** {oneri_mesaji}")
        
        # ---> KULLANICININ İSTEDİĞİ ESKİ "Profil Yorumlama ve Öneriler" KISMI TAMAMEN GERİ GELDİ! <---
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

        # ==================================================
        # GÖRSEL PERFORMANS GRAFİĞİ VE RADAR
        # ==================================================
        st.markdown("---")
        st.subheader("📊 Öğrenci Performans & Profil Radarı")
        
        col_grafik1, col_grafik2 = st.columns(2)
        
        with col_grafik1:
            st.markdown("**Temel Puanlar (Sütun)**")
            grafik_verisi = pd.DataFrame({
                "Kategoriler": ["1. Sınav", "2. Sınav", "Ödev", "Katılım"],
                "Puanlar": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]
            })
            st.bar_chart(grafik_verisi.set_index("Kategoriler"))
            
        with col_grafik2:
            st.markdown("**Yetkinlik Ağı (Radar)**")
            
            devam_puani = 100 - (devamsizlik * 2) 
            if devam_puani < 0: devam_puani = 0
                
            kategoriler = ['1. Sınav', '2. Sınav', 'Ödev', 'Katılım', 'Devamlılık']
            degerler = [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi, devam_puani]
            
            kategoriler_kapali = kategoriler + [kategoriler[0]]
            degerler_kapali = degerler + [degerler[0]]
            
            fig = go.Figure(data=go.Scatterpolar(
                r=degerler_kapali,
                theta=kategoriler_kapali,
                fill='toself',
                line_color='#FF4B4B'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                showlegend=False,
                margin=dict(l=40, r=40, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ==================================================
    # TOPLU SINIF ANALİZİ (ŞABLON VE YÜKLEME MODÜLÜ)
    # ==================================================
    st.markdown("---")
    st.header("📁 Toplu Sınıf Analizi")
    st.write("Sınıfınızın verilerini tek seferde analiz etmek için önce aşağıdaki şablonu indirin, öğrenci verilerini doldurun ve ardından sisteme geri yükleyin.")

    ornek_veri = {
        "Öğrenci Adı": ["Öğrenci 1", "Öğrenci 2", "Öğrenci 3", "Öğrenci 4"],
        "İlk Not": [95, 40, 85, 95],
        "İkinci Not": [100, 35, 90, 90],
        "Devamsızlık": [0, 15, 22, 2],
        "Ödev Yüzdesi": [100, 40, 90, 10],
        "Katılım Yüzdesi": [100, 30, 85, 20]
    }
    ornek_df = pd.DataFrame(ornek_veri)
    csv_sablon = ornek_df.to_csv(index=False, sep=';').encode('utf-8-sig')

    st.download_button(
        label="📥 Örnek Şablonu İndir (CSV)",
        data=csv_sablon,
        file_name='SmartClass_Ornek_Sablon.csv',
        mime='text/csv',
    )

    st.markdown("<br>", unsafe_allow_html=True) 

    yuklenen_dosya = st.file_uploader("Doldurduğunuz şablonu buraya sürükleyin", type=["csv", "xlsx"])

    if yuklenen_dosya is not None:
        try:
            if yuklenen_dosya.name.endswith('.csv'):
                df_yuklenen = pd.read_csv(yuklenen_dosya, sep=';')
            else:
                df_yuklenen = pd.read_excel(yuklenen_dosya)
                
            risk_puanlari = []
            durumlar = []
            gerekceler = []
            
            for index, row in df_yuklenen.iterrows():
                puan, durum, gerekce = risk_hesapla(
                    row["İlk Not"], row["İkinci Not"], row["Devamsızlık"], row["Ödev Yüzdesi"], row["Katılım Yüzdesi"]
                )
                risk_puanlari.append(puan)
                durumlar.append(durum)
                gerekceler.append(gerekce)
            
            df_yuklenen["Risk Puanı"] = risk_puanlari
            df_yuklenen["Risk Durumu"] = durumlar
            df_yuklenen["Yapay Zeka Önerisi"] = gerekceler
            
            st.success("✅ Yapay Zeka sınıfınızı saniyeler içinde analiz etti! İşte sonuçlar:")
            
            toplam_ogrenci = len(df_yuklenen)
            yuksek_risk_sayisi = durumlar.count("Yüksek Risk")
            riskli_sayisi = durumlar.count("Riskli")
            dusuk_risk_sayisi = durumlar.count("Düşük Risk")
            risk_yok_sayisi = durumlar.count("Risk Yok")
            
            st.subheader("📊 Sınıf Genel Risk İstatistikleri")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Mevcut", toplam_ogrenci)
            m2.metric("🚨 Yüksek Risk", yuksek_risk_sayisi)
            m3.metric("⚠️ Riskli", riskli_sayisi)
            m4.metric("💡 Düşük Risk", dusuk_risk_sayisi)
            m5.metric("✅ Risk Yok", risk_yok_sayisi)
            st.markdown("<br>", unsafe_allow_html=True)
            
            def renk_ver(val):
                if val == "Yüksek Risk": return 'background-color: rgba(255, 75, 75, 0.4)'
                elif val == "Riskli": return 'background-color: rgba(255, 165, 0, 0.4)'
                elif val == "Düşük Risk": return 'background-color: rgba(255, 255, 0, 0.2)'
                elif val == "Risk Yok": return 'background-color: rgba(0, 128, 0, 0.4)'
                return ''

            if hasattr(df_yuklenen.style, "map"):
                st.dataframe(df_yuklenen.style.map(renk_ver, subset=['Risk Durumu']))
            else:
                st.dataframe(df_yuklenen.style.applymap(renk_ver, subset=['Risk Durumu']))
                
            csv_analiz = df_yuklenen.to_csv(index=False, sep=';')
            
            ozet_rapor_metni = (
                "\n\n"
                "=== YAPAY ZEKA SINIF GENEL RİSK ÖZETİ ===\n"
                f"Toplam Analiz Edilen Öğrenci Sayısı;{toplam_ogrenci}\n"
                f"🚨 Yüksek Riskli Öğrenci Sayısı;{yuksek_risk_sayisi}\n"
                f"⚠️ Riskli Öğrenci Sayısı;{riskli_sayisi}\n"
                f"💡 Düşük Riskli Öğrenci Sayısı;{dusuk_risk_sayisi}\n"
                f"✅ Risk Faktörü Bulunmayan Öğrenci Sayısı;{risk_yok_sayisi}\n"
            )
            
            indirme_verisi = (csv_analiz + ozet_rapor_metni).encode('utf-8-sig')
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Analiz Raporunu İndir (Özet Verileri Dahil)",
                data=indirme_verisi,
                file_name='SmartClass_Sınıf_Analiz_Raporu.csv',
                mime='text/csv',
            )
            
        except Exception as e:
            st.error(f"🚨 Hata detayı: {e}")

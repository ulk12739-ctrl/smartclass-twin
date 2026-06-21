import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import streamlit as st
import matplotlib.pyplot as plt
from sklearn import tree
from streamlit_extras.let_it_rain import rain

# ==================================================
# SAYFA AYARLARI
# ==================================================
st.set_page_config(page_title="SmartClass Twin", page_icon="🏫", layout="centered")

# ==================================================
# HESAPLAMA MOTORU
# ==================================================
def risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi):
    nedenler = []
    not_ort = (ilk_not + ikinci_not) / 2
    performans_dususu = ilk_not - ikinci_not
    
    # Excel'deki formülün birebir aynısı!
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

# ==================================================
# EN ÜST KÖŞELERDEKİ ŞEFFAF LOGOLAR 
# ==================================================
col_sol, col_bosluk, col_sag = st.columns([2, 3, 2])

with col_sol:
    st.image("kesapfenlogo-removebg-preview.png", width=90)

with col_sag:
    st.image("meblogo-removebg-preview.png", width=120)

st.title("🏫 SmartClass Twin - Öğrenci Risk Analiz Paneli")
st.write("Öğrencinin verilerini girerek yapay zeka ve ağırlıklı risk puanı analizini anında görebilirsiniz.")
st.markdown("---")

# ==================================================
# ARKA PLAN: YAPAY ZEKA MODELİNİN EĞİTİLMESİ
# ==================================================
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

# ==================================================
# SOL MENÜ (SIDEBAR): VERİ GİRİŞ PANELİ
# ==================================================
st.sidebar.header("⚙️ Veri Giriş Paneli")
st.sidebar.write("Tekil öğrenci analizi için değerleri belirleyin.")

ogrenci_adi = st.sidebar.text_input("Öğrenci Tanımlayıcı", value="Öğrenci Örnek")
ilk_not = st.sidebar.number_input("1. Sınav Notu", min_value=0, max_value=100, value=95)
ikinci_not = st.sidebar.number_input("2. Sınav Notu", min_value=0, max_value=100, value=85)
odev_yuzdesi = st.sidebar.slider("Ödev Tamamlama (%)", min_value=0, max_value=100, value=100)
katilim_yuzdesi = st.sidebar.slider("Derse Katılım (%)", min_value=0, max_value=100, value=90)
devamsizlik = st.sidebar.number_input("Devamsızlık (Gün)", min_value=0, max_value=100, value=5)

# ==================================================
# ANALİZ BUTONU VE SONUÇLARIN GÖSTERİLMESİ
# ==================================================
if st.button("📊 Öğrenci Risk Analizini Yap", type="primary"):
    puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
    
    st.subheader(f"📋 {ogrenci_adi} İçin Risk Analiz Raporu")
    st.metric(label="Hesaplanan Risk Puanı", value=f"{puan} / 100")
    
    if durum == "Yüksek Risk": 
        st.error(f"🚨 GENEL DURUM: {durum}")
    elif durum == "Riskli": 
        st.warning(f"⚠️ GENEL DURUM: {durum}")
    elif durum == "Düşük Risk": 
        st.info(f"💡 GENEL DURUM: {durum}")
    else: 
        st.success(f"✅ GENEL DURUM: {durum}")
        rain(emoji="🎉", font_size=40, falling_speed=5, animation_length=3)
        
    st.info(f"🔍 **Tespit Edilen Risk Gerekçeleri:** {gerekce}")
    
    st.subheader("📋 Profil Yorumlama ve Öneriler")
    
    not_ort = (ilk_not + ikinci_not) / 2
    uyari_sayisi = 0

    if devamsizlik >= 18:
        st.error("🚨 KRİTİK DEVAMSIZLIK: Devamsızlık sınırı aşılmış. Veli ivedilikle aranmalı, devamsızlık mektubu gönderilmeli ve neden araştırılmalıdır.")
        uyari_sayisi += 1
    elif devamsizlik >= 10:
        st.warning("⚠️ DEVAMSIZLIK SINIRDA: Devamsızlık sınırda. Öğrenciye uyarı verilmeli, daha fazla devamsızlık yapmaması için çalışılmalı.")
        uyari_sayisi += 1

    if not_ort < 50 and odev_yuzdesi < 50:
        st.error("🔴 AKADEMİK & ÖDEV ALARMI: Öğrenci hem derslerde başarısız hem de ödev teslim etmiyor. Birebir ödev koçluğu başlatılmalı ve ek etüt programı planlanmalı.")
        uyari_sayisi += 1
    else:
        if not_ort < 70:
            st.warning("🟠 AKADEMİK DESTEK: Not ortalaması zayıf. Eksik olduğu üniteler belirlenmeli, soru çözüm ofislerine and etütlere katılım zorunlu tutulmalı.")
            uyari_sayisi += 1
        if odev_yuzdesi < 85:
            st.warning("🟡 ÖDEV DİSİPLİNİ: Ders başarısı veya katılımı iyi olsa da ödev istikrarı düşük. Haftalık ödev takip çizelgesi verilmeli and veli onayı istenmeli.")
            uyari_sayisi += 1

    if katilim_yuzdesi < 75:
        st.info("🔵 DERSE KATILIM RİSKİ: Öğrenci derste pasif veya çekingen. Derste söz hakkı verilerek teşvik edilmeli, rehberlik servisiyle özgüven çalışması yapılmalı.")
        uyari_sayisi += 1

    if uyari_sayisi == 0:
        st.success("🟢 BAŞARILI PROFİL: Tüm kriterler hedef seviyede. Öğrencinin motivasyonunu korumak adına tebrik edilmeli, mevcut çalışma disiplini desteklenmeli.")

    # ==================================================
    # GÖRSEL PERFORMANS GRAFİĞİ
    # ==================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Öğrenci Performans Analizi")
    
    grafik_verisi = pd.DataFrame({
        "Kategoriler": ["1. Sınav", "2. Sınav", "Ödev", "Katılım"],
        "Puanlar": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]
    })
    
    st.bar_chart(grafik_verisi.set_index("Kategoriler"))

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
                row["İlk Not"], 
                row["İkinci Not"], 
                row["Devamsızlık"], 
                row["Ödev Yüzdesi"], 
                row["Katılım Yüzdesi"]
            )
            risk_puanlari.append(puan)
            durumlar.append(durum)
            gerekceler.append(gerekce)
        
        df_yuklenen["Risk Puanı"] = risk_puanlari
        df_yuklenen["Risk Durumu"] = durumlar
        df_yuklenen["Yapay Zeka Önerisi"] = gerekceler
        
        st.success("✅ Yapay Zeka sınıfınızı saniyeler içinde analiz etti! İşte sonuçlar:")
        
        # ==================================================
        # YENİ: EKRAN ÜSTÜ SINIF RISK ÖZETİ (METRİKLER)
        # ==================================================
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
        
        # ==================================================
        # TABLO RENKLENDİRME VE GÖSTERİM
        # ==================================================
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
            
        # ==================================================
        # YENİ: ÖZETLİ RAPOR İNDİRME BUTONU
        # ==================================================
        # Tabloyu ana metin olarak alıyoruz
        csv_analiz = df_yuklenen.to_csv(index=False, sep=';')
        
        # İndirilen dosyanın en altına şık bir özet rapor ekliyoruz
        ozet_rapor_metni = (
            "\n\n"
            "=== YAPAY ZEKA SINIF GENEL RİSK ÖZETİ ===\n"
            f"Toplam Analiz Edilen Öğrenci Sayısı;{toplam_ogrenci}\n"
            f"🚨 Yüksek Riskli Öğrenci Sayısı;{yuksek_risk_sayisi}\n"
            f"⚠️ Riskli Öğrenci Sayısı;{riskli_sayisi}\n"
            f"💡 Düşük Riskli Öğrenci Sayısı;{dusuk_risk_sayisi}\n"
            f"✅ Risk Faktörü Bulunmayan Öğrenci Sayısı;{risk_yok_sayisi}\n"
        )
        
        # Tablo verisi ile özet verisini birleştirip tek dosya yapıyoruz
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

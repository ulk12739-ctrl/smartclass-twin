import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import streamlit as st
import matplotlib.pyplot as plt
from sklearn import tree

# ==================================================
# SAYFA AYARLARI
# ==================================================
st.set_page_config(page_title="SmartClass Twin", page_icon="🏫", layout="centered")

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
# ÖN YÜZ: KULLANICI GİRDİ ALANLARI (FORM)
# ==================================================
st.subheader("👤 Öğrenci Bilgilerini Giriniz")

ogrenci_adi = st.text_input("Öğrenci Adı Soyadı", value="Selin")

col1, col2 = st.columns(2)
with col1:
    ilk_not = st.number_input("1. Sınav Notu", min_value=0, max_value=100, value=95)
    odev_yuzdesi = st.slider("Ödev Tamamlama Yüzdesi (%)", min_value=0, max_value=100, value=100)
with col2:
    ikinci_not = st.number_input("2. Sınav Notu", min_value=0, max_value=100, value=85)
    katilim_yuzdesi = st.slider("Derse Katılım Yüzdesi (%)", min_value=0, max_value=100, value=90)

devamsizlik = st.number_input("Toplam Devamsızlık (Gün)", min_value=0, max_value=100, value=28)

st.markdown("---")

# ==================================================
# HESAPLAMA MOTORU (FONKSİYON)
# ==================================================
def risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi):
    nedenler = []
    not_ort = (ilk_not + ikinci_not) / 2
    
    if not_ort < 50: akademik_riski, n = 100, "Düşük Akademik Başarı"
    elif not_ort < 70: akademik_riski, n = 70, "Kritik Akademik Başarı"
    elif not_ort < 85: akademik_riski, n = 35, "Sınırda Akademik Başarı"
    else: akademik_riski, n = 0, ""
    if n: nedenler.append(n)

    if devamsizlik >= 18: devamsizlik_riski, n = 100, "Kritik Devamsızlık"
    elif devamsizlik >= 10: devamsizlik_riski, n = 40, "Sınırda Devamsızlık"
    else: devamsizlik_riski, n = 0, ""
    if n: nedenler.append(n)
        
    if odev_yuzdesi < 90: odev_riski, n = 100, "Ödev Eksikliği"
    else: odev_riski, n = 0, ""
    if n: nedenler.append(n)
        
    if katilim_yuzdesi < 70: katilim_riski, n = 100, "Çok Düşük Katılım"
    elif katilim_yuzdesi <= 85: katilim_riski, n = 60, "Yetersiz Katılım"
    else: katilim_riski, n = 0, ""
    if n: nedenler.append(n)
        
    if ikinci_not < ilk_not:
        performans_riski = 100
        nedenler.append(f"Performans Düşüşü ({ilk_not} -> {ikinci_not})")
    else:
        performans_riski = 0

    agirli_toplam = (devamsizlik_riski * 0.50) + (akademik_riski * 0.50) + (odev_riski * 0.20) + (katilim_riski * 0.20) + (performans_riski * 0.10)
    puan = round(agirli_toplam / 1.50, 2)
    
    if puan >= 50: durum = "Yüksek Risk"
    elif puan >= 20: durum = "Riskli"
    elif puan >= 10: durum = "Düşük Risk"
    else: durum = "Risk Yok"
        
    gerekce = ", ".join(nedenler) if nedenler else "Belirgin bir risk faktörü bulunamadı."
    return puan, durum, gerekce

# ==================================================
# ANALİZ BUTONU VE SONUÇLARIN GÖSTERİLMESİ
# ==================================================
if st.button("📊 Öğrenci Risk Analizini Yap", type="primary"):
    # 1. Puanı hesapla
    puan, durum, gerekce = risk_hesapla(ilk_not, ikinci_not, devamsizlik, odev_yuzdesi, katilim_yuzdesi)
    
    # 2. Raporu göster
    st.subheader(f"📋 {ogrenci_adi} İçin Risk Analiz Raporu")
    st.metric(label="Hesaplanan Risk Puanı", value=f"{puan} / 100")
    
    # 3. Genel Durum
    if durum == "Yüksek Risk": st.error(f"🚨 GENEL DURUM: {durum}")
    elif durum == "Riskli": st.warning(f"⚠️ GENEL DURUM: {durum}")
    elif durum == "Düşük Risk": st.info(f"💡 GENEL DURUM: {durum}")
    else: st.success(f"✅ GENEL DURUM: {durum}")
        
    st.info(f"🔍 **Tespit Edilen Risk Gerekçeleri:** {gerekce}")
    
    # 4. ÖNERİLER (Çoklu Uyarı Sistemi)
    st.subheader("📋 Profil Yorumlama ve Öneriler")
    
    not_ort = (ilk_not + ikinci_not) / 2
    uyari_sayisi = 0

    # 1. Devamsızlık Kontrolü
    if devamsizlik >= 18:
        st.error("🚨 KRİTİK DEVAMSIZLIK: Devamsızlık sınırı aşılmış. Veli ivedilikle aranmalı, devamsızlık mektubu gönderilmeli ve neden araştırılmalıdır.")
        uyari_sayisi += 1
    elif devamsizlik >= 10:
        st.warning("⚠️ DEVAMSIZLIK SINIRDA: Devamsızlık sınırda. Öğrenciye uyarı verilmeli, daha fazla devamsızlık yapmaması için çalışılmalı.")
        uyari_sayisi += 1

    # 2. Akademik ve Ödev Kontrolü
    if not_ort < 50 and odev_yuzdesi < 50:
        st.error("🔴 AKADEMİK & ÖDEV ALARMI: Öğrenci hem derslerde başarısız hem de ödev teslim etmiyor. Birebir ödev koçluğu başlatılmalı ve ek etüt programı planlanmalı.")
        uyari_sayisi += 1
    else:
        if not_ort < 70:
            st.warning("🟠 AKADEMİK DESTEK: Not ortalaması zayıf. Eksik olduğu üniteler belirlenmeli, soru çözüm ofislerine ve etütlere katılım zorunlu tutulmalı.")
            uyari_sayisi += 1
        if odev_yuzdesi < 85:
            st.warning("🟡 ÖDEV DİSİPLİNİ: Ders başarısı veya katılımı iyi olsa da ödev istikrarı düşük. Haftalık ödev takip çizelgesi verilmeli ve veli onayı istenmeli.")
            uyari_sayisi += 1

    # 3. Katılım Kontrolü
    if katilim_yuzdesi < 75:
        st.info("🔵 DERSE KATILIM RİSKİ: Öğrenci derste pasif veya çekingen. Derste söz hakkı verilerek teşvik edilmeli, rehberlik servisiyle özgüven çalışması yapılmalı.")
        uyari_sayisi += 1

    # 4. Hiç Sorun Yoksa
    if uyari_sayisi == 0:
        st.success("🟢 BAŞARILI PROFİL: Tüm kriterler hedef seviyede. Öğrencinin motivasyonunu korumak adına tebrik edilmeli, mevcut çalışma disiplini desteklenmeli.")

# ==================================================
    # GÖRSEL PERFORMANS GRAFİĞİ
    # ==================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Öğrenci Performans Analizi")
    
    # Grafiğe basılacak verileri (notlar, ödev ve katılım) 
    grafik_verisi = pd.DataFrame({
        "Kategoriler": ["1. Sınav", "2. Sınav", "Ödev", "Katılım"],
        "Puanlar": [ilk_not, ikinci_not, odev_yuzdesi, katilim_yuzdesi]
    })
    
    # Streamlit'in kendi interaktif sütun grafiği
    st.bar_chart(grafik_verisi.set_index("Kategoriler"))

# ==================================================
# TOPLU SINIF ANALİZİ (ŞABLON VE YÜKLEME MODÜLÜ)
# ==================================================
st.markdown("---")
st.header("📁 Toplu Sınıf Analizi")
st.write("Sınıfınızın verilerini tek seferde analiz etmek için önce aşağıdaki şablonu indirin, öğrenci verilerini doldurun ve ardından sisteme geri yükleyin.")

# 1. Örnek Şablon Oluşturma ve İndirme Butonu
ornek_veri = {
    "Öğrenci Adı": ["Örnek Öğrenci 1", "Örnek Öğrenci 2"],
    "İlk Not": [100, 70],
    "İkinci Not": [90, 80],
    "Devamsızlık": [2, 12],
    "Ödev Yüzdesi": [100, 60],
    "Katılım Yüzdesi": [95, 50]
}
ornek_df = pd.DataFrame(ornek_veri)
csv_sablon = ornek_df.to_csv(index=False, sep=';').encode('utf-8-sig')

st.download_button(
    label="📥 Örnek Şablonu İndir (CSV)",
    data=csv_sablon,
    file_name='SmartClass_Ornek_Sablon.csv',
    mime='text/csv',
)

st.markdown("<br>", unsafe_allow_html=True) # Araya şık bir boşluk atıyoruz

# 2. Doldurulan Dosyayı Yükleme Alanı
yuklenen_dosya = st.file_uploader("Doldurduğunuz şablonu (Excel veya CSV) buraya sürükleyin", type=["csv", "xlsx"])

if yuklenen_dosya is not None:
    try:
        # Excel veya CSV formatını otomatik anlama
        if yuklenen_dosya.name.endswith('.csv'):
            df_yuklenen = pd.read_csv(yuklenen_dosya)
        else:
            df_yuklenen = pd.read_excel(yuklenen_dosya)
            
        st.success("✅ Dosya başarıyla okundu! Yüklenen liste:")
        st.dataframe(df_yuklenen)
        
    except Exception as e:
        st.error("🚨 Dosya okunurken bir hata oluştu. Lütfen indirdiğiniz şablondaki sütun isimlerini değiştirmediğinizden emin olun.")

import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import streamlit as st
import matplotlib.pyplot as plt
from sklearn import tree
from streamlit_extras.let_it_rain import rain
import plotly.graph_objects as go


st.set_page_config(
    page_title="SmartClass Twin",
    page_icon="🏫",
    layout="centered"
)


# ---------------------------------------------------------
# BAŞLIK VE LOGOLAR
# ---------------------------------------------------------

col_logo_sol, col_baslik, col_logo_sag = st.columns([1, 3, 1])

with col_logo_sol:
    st.image("kesapfenlogo-removebg-preview.png", width=90)

with col_baslik:
    st.markdown(
        "<h2 style='text-align: center; color: #FF4B4B; margin-bottom: 0;'>"
        "🏫 SmartClass Twin"
        "</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<h4 style='text-align: center; font-style: italic;'>"
        "Öğrenci Risk Analiz Paneli"
        "</h4>",
        unsafe_allow_html=True
    )

with col_logo_sag:
    st.image("meblogo-removebg-preview.png", width=120)

st.markdown("---")


# ---------------------------------------------------------
# GİRİŞ SİSTEMİ
# ---------------------------------------------------------

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False


if not st.session_state["giris_yapildi"]:

    st.markdown(
        "<h3 style='text-align: center;'>🔐 Sistem Girişi</h3>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")

        if st.button(
            "Sisteme Giriş Yap",
            use_container_width=True,
            type="primary"
        ):
            if k_adi == "ogretmen" and sifre == "1234":
                st.session_state["giris_yapildi"] = True
                st.rerun()
            else:
                st.error("🚨 Hatalı kullanıcı adı veya şifre!")


else:

    st.write(
        "Öğrencinin verilerini girerek yapay zeka ve ağırlıklı "
        "risk puanı analizini anında görebilirsiniz."
    )


    # =========================================================
    # AKADEMİK RİSK HESAPLAMA MOTORU
    # =========================================================

    def risk_hesapla(
        ilk_not,
        ikinci_not,
        devamsizlik,
        odev_yuzdesi,
        katilim_yuzdesi
    ):

        nedenler = []

        not_ort = (ilk_not + ikinci_not) / 2
        performans_dususu = ilk_not - ikinci_not

        puan = (
            90.0
            + (devamsizlik * 0.5)
            - (not_ort * 0.5)
            - (odev_yuzdesi * 0.2)
            - (katilim_yuzdesi * 0.2)
            + (performans_dususu * 0.1)
        )

        if puan > 100:
            puan = 100

        if puan < 0:
            puan = 0

        puan = round(puan, 2)

        if not_ort < 50:
            nedenler.append("Akademik Yüksek Risk")

        elif not_ort < 70:
            nedenler.append("Akademik Düşük Risk")

        elif ikinci_not < 70:
            nedenler.append(
                "2. Sınav Kaynaklı Akademik Düşük Risk"
            )

        if devamsizlik >= 18:
            nedenler.append("Kritik Devamsızlık Riski")

        elif devamsizlik >= 10:
            nedenler.append(
                "Devamsızlık Kaynaklı Düşük Risk"
            )

        if odev_yuzdesi < 50:
            nedenler.append("Ödev Kaynaklı Yüksek Risk")

        elif odev_yuzdesi < 85:
            nedenler.append("Ödev Kaynaklı Düşük Risk")

        if katilim_yuzdesi < 50:
            nedenler.append(
                "Katılım Kaynaklı Yüksek Risk"
            )

        elif katilim_yuzdesi < 75:
            nedenler.append(
                "Katılım Kaynaklı Düşük Risk"
            )

        if performans_dususu > 0:
            nedenler.append(
                f"Performans Düşüşü ({ilk_not} -> {ikinci_not})"
            )

        if puan >= 85:
            durum = "Kritik Risk"

        elif puan >= 50:
            durum = "Yüksek Risk"

        elif puan >= 30:
            durum = "Riskli"

        elif puan >= 15:
            durum = "Düşük Risk"

        else:
            durum = "Risk Yok"

        gerekce = (
            ", ".join(nedenler)
            if nedenler
            else "Belirgin bir risk faktörü bulunamadı."
        )

        return puan, durum, gerekce


    # =========================================================
    # SOSYAL RİSK HESAPLAMA MOTORU
    # =========================================================

    def sosyal_risk_hesapla(
        grup_katilimi,
        akran_destegi,
        arkadas_baglantisi,
        ogretmen_iletisimi,
        sosyal_izolasyon,
        oturma_konumu
    ):

        nedenler = []
        oneriler = []

        if grup_katilimi <= 2:
            grup_riski = 90
            nedenler.append(
                "Grup çalışmalarına katılım düşüktür."
            )
            oneriler.append(
                "Küçük grup görevlerinde sorumluluk verilebilir."
            )

        elif grup_katilimi == 3:
            grup_riski = 60

        elif grup_katilimi == 4:
            grup_riski = 30

        else:
            grup_riski = 10

        if akran_destegi <= 2:
            akran_riski = 90
            nedenler.append(
                "Akran desteği sınırlıdır."
            )
            oneriler.append(
                "Destekleyici bir akranla eşleştirme düşünülebilir."
            )

        elif akran_destegi == 3:
            akran_riski = 60

        elif akran_destegi == 4:
            akran_riski = 30

        else:
            akran_riski = 10

        if arkadas_baglantisi == 0:
            baglanti_riski = 90
            nedenler.append(
                "Sınıf içi arkadaş bağlantısı düşüktür."
            )
            oneriler.append(
                "Grup içinde aktif bir rol verilmesi düşünülebilir."
            )

        elif arkadas_baglantisi <= 2:
            baglanti_riski = 60
            nedenler.append(
                "Sınıf içi arkadaş bağlantısı düşüktür."
            )
            oneriler.append(
                "Grup içinde aktif bir rol verilmesi düşünülebilir."
            )

        elif arkadas_baglantisi <= 4:
            baglanti_riski = 30

        else:
            baglanti_riski = 10

        if ogretmen_iletisimi <= 2:
            iletisim_riski = 90
            nedenler.append(
                "Öğretmenle iletişim düzeyi düşüktür."
            )
            oneriler.append(
                "Kısa bireysel öğretmen görüşmeleri planlanabilir."
            )

        elif ogretmen_iletisimi == 3:
            iletisim_riski = 60

        elif ogretmen_iletisimi == 4:
            iletisim_riski = 30

        else:
            iletisim_riski = 10

        if sosyal_izolasyon >= 5:
            izolasyon_riski = 90
            nedenler.append(
                "Sosyal izolasyon belirtisi gözlenmektedir."
            )
            oneriler.append(
                "Rehberlik servisi tarafından gözlem önerilebilir."
            )

        elif sosyal_izolasyon == 4:
            izolasyon_riski = 70
            nedenler.append(
                "Sosyal izolasyon belirtisi gözlenmektedir."
            )
            oneriler.append(
                "Rehberlik servisi tarafından gözlem önerilebilir."
            )

        elif sosyal_izolasyon == 3:
            izolasyon_riski = 50

        else:
            izolasyon_riski = 20

        oturma_riskleri = {
            "Ön": 10,
            "Orta": 30,
            "Kenar": 50,
            "Arka": 60
        }

        oturma_riski = oturma_riskleri.get(
            oturma_konumu,
            30
        )

        if oturma_konumu == "Arka":
            nedenler.append(
                "Arka sıradaki konum sınıf içi etkileşim "
                "açısından ayrıca izlenebilir."
            )
            oneriler.append(
                "Öğrencinin farklı bir oturma konumundaki "
                "etkileşimi gözlemlenebilir."
            )

        sosyal_puan = (
            grup_riski * 0.20
            + akran_riski * 0.20
            + baglanti_riski * 0.25
            + iletisim_riski * 0.15
            + izolasyon_riski * 0.15
            + oturma_riski * 0.05
        )

        sosyal_puan = round(sosyal_puan, 2)

        if sosyal_puan >= 70:
            sosyal_durum = "Yüksek Sosyal Risk"

        elif sosyal_puan >= 40:
            sosyal_durum = "Orta Sosyal Risk"

        else:
            sosyal_durum = "Düşük Sosyal Risk"

        if not nedenler:
            if sosyal_durum == "Yüksek Sosyal Risk":
                nedenler = [
                    "Sosyal risk puanı yüksek düzeydedir. Tek bir baskın neden yerine, "
                    "birden fazla sosyal göstergenin birleşik etkisi izlenmelidir."
                ]
            elif sosyal_durum == "Orta Sosyal Risk":
                nedenler = [
                    "Sosyal etkileşim göstergeleri genel olarak orta düzeyde destek ihtiyacına işaret etmektedir."
                ]
            else:
                nedenler = [
                    "Belirgin bir sosyal risk göstergesi bulunmamaktadır."
                ]

        if not oneriler:
            if sosyal_durum == "Yüksek Sosyal Risk":
                oneriler = [
                    "Öğretmen gözlemiyle birlikte sosyal etkileşim göstergelerinin yakından izlenmesi önerilir."
                ]
            elif sosyal_durum == "Orta Sosyal Risk":
                oneriler = [
                    "Öğrencinin sosyal etkileşimi düzenli olarak izlenebilir ve gerekli görülen alanlarda destek sağlanabilir."
                ]
            else:
                oneriler = [
                    "Mevcut sosyal uyumun izlenerek desteklenmesi önerilir."
                ]

        risk_bilesenleri = {
            "Grup Katılımı Riski": grup_riski,
            "Akran Desteği Riski": akran_riski,
            "Arkadaş Bağlantısı Riski": baglanti_riski,
            "Öğretmen İletişimi Riski": iletisim_riski,
            "Sosyal İzolasyon Riski": izolasyon_riski,
            "Oturma Konumu Riski": oturma_riski
        }

        return (
            sosyal_puan,
            sosyal_durum,
            nedenler,
            oneriler,
            risk_bilesenleri
        )



    # =========================================================
    # GENEL DESTEK DURUMU
    # Akademik ve sosyal risk ayrı tutulur; burada yalnızca
    # öğretmenin önceliklendirmesine yardımcı olan ortak özet üretilir.
    # =========================================================

    def genel_destek_durumu_hesapla(akademik_durum, sosyal_durum):
        akademik_yuksek = akademik_durum in [
            "Kritik Risk",
            "Yüksek Risk"
        ]

        akademik_izleme = akademik_durum in [
            "Riskli",
            "Düşük Risk"
        ]

        sosyal_yuksek = sosyal_durum == "Yüksek Sosyal Risk"
        sosyal_izleme = sosyal_durum == "Orta Sosyal Risk"

        if akademik_yuksek and sosyal_yuksek:
            return (
                "Çoklu Destek",
                "🚨",
                f"Akademik durum '{akademik_durum}', sosyal durum ise '{sosyal_durum}' olarak hesaplandı. "
                "Her iki alanın birlikte öğretmen tarafından değerlendirilmesi önerilir."
            )

        elif akademik_yuksek:
            return (
                "Akademik Destek",
                "📚",
                f"Akademik durum '{akademik_durum}', sosyal durum ise '{sosyal_durum}'. "
                "Önceliğin akademik risk göstergelerine verilmesi önerilir."
            )

        elif sosyal_yuksek:
            return (
                "Sosyal Destek",
                "🤝",
                f"Akademik durum '{akademik_durum}', sosyal durum ise '{sosyal_durum}'. "
                "Önceliğin sosyal etkileşim göstergelerine verilmesi önerilir."
            )

        elif akademik_izleme or sosyal_izleme:
            return (
                "İzleme",
                "👀",
                f"Akademik durum '{akademik_durum}', sosyal durum ise '{sosyal_durum}'. "
                "Yüksek düzeyde ortak risk görülmese de öğrencinin gelişiminin düzenli izlenmesi önerilir."
            )

        else:
            return (
                "Rutin Takip",
                "✅",
                f"Akademik durum '{akademik_durum}', sosyal durum ise '{sosyal_durum}'. "
                "Mevcut göstergelerde yüksek destek ihtiyacı görülmemektedir."
            )


    # =========================================================
    # OTURMA DÜZENİ ÖNERİSİ
    # =========================================================

    def oturma_onerisi_yap(
        ilk_not,
        ikinci_not,
        duzen2
    ):

        performans_egrisi = ilk_not - ikinci_not

        mesaj = ""
        ikon = "💡"
        durum_analizi = ""

        if performans_egrisi > 0:

            durum_analizi = (
                f"📉 Performans Eğrisi: +{performans_egrisi} "
                "(Düşüş Tespit Edildi)"
            )

            if duzen2 == "Geleneksel Sıra":

                mesaj = (
                    "Geleneksel düzenin kullanıldığı dönemde "
                    "performans düşüşü gözlenmiştir. "
                    "Sosyal etkileşimi artırabilecek "
                    "'Yarım Daire' veya 'Küme Düzeni' "
                    "alternatifleri öğretmen tarafından "
                    "değerlendirilebilir."
                )

                ikon = "🚨"

            elif duzen2 == "Yarım Daire":

                mesaj = (
                    "Yarım daire düzeninin kullanıldığı dönemde "
                    "performans düşüşü gözlenmiştir. "
                    "Farklı bir etkileşim senaryosu olarak "
                    "'Küme Düzeni' denenebilir."
                )

                ikon = "⚠️"

            else:

                mesaj = (
                    "Küme düzeninin kullanıldığı dönemde de "
                    "performans düşüşü gözlenmiştir. "
                    "Oturma düzeninin yanında akademik, sosyal "
                    "ve rehberlik faktörlerinin de "
                    "değerlendirilmesi önerilir."
                )

                ikon = "🛑"

        elif performans_egrisi < 0:

            durum_analizi = (
                f"📈 Performans Eğrisi: {performans_egrisi} "
                "(Artış Tespit Edildi)"
            )

            mesaj = (
                f"'{duzen2}' düzeninin kullanıldığı dönemde "
                "performans artışı gözlenmiştir. "
                "Ancak bu artışın yalnızca oturma düzeninden "
                "kaynaklandığı varsayılmamalıdır. "
                "Mevcut düzen bir süre daha izlenebilir."
            )

            ikon = "✅"

        else:

            durum_analizi = (
                "📊 Performans Eğrisi: 0 "
                "(Değişim Yok)"
            )

            mesaj = (
                "Başarı durumu stabil görünmektedir. "
                "Öğrencinin etkileşimini artırmak amacıyla "
                "alternatif oturma düzenleri öğretmen "
                "tarafından değerlendirilebilir."
            )

            ikon = "ℹ️"

        return durum_analizi, mesaj, ikon


    # =========================================================
    # KARAR AĞACI MODELİ
    # =========================================================

    @st.cache_resource
    def modeli_egit():

        veri_egitim = {

            "Devamsizlik":
                [1, 5, 0, 4, 1, 6, 2, 12],

            "Sinav_1":
                [80, 50, 95, 60, 75, 40, 90, 55],

            "Sinav_2":
                [90, 40, 85, 40, 65, 20, 92, 45],

            "Odev_Tamamlama_Yuzdesi":
                [90, 40, 100, 50, 80, 20, 95, 30],

            "Katilim_Yuzdesi":
                [85, 45, 95, 55, 75, 30, 90, 40],

            "Risk_Durumu":
                [0, 1, 0, 1, 0, 1, 0, 1]
        }

        df = pd.DataFrame(veri_egitim)

        df["Not_Ortalamasi"] = (
            df["Sinav_1"] + df["Sinav_2"]
        ) / 2

        df["Performans_Dususu"] = (
            df["Sinav_1"] - df["Sinav_2"]
        )

        X = df[
            [
                "Devamsizlik",
                "Not_Ortalamasi",
                "Odev_Tamamlama_Yuzdesi",
                "Katilim_Yuzdesi",
                "Performans_Dususu"
            ]
        ]

        y = df["Risk_Durumu"]

        model = DecisionTreeClassifier(
            max_depth=3,
            random_state=42
        )

        model.fit(X, y)

        return model


    model = modeli_egit()


    # =========================================================
    # SIDEBAR
    # =========================================================

    st.sidebar.header("⚙️ Veri Giriş Paneli")

    ogrenci_adi = st.sidebar.text_input(
        "Öğrenci Tanımlayıcı",
        value="Öğrenci Örnek"
    )

    st.sidebar.subheader("📚 Akademik Veriler")

    ilk_not = st.sidebar.number_input(
        "1. Sınav Notu",
        0,
        100,
        95
    )

    duzen1 = st.sidebar.selectbox(
        "1. Sınav Dönemi Oturma Düzeni",
        [
            "Geleneksel Sıra",
            "Yarım Daire",
            "Küme Düzeni"
        ]
    )

    ikinci_not = st.sidebar.number_input(
        "2. Sınav Notu",
        0,
        100,
        85
    )

    duzen2 = st.sidebar.selectbox(
        "2. Sınav Dönemi Oturma Düzeni",
        [
            "Geleneksel Sıra",
            "Yarım Daire",
            "Küme Düzeni"
        ]
    )

    st.sidebar.markdown("---")

    odev_yuzdesi = st.sidebar.slider(
        "Ödev Tamamlama (%)",
        0,
        100,
        100
    )

    katilim_yuzdesi = st.sidebar.slider(
        "Derse Katılım (%)",
        0,
        100,
        90
    )

    devamsizlik = st.sidebar.number_input(
        "Devamsızlık (Gün)",
        0,
        100,
        5
    )

    # =========================================================
    # SOSYAL ETKİLEŞİM GİRİŞLERİ
    # =========================================================

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "🤝 Sosyal Etkileşim Verileri"
    )

    grup_katilimi = st.sidebar.slider(
        "Grup Çalışmasına Katılım",
        0,
        5,
        3,
        help="0 = hiç katılmıyor, 5 = çok aktif katılıyor"
    )

    akran_destegi = st.sidebar.slider(
        "Akran Desteği",
        0,
        5,
        3,
        help="0 = destek yok, 5 = çok güçlü destek"
    )

    arkadas_baglantisi = st.sidebar.slider(
        "Arkadaş Bağlantısı",
        0,
        5,
        3,
        help="0 = bağlantı yok, 5 = güçlü sosyal bağlantı"
    )

    ogretmen_iletisimi = st.sidebar.slider(
        "Öğretmenle İletişim",
        0,
        5,
        3,
        help="0 = çok düşük, 5 = çok yüksek"
    )

    sosyal_izolasyon = st.sidebar.slider(
        "Sosyal İzolasyon",
        0,
        5,
        1,
        help="0 = izolasyon yok, 5 = çok yüksek izolasyon"
    )

    oturma_konumu = st.sidebar.selectbox(
        "Oturma Konumu",
        [
            "Ön",
            "Orta",
            "Kenar",
            "Arka"
        ]
    )

    st.sidebar.markdown("---")

    if st.sidebar.button(
        "🚪 Sistemden Çıkış Yap"
    ):

        st.session_state["giris_yapildi"] = False
        st.rerun()


    # =========================================================
    # TEK ÖĞRENCİ ANALİZİ
    # =========================================================

    if st.button(
        "📊 Öğrenci Risk Analizini Yap",
        type="primary",
        use_container_width=True
    ):

        puan, durum, gerekce = risk_hesapla(
            ilk_not,
            ikinci_not,
            devamsizlik,
            odev_yuzdesi,
            katilim_yuzdesi
        )

        # YENİ: Aynı buton sosyal risk motorunu da çalıştırıyor
        sosyal_puan, sosyal_durum, sosyal_nedenler, sosyal_oneriler, sosyal_bilesenler = sosyal_risk_hesapla(
            grup_katilimi,
            akran_destegi,
            arkadas_baglantisi,
            ogretmen_iletisimi,
            sosyal_izolasyon,
            oturma_konumu
        )

        genel_destek, genel_destek_ikon, genel_destek_aciklama = genel_destek_durumu_hesapla(
            durum,
            sosyal_durum
        )

        egri_metni, oneri_mesaji, oneri_ikon = (
            oturma_onerisi_yap(
                ilk_not,
                ikinci_not,
                duzen2
            )
        )

        not_ort = (
            ilk_not + ikinci_not
        ) / 2

        performans_dususu = (
            ilk_not - ikinci_not
        )

        ai_girdi = pd.DataFrame({

            "Devamsizlik":
                [devamsizlik],

            "Not_Ortalamasi":
                [not_ort],

            "Odev_Tamamlama_Yuzdesi":
                [odev_yuzdesi],

            "Katilim_Yuzdesi":
                [katilim_yuzdesi],

            "Performans_Dususu":
                [performans_dususu]
        })

        ai_tahmin = model.predict(
            ai_girdi
        )[0]

        risk_index = list(
            model.classes_
        ).index(1)

        risk_olasiligi = (
            model.predict_proba(
                ai_girdi
            )[0][risk_index]
            * 100
        )

        st.subheader(
            f"📋 {ogrenci_adi} İçin Risk Analiz Raporu"
        )

        st.markdown("### 🧭 Öğrenci Genel Risk Profili")

        col_akademik, col_sosyal = st.columns(2)

        with col_akademik:
            st.metric(
                label="📚 Akademik Risk Puanı",
                value=f"{puan} / 100"
            )

            if durum in ["Kritik Risk", "Yüksek Risk"]:
                st.error(f"🚨 {durum}")

            elif durum == "Riskli":
                st.warning(f"⚠️ {durum}")

            elif durum == "Düşük Risk":
                st.info(f"💡 {durum}")

            else:
                st.success(f"✅ {durum}")

        with col_sosyal:
            st.metric(
                label="🤝 Sosyal Risk Puanı",
                value=f"{sosyal_puan} / 100"
            )

            if sosyal_durum == "Yüksek Sosyal Risk":
                st.error(f"🚨 {sosyal_durum}")

            elif sosyal_durum == "Orta Sosyal Risk":
                st.warning(f"⚠️ {sosyal_durum}")

            else:
                st.success(f"✅ {sosyal_durum}")

        st.markdown("#### 🎯 Genel Destek Durumu")

        if genel_destek == "Çoklu Destek":
            st.error(
                f"{genel_destek_ikon} **{genel_destek}** — "
                f"{genel_destek_aciklama}"
            )

        elif genel_destek in ["Akademik Destek", "Sosyal Destek"]:
            st.warning(
                f"{genel_destek_ikon} **{genel_destek}** — "
                f"{genel_destek_aciklama}"
            )

        elif genel_destek == "İzleme":
            st.info(
                f"{genel_destek_ikon} **{genel_destek}** — "
                f"{genel_destek_aciklama}"
            )

        else:
            st.success(
                f"{genel_destek_ikon} **{genel_destek}** — "
                f"{genel_destek_aciklama}"
            )

        if durum == "Risk Yok" and sosyal_durum == "Düşük Sosyal Risk":
            rain(
                emoji="🎉",
                font_size=40,
                falling_speed=5,
                animation_length=3
            )

        st.caption(
            "Akademik risk ve sosyal risk birbirinden ayrı hesaplanır. "
            "Sosyal risk puanı öğrenciyi etiketlemek için değil, öğretmenin "
            "destek ihtiyacını erken fark etmesine yardımcı olmak için kullanılır."
        )

        st.subheader(
            "🤖 Akademik Yapay Zekâ Ön Tahmini"
        )

        if ai_tahmin == 1:

            st.warning(
                "Karar ağacı modeline göre öğrenci "
                "risk grubunda olabilir. "
                f"Model risk skoru: %{risk_olasiligi:.1f}"
            )

        else:

            st.success(
                "Karar ağacı modeline göre öğrenci "
                "düşük risk grubunda görünüyor. "
                f"Model risk skoru: %{risk_olasiligi:.1f}"
            )

        st.caption(
            "Not: Bu karar ağacı tahmini yalnızca akademik veriler üzerinden çalışan "
            "destekleyici bir ön tahmindir. Sosyal risk analizi ayrı bir ağırlıklı modelle "
            "hesaplanır. Nihai değerlendirme öğretmenin pedagojik yorumuyla yapılır."
        )

        with st.expander(
            "🌳 Karar Ağacı Modelini Görüntüle"
        ):

            fig_tree, ax_tree = plt.subplots(
                figsize=(12, 6)
            )

            tree.plot_tree(
                model,
                feature_names=[
                    "Devamsızlık",
                    "Not Ortalaması",
                    "Ödev Yüzdesi",
                    "Katılım Yüzdesi",
                    "Performans Düşüşü"
                ],
                class_names=[
                    "Risk Yok",
                    "Risk Var"
                ],
                filled=True,
                rounded=True,
                ax=ax_tree
            )

            st.pyplot(fig_tree)

        st.info(
            f"🔍 **Tespit Edilen Akademik Risk Gerekçeleri:** "
            f"{gerekce}"
        )

        # -----------------------------------------------------
        # SOSYAL ETKİLEŞİM ANALİZİ
        # -----------------------------------------------------

        st.markdown("---")
        st.subheader("🤝 Sosyal Etkileşim Analizi")

        if sosyal_durum == "Yüksek Sosyal Risk":
            st.error(
                f"🚨 **Sosyal Değerlendirme:** {sosyal_puan}/100 — {sosyal_durum}"
            )
        elif sosyal_durum == "Orta Sosyal Risk":
            st.warning(
                f"⚠️ **Sosyal Değerlendirme:** {sosyal_puan}/100 — {sosyal_durum}"
            )
        else:
            st.success(
                f"✅ **Sosyal Değerlendirme:** {sosyal_puan}/100 — {sosyal_durum}"
            )

        sosyal_sol, sosyal_sag = st.columns([1, 1])

        with sosyal_sol:
            st.markdown("**🔎 Sosyal Risk Nedenleri**")
            for neden in sosyal_nedenler:
                st.write(f"• {neden}")

        with sosyal_sag:
            st.markdown("**🧩 Sosyal Müdahale Önerileri**")
            for oneri in sosyal_oneriler:
                st.write(f"• {oneri}")

        sirali_bilesenler = sorted(
            sosyal_bilesenler.items(),
            key=lambda x: x[1],
            reverse=True
        )
        en_etkili_uc = sirali_bilesenler[:3]

        st.info(
            "📌 **Öne çıkan sosyal göstergeler:** "
            + ", ".join([f"{ad}: {deger}/100" for ad, deger in en_etkili_uc])
        )

        st.markdown("**📊 Sosyal Risk Bileşenleri**")

        sosyal_grafik_df = pd.DataFrame(
            {
                "Risk Bileşeni": list(sosyal_bilesenler.keys()),
                "Risk Puanı": list(sosyal_bilesenler.values())
            }
        )

        kisa_etiketler = {
            "Grup Katılımı Riski": "Grup Katılımı",
            "Akran Desteği Riski": "Akran Desteği",
            "Arkadaş Bağlantısı Riski": "Arkadaş Bağlantısı",
            "Öğretmen İletişimi Riski": "Öğretmen İletişimi",
            "Sosyal İzolasyon Riski": "Sosyal İzolasyon",
            "Oturma Konumu Riski": "Oturma Konumu"
        }

        sosyal_grafik_gosterim = sosyal_grafik_df.copy()
        sosyal_grafik_gosterim["Gösterim"] = sosyal_grafik_gosterim["Risk Bileşeni"].map(kisa_etiketler)

        fig_sosyal = go.Figure(
            go.Bar(
                x=sosyal_grafik_gosterim["Risk Puanı"],
                y=sosyal_grafik_gosterim["Gösterim"],
                orientation="h"
            )
        )

        fig_sosyal.update_layout(
            xaxis_title="Risk Puanı",
            yaxis_title="",
            xaxis=dict(range=[0, 100]),
            margin=dict(l=20, r=20, t=10, b=20),
            height=360
        )

        st.plotly_chart(
            fig_sosyal,
            use_container_width=True
        )

        with st.expander("🧮 Sosyal risk hesabının ayrıntılarını görüntüle"):
            st.write(
                "Sosyal risk; grup katılımı (%20), akran desteği (%20), "
                "arkadaş bağlantısı (%25), öğretmen iletişimi (%15), "
                "sosyal izolasyon (%15) ve oturma konumu (%5) "
                "bileşenlerinin ağırlıklı toplamıyla hesaplanır."
            )
            st.dataframe(
                sosyal_grafik_df,
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "Not: Oturma konumu tek başına sosyal risk göstergesi olarak "
            "yorumlanmaz; toplam değerlendirmede düşük ağırlıklı destekleyici "
            "bir değişken olarak kullanılır."
        )

        st.subheader(
            "🎯 Stratejik Yerleşim Önerisi"
        )

        st.info(
            f"**{egri_metni}**"
        )

        st.success(
            f"{oneri_ikon} "
            f"**Yerleşim Tavsiyesi:** "
            f"{oneri_mesaji}"
        )

        st.subheader(
            "📋 Profil Yorumlama ve Öneriler"
        )

        uyari_sayisi = 0

        if devamsizlik >= 18:

            st.error(
                "🚨 KRİTİK DEVAMSIZLIK: "
                "Devamsızlık sınırı aşılmış. "
                "Veli ivedilikle aranmalı."
            )

            uyari_sayisi += 1

        elif devamsizlik >= 10:

            st.warning(
                "⚠️ DEVAMSIZLIK SINIRDA: "
                "Devamsızlık sınırda. "
                "Öğrenciye uyarı verilmeli."
            )

            uyari_sayisi += 1

        if not_ort < 50 and odev_yuzdesi < 50:

            st.error(
                "🔴 AKADEMİK & ÖDEV ALARMI: "
                "Öğrenci başarısız ve ödev teslim etmiyor. "
                "Ek etüt planlanmalı."
            )

            uyari_sayisi += 1

        else:

            if not_ort < 70:

                st.warning(
                    "🟠 AKADEMİK DESTEK: "
                    "Not ortalaması zayıf. "
                    "Soru çözüm ofislerine katılım "
                    "önerilebilir."
                )

                uyari_sayisi += 1

            if odev_yuzdesi < 85:

                st.warning(
                    "🟡 ÖDEV DİSİPLİNİ: "
                    "Ödev istikrarı düşük. "
                    "Haftalık ödev takip çizelgesi "
                    "uygulanabilir."
                )

                uyari_sayisi += 1

        if katilim_yuzdesi < 75:

            st.info(
                "🔵 DERSE KATILIM RİSKİ: "
                "Öğrenci derste pasif olabilir. "
                "Derste söz hakkı verilerek "
                "teşvik edilebilir."
            )

            uyari_sayisi += 1

        if uyari_sayisi == 0:

            st.success(
                "🟢 BAŞARILI PROFİL: "
                "Tüm kriterler hedef seviyede. "
                "Mevcut çalışma düzeninin "
                "desteklenmesi önerilir."
            )

        st.markdown("---")

        st.subheader(
            "📊 Öğrenci Performans & Profil Radarı"
        )

        col_grafik1, col_grafik2 = st.columns(2)

        with col_grafik1:

            st.markdown(
                "**Temel Puanlar (Sütun)**"
            )

            grafik_verisi = pd.DataFrame({

                "Kategoriler": [
                    "1. Sınav",
                    "2. Sınav",
                    "Ödev",
                    "Katılım"
                ],

                "Puanlar": [
                    ilk_not,
                    ikinci_not,
                    odev_yuzdesi,
                    katilim_yuzdesi
                ]
            })

            st.bar_chart(
                grafik_verisi.set_index(
                    "Kategoriler"
                )
            )

        with col_grafik2:

            st.markdown(
                "**Yetkinlik Ağı (Radar)**"
            )

            devam_puani = (
                100 - (devamsizlik * 2)
            )

            if devam_puani < 0:
                devam_puani = 0

            kategoriler = [
                "1. Sınav",
                "2. Sınav",
                "Ödev",
                "Katılım",
                "Devamlılık"
            ]

            degerler = [
                ilk_not,
                ikinci_not,
                odev_yuzdesi,
                katilim_yuzdesi,
                devam_puani
            ]

            kategoriler_kapali = (
                kategoriler
                + [kategoriler[0]]
            )

            degerler_kapali = (
                degerler
                + [degerler[0]]
            )

            fig = go.Figure(
                data=go.Scatterpolar(
                    r=degerler_kapali,
                    theta=kategoriler_kapali,
                    fill="toself",
                    line_color="#FF4B4B"
                )
            )

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )
                ),
                showlegend=False,
                margin=dict(
                    l=40,
                    r=40,
                    t=20,
                    b=20
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


    # =========================================================
    # TOPLU SINIF ANALİZİ
    # =========================================================

    st.markdown("---")

    st.header(
        "📁 Toplu Sınıf Analizi"
    )

    st.write(
        "Sınıfınızın verilerini tek seferde analiz etmek "
        "için önce aşağıdaki şablonu indirin, öğrenci "
        "verilerini doldurun ve ardından sisteme geri yükleyin."
    )

    ornek_veri = {

        "Öğrenci Adı":
            [
                "Öğrenci 1",
                "Öğrenci 2",
                "Öğrenci 3",
                "Öğrenci 4"
            ],

        "İlk Not":
            [95, 40, 85, 95],

        "İkinci Not":
            [100, 35, 90, 90],

        "Devamsızlık":
            [0, 15, 22, 2],

        "Ödev Yüzdesi":
            [100, 40, 90, 10],

        "Katılım Yüzdesi":
            [100, 30, 85, 20]
    }

    ornek_df = pd.DataFrame(
        ornek_veri
    )

    csv_sablon = (
        ornek_df
        .to_csv(
            index=False,
            sep=";"
        )
        .encode("utf-8-sig")
    )

    st.download_button(
        label="📥 Örnek Şablonu İndir (CSV)",
        data=csv_sablon,
        file_name="SmartClass_Ornek_Sablon.csv",
        mime="text/csv"
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    yuklenen_dosya = st.file_uploader(
        "Doldurduğunuz şablonu buraya sürükleyin",
        type=[
            "csv",
            "xlsx"
        ]
    )

    if yuklenen_dosya is not None:

        try:

            if yuklenen_dosya.name.endswith(
                ".csv"
            ):

                df_yuklenen = pd.read_csv(
                    yuklenen_dosya,
                    sep=";"
                )

            else:

                df_yuklenen = pd.read_excel(
                    yuklenen_dosya
                )

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

                risk_puanlari.append(
                    puan
                )

                durumlar.append(
                    durum
                )

                gerekceler.append(
                    gerekce
                )

            df_yuklenen[
                "Risk Puanı"
            ] = risk_puanlari

            df_yuklenen[
                "Risk Durumu"
            ] = durumlar

            df_yuklenen[
                "Yapay Zeka Önerisi"
            ] = gerekceler

            st.success(
                "✅ Sınıf verileri analiz edildi."
            )

            toplam_ogrenci = len(
                df_yuklenen
            )

            kritik_risk_sayisi = (
                durumlar.count(
                    "Kritik Risk"
                )
            )

            yuksek_risk_sayisi = (
                durumlar.count(
                    "Yüksek Risk"
                )
            )

            riskli_sayisi = (
                durumlar.count(
                    "Riskli"
                )
            )

            dusuk_risk_sayisi = (
                durumlar.count(
                    "Düşük Risk"
                )
            )

            risk_yok_sayisi = (
                durumlar.count(
                    "Risk Yok"
                )
            )

            st.subheader(
                "📊 Sınıf Genel Risk İstatistikleri"
            )

            m1, m2, m3, m4, m5, m6 = st.columns(6)

            m1.metric(
                "Mevcut",
                toplam_ogrenci
            )

            m2.metric(
                "🚨 Kritik",
                kritik_risk_sayisi
            )

            m3.metric(
                "🚨 Yüksek",
                yuksek_risk_sayisi
            )

            m4.metric(
                "⚠️ Riskli",
                riskli_sayisi
            )

            m5.metric(
                "💡 Düşük",
                dusuk_risk_sayisi
            )

            m6.metric(
                "✅ Yok",
                risk_yok_sayisi
            )

            st.markdown(
                "<br>",
                unsafe_allow_html=True
            )

            def renk_ver(val):

                if val == "Kritik Risk":
                    return (
                        "background-color: "
                        "rgba(220, 20, 60, 0.6)"
                    )

                elif val == "Yüksek Risk":
                    return (
                        "background-color: "
                        "rgba(255, 75, 75, 0.4)"
                    )

                elif val == "Riskli":
                    return (
                        "background-color: "
                        "rgba(255, 165, 0, 0.4)"
                    )

                elif val == "Düşük Risk":
                    return (
                        "background-color: "
                        "rgba(255, 255, 0, 0.2)"
                    )

                elif val == "Risk Yok":
                    return (
                        "background-color: "
                        "rgba(0, 128, 0, 0.4)"
                    )

                return ""

            if hasattr(
                df_yuklenen.style,
                "map"
            ):

                st.dataframe(
                    df_yuklenen.style.map(
                        renk_ver,
                        subset=["Risk Durumu"]
                    )
                )

            else:

                st.dataframe(
                    df_yuklenen.style.applymap(
                        renk_ver,
                        subset=["Risk Durumu"]
                    )
                )

            csv_analiz = (
                df_yuklenen.to_csv(
                    index=False,
                    sep=";"
                )
            )

            ozet_rapor_metni = (

                "\n\n"

                "=== SINIF GENEL RİSK ÖZETİ ===\n"

                f"Toplam Analiz Edilen Öğrenci Sayısı;"
                f"{toplam_ogrenci}\n"

                f"🚨 Kritik Riskli Öğrenci Sayısı;"
                f"{kritik_risk_sayisi}\n"

                f"🚨 Yüksek Riskli Öğrenci Sayısı;"
                f"{yuksek_risk_sayisi}\n"

                f"⚠️ Riskli Öğrenci Sayısı;"
                f"{riskli_sayisi}\n"

                f"💡 Düşük Riskli Öğrenci Sayısı;"
                f"{dusuk_risk_sayisi}\n"

                f"✅ Risk Faktörü Bulunmayan Öğrenci Sayısı;"
                f"{risk_yok_sayisi}\n"
            )

            indirme_verisi = (
                csv_analiz
                + ozet_rapor_metni
            ).encode(
                "utf-8-sig"
            )

            st.markdown(
                "<br>",
                unsafe_allow_html=True
            )

            st.download_button(
                label=(
                    "📥 Analiz Raporunu İndir "
                    "(Özet Verileri Dahil)"
                ),
                data=indirme_verisi,
                file_name=(
                    "SmartClass_Sınıf_Analiz_Raporu.csv"
                ),
                mime="text/csv"
            )

        except Exception as e:

            st.error(
                f"🚨 Hata detayı: {e}"
            )

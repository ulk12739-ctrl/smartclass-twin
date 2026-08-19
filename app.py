from pathlib import Path
import py_compile
import re

src = Path("/mnt/data/app_social_connected.py")
text = src.read_text(encoding="utf-8")

# 1) Genel destek durumu fonksiyonunu sosyal risk fonksiyonundan sonra, oturma düzeni bölümünden önce ekle.
marker = """    # =========================================================
    # OTURMA DÜZENİ ÖNERİSİ
    # =========================================================
"""
insert = r'''
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
                "Öğrencinin hem akademik hem sosyal göstergelerinde yüksek destek ihtiyacı görülmektedir."
            )

        elif akademik_yuksek:
            return (
                "Akademik Destek",
                "📚",
                "Öncelik akademik risk göstergelerinin öğretmen tarafından değerlendirilmesidir."
            )

        elif sosyal_yuksek:
            return (
                "Sosyal Destek",
                "🤝",
                "Öncelik sosyal etkileşim göstergelerinin öğretmen tarafından değerlendirilmesidir."
            )

        elif akademik_izleme or sosyal_izleme:
            return (
                "İzleme",
                "👀",
                "Belirgin bir yüksek risk olmasa da öğrencinin gelişiminin düzenli izlenmesi önerilir."
            )

        else:
            return (
                "Rutin Takip",
                "✅",
                "Mevcut göstergelerde yüksek destek ihtiyacı görülmemektedir."
            )


'''
if insert.strip() not in text:
    text = text.replace(marker, insert + marker)

# 2) Sosyal risk hesaplandıktan sonra genel destek durumunu hesapla.
target = """        sosyal_puan, sosyal_durum, sosyal_nedenler, sosyal_oneriler, sosyal_bilesenler = sosyal_risk_hesapla(
            grup_katilimi,
            akran_destegi,
            arkadas_baglantisi,
            ogretmen_iletisimi,
            sosyal_izolasyon,
            oturma_konumu
        )

        egri_metni, oneri_mesaji, oneri_ikon = (
"""
replacement = """        sosyal_puan, sosyal_durum, sosyal_nedenler, sosyal_oneriler, sosyal_bilesenler = sosyal_risk_hesapla(
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
"""
text = text.replace(target, replacement)

# 3) Eski tek akademik metric + durum bloğunu iki kolonlu genel profil bölümüyle değiştir.
start = text.index('        st.subheader(\n            f"📋 {ogrenci_adi} İçin Risk Analiz Raporu"\n        )')
end = text.index('        st.subheader(\n            "🤖 Yapay Zekâ Ön Tahmini"\n        )', start)

new_profile = r'''        st.subheader(
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

'''
text = text[:start] + new_profile + text[end:]

# 4) Akademik gerekçeden sonra sosyal analiz paneli ekle.
target2 = '''        st.info(
            f"🔍 **Tespit Edilen Risk Gerekçeleri:** "
            f"{gerekce}"
        )

        st.subheader(
            "🎯 Stratejik Yerleşim Önerisi"
        )
'''
replacement2 = r'''        st.info(
            f"🔍 **Tespit Edilen Akademik Risk Gerekçeleri:** "
            f"{gerekce}"
        )

        # -----------------------------------------------------
        # SOSYAL ETKİLEŞİM ANALİZİ
        # -----------------------------------------------------

        st.markdown("---")
        st.subheader("🤝 Sosyal Etkileşim Analizi")

        sosyal_sol, sosyal_sag = st.columns([1, 1])

        with sosyal_sol:
            st.markdown("**🔎 Sosyal Risk Nedenleri**")
            for neden in sosyal_nedenler:
                st.write(f"• {neden}")

        with sosyal_sag:
            st.markdown("**🧩 Sosyal Müdahale Önerileri**")
            for oneri in sosyal_oneriler:
                st.write(f"• {oneri}")

        st.markdown("**📊 Sosyal Risk Bileşenleri**")

        sosyal_grafik_df = pd.DataFrame(
            {
                "Risk Bileşeni": list(sosyal_bilesenler.keys()),
                "Risk Puanı": list(sosyal_bilesenler.values())
            }
        )

        st.bar_chart(
            sosyal_grafik_df.set_index("Risk Bileşeni"),
            y="Risk Puanı"
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
'''
text = text.replace(target2, replacement2)

out = Path("/mnt/data/app_sosyal_gorunur.py")
out.write_text(text, encoding="utf-8")

# Syntax check
py_compile.compile(str(out), doraise=True)

# Lightweight formula sanity checks mirroring Excel social rows:
def sosyal_calc(g,a,b,o,i,k):
    gr = 90 if g <= 2 else 60 if g == 3 else 30 if g == 4 else 10
    ar = 90 if a <= 2 else 60 if a == 3 else 30 if a == 4 else 10
    br = 90 if b == 0 else 60 if b <= 2 else 30 if b <= 4 else 10
    ir = 90 if o <= 2 else 60 if o == 3 else 30 if o == 4 else 10
    iz = 90 if i >= 5 else 70 if i == 4 else 50 if i == 3 else 20
    ot = {"Ön":10,"Orta":30,"Kenar":50,"Arka":60}[k]
    return round(gr*.20+ar*.20+br*.25+ir*.15+iz*.15+ot*.05,2)

checks = {
    "ST02": sosyal_calc(3,2,1,3,1,"Orta"),
    "ST08": sosyal_calc(3,0,0,3,5,"Ön"),
    "ST09": sosyal_calc(1,1,1,2,3,"Arka"),
    "ST10": sosyal_calc(0,1,2,1,2,"Arka"),
}
print("Dosya hazır ve syntax kontrolünden geçti:", out)
print("Excel uyum kontrolü:", checks)

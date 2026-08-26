import pandas as pd
import json
import re
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



def ogrenci_analiz_gecmisini_getir(ogrenci_id):
    """Seçilen öğrencinin kayıtlı analiz geçmişini kronolojik sırada getirir."""
    client, hata = supabase_client_al()
    if hata:
        return [], hata

    try:
        sonuc = (
            client.table("analiz_gecmisi")
            .select(
                "id, analiz_tarihi, akademik_risk, akademik_durum, "
                "sosyal_risk, sosyal_durum, genel_destek"
            )
            .eq("ogrenci_id", ogrenci_id)
            .order("analiz_tarihi")
            .execute()
        )
        return sonuc.data or [], None
    except Exception:
        return [], (
            "Analiz geçmişi alınamadı. Supabase bağlantısını ve `analiz_gecmisi` "
            "tablosunu kontrol edin."
        )


# --------------------------------------------------------------------------
# SMARTCLASS AI ÖĞRETMEN ASİSTANI
# SÜRÜM: TIMELINE-2026-08-26
# --------------------------------------------------------------------------
# API anahtarı kaynak kodda tutulmaz. Streamlit Secrets içinde
# GEMINI_API_KEY adıyla saklanır.

if "smartclass_ai_messages" not in st.session_state:
    st.session_state["smartclass_ai_messages"] = []

if "son_analiz" not in st.session_state:
    st.session_state["son_analiz"] = None

if "yeni_analiz_yapildi" not in st.session_state:
    st.session_state["yeni_analiz_yapildi"] = False

if "analiz_kaydedildi" not in st.session_state:
    st.session_state["analiz_kaydedildi"] = False


# --------------------------------------------------------------------------
# SUPABASE AUTH + POSTGRESQL KALICI KAYIT KATMANI
# SÜRÜM: AUTH-RLS-2026-08-26
# --------------------------------------------------------------------------
# Normal öğretmen işlemleri yalnızca SUPABASE_PUBLISHABLE_KEY ile yapılır.
# SUPABASE_SECRET_KEY uygulamanın normal akışında kullanılmaz.
# Öğretmen oturumu Supabase Auth üzerinden açılır; veritabanı erişimi RLS'ye tabidir.

AUTH_SESSION_KEYS = (
    "sb_access_token",
    "sb_refresh_token",
    "sb_user_id",
    "sb_user_email",
)


def _auth_session_temizle():
    for key in AUTH_SESSION_KEYS:
        st.session_state.pop(key, None)


def _auth_session_kaydet(session=None, user=None):
    if session is not None:
        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)
        if access_token:
            st.session_state["sb_access_token"] = access_token
        if refresh_token:
            st.session_state["sb_refresh_token"] = refresh_token

        session_user = getattr(session, "user", None)
        if user is None and session_user is not None:
            user = session_user

    if user is not None:
        user_id = getattr(user, "id", None)
        user_email = getattr(user, "email", None)
        if user_id:
            st.session_state["sb_user_id"] = str(user_id)
        if user_email:
            st.session_state["sb_user_email"] = str(user_email)


def _supabase_baglantibilgileri_al():
    try:
        url = st.secrets["SUPABASE_URL"]
        publishable_key = st.secrets["SUPABASE_PUBLISHABLE_KEY"]
        return url, publishable_key, None
    except Exception:
        return None, None, (
            "Supabase bağlantı bilgileri bulunamadı. Streamlit Secrets içinde "
            "`SUPABASE_URL` ve `SUPABASE_PUBLISHABLE_KEY` tanımlı olmalıdır."
        )


def _supabase_yeni_client():
    url, publishable_key, hata = _supabase_baglantibilgileri_al()
    if hata:
        return None, hata

    try:
        from supabase import create_client
        return create_client(url, publishable_key), None
    except ImportError:
        return None, (
            "Supabase Python paketi bulunamadı. `requirements.txt` dosyasında "
            "`supabase` satırı bulunmalıdır."
        )
    except Exception:
        return None, (
            "Supabase istemcisi oluşturulamadı. Project URL ve Publishable Key "
            "ayarlarını kontrol edin."
        )


def supabase_client_al(giris_zorunlu=True):
    """Geçerli öğretmen oturumuyla RLS'ye tabi Supabase istemcisi döndürür."""
    client, hata = _supabase_yeni_client()
    if hata:
        return None, hata

    access_token = st.session_state.get("sb_access_token")
    refresh_token = st.session_state.get("sb_refresh_token")

    if not access_token or not refresh_token:
        if giris_zorunlu:
            return None, "Öğretmen oturumu bulunamadı. Lütfen tekrar giriş yapın."
        return client, None

    try:
        session_response = client.auth.set_session(access_token, refresh_token)
        yenilenen_session = getattr(session_response, "session", None)
        if yenilenen_session is not None:
            _auth_session_kaydet(session=yenilenen_session)

        user_response = client.auth.get_user()
        user = getattr(user_response, "user", None)
        if user is None:
            raise RuntimeError("Kullanıcı doğrulanamadı.")

        _auth_session_kaydet(user=user)
        return client, None

    except Exception:
        _auth_session_temizle()
        return None, "Oturumun süresi dolmuş veya geçersiz. Lütfen tekrar giriş yapın."


def supabase_giris_yap(email, password):
    email = str(email or "").strip()
    password = str(password or "")

    if not email or not password:
        return False, "E-posta ve şifre alanları zorunludur."

    client, hata = _supabase_yeni_client()
    if hata:
        return False, hata

    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        session = getattr(response, "session", None)
        user = getattr(response, "user", None)

        if session is None or user is None:
            return False, "Giriş oturumu oluşturulamadı. E-posta doğrulamasını kontrol edin."

        _auth_session_kaydet(session=session, user=user)
        return True, "Giriş başarılı."
    except Exception:
        return False, "E-posta veya şifre hatalı ya da hesap henüz doğrulanmamış."


def supabase_oturum_acik_mi():
    if not st.session_state.get("sb_access_token") or not st.session_state.get("sb_refresh_token"):
        return False

    client, hata = supabase_client_al(giris_zorunlu=True)
    return client is not None and hata is None


def supabase_cikis_yap():
    try:
        client, _ = supabase_client_al(giris_zorunlu=False)
        if client is not None and st.session_state.get("sb_access_token"):
            try:
                client.auth.set_session(
                    st.session_state.get("sb_access_token"),
                    st.session_state.get("sb_refresh_token"),
                )
                client.auth.sign_out()
            except Exception:
                pass
    finally:
        _auth_session_temizle()


def supabase_baglanti_testi():
    client, hata = supabase_client_al()
    if hata:
        return False, hata

    try:
        client.table("ogrenciler").select("id").limit(1).execute()
        return True, "Supabase/PostgreSQL bağlantısı ve öğretmen oturumu hazır."
    except Exception:
        return False, (
            "Veritabanına yetkili erişim sağlanamadı. Auth oturumunu, RLS politikalarını "
            "ve Data API izinlerini kontrol edin."
        )


def _temiz_metin(deger):
    return " ".join(str(deger or "").strip().split())


def kayitli_ogrencileri_getir():
    """Yalnızca giriş yapan öğretmenin RLS ile izin verilen öğrencilerini getirir."""
    client, hata = supabase_client_al()
    if hata:
        return [], hata

    try:
        sonuc = (
            client.table("ogrenciler")
            .select("id, ogrenci_kodu, ad_soyad, sinif")
            .order("sinif")
            .order("ad_soyad")
            .execute()
        )
        return sonuc.data or [], None
    except Exception:
        return [], (
            "Kayıtlı öğrenci listesi alınamadı. Öğretmen oturumunu ve RLS politikalarını kontrol edin."
        )


def siradaki_ogrenci_kodu_uret(client):
    """Her öğretmen için ST0001, ST0002 ... biçiminde sıradaki kodu üretir."""
    sonuc = client.table("ogrenciler").select("ogrenci_kodu").execute()
    en_buyuk = 0

    for kayit in sonuc.data or []:
        kod = _temiz_metin(kayit.get("ogrenci_kodu")).upper()
        eslesme = re.fullmatch(r"ST0*(\d+)", kod)
        if eslesme:
            en_buyuk = max(en_buyuk, int(eslesme.group(1)))

    return f"ST{en_buyuk + 1:04d}"


def ogrenciyi_bul_veya_olustur(client, ogrenci_kodu, ad_soyad, sinif):
    """RLS kapsamında mevcut öğrenciyi doğrular veya yeni öğrenci oluşturur."""
    kod = _temiz_metin(ogrenci_kodu).upper()
    ad = _temiz_metin(ad_soyad)
    sinif_degeri = _temiz_metin(sinif).upper()

    if not ad or not sinif_degeri:
        raise ValueError("Ad soyad ve sınıf alanları zorunludur.")

    if kod:
        sonuc = (
            client.table("ogrenciler")
            .select("id, ogrenci_kodu, ad_soyad, sinif")
            .eq("ogrenci_kodu", kod)
            .limit(1)
            .execute()
        )

        if not sonuc.data:
            raise ValueError(
                f"`{kod}` kodlu öğrenci bu öğretmen hesabında bulunamadı. "
                "Kayıtlı öğrenci listesinden seçim yapın veya Yeni Öğrenci modunu kullanın."
            )

        kayit = sonuc.data[0]
        kayitli_ad = _temiz_metin(kayit.get("ad_soyad"))
        kayitli_sinif = _temiz_metin(kayit.get("sinif")).upper()

        if kayitli_ad.casefold() != ad.casefold() or kayitli_sinif != sinif_degeri:
            raise ValueError(
                f"`{kod}` öğrenci kodunun kimlik bilgileri kayıtla eşleşmiyor. "
                "Yanlış öğrenciye analiz bağlanmaması için öğrenciyi listeden tekrar seçin."
            )

        return kayit["id"], False, kayit["ogrenci_kodu"]

    son_hata = None
    for _ in range(3):
        yeni_kod = siradaki_ogrenci_kodu_uret(client)
        try:
            eklenen = (
                client.table("ogrenciler")
                .insert(
                    {
                        "ogrenci_kodu": yeni_kod,
                        "ad_soyad": ad,
                        "sinif": sinif_degeri,
                        # ogretmen_id veritabanında auth.uid() default'u ile atanır.
                    }
                )
                .execute()
            )
            if eklenen.data:
                return eklenen.data[0]["id"], True, yeni_kod
        except Exception as e:
            son_hata = e

    raise RuntimeError(f"Öğrenci kaydı oluşturulamadı: {son_hata}")


def analizi_supabase_kaydet(analiz):
    """Son öğrenci analizini giriş yapan öğretmenin yetkisiyle kaydeder."""
    client, hata = supabase_client_al()
    if hata:
        return False, hata, None

    try:
        ogrenci_id, yeni_ogrenci, gercek_kod = ogrenciyi_bul_veya_olustur(
            client,
            analiz.get("ogrenci_kodu"),
            analiz.get("ogrenci_adi"),
            analiz.get("sinif"),
        )

        kayit = {
            "ogrenci_id": ogrenci_id,
            "ilk_not": int(analiz["ilk_not"]),
            "ikinci_not": int(analiz["ikinci_not"]),
            "birinci_oturma_duzeni": analiz.get("duzen1"),
            "ikinci_oturma_duzeni": analiz.get("duzen2"),
            "devamsizlik": int(analiz["devamsizlik"]),
            "odev_yuzdesi": int(analiz["odev_yuzdesi"]),
            "katilim_yuzdesi": int(analiz["katilim_yuzdesi"]),
            "grup_katilimi": int(analiz["grup_katilimi"]),
            "akran_destegi": int(analiz["akran_destegi"]),
            "arkadas_baglantisi": int(analiz["arkadas_baglantisi"]),
            "ogretmen_iletisimi": int(analiz["ogretmen_iletisimi"]),
            "sosyal_izolasyon": int(analiz["sosyal_izolasyon"]),
            "oturma_konumu": analiz["oturma_konumu"],
            "akademik_risk": float(analiz["puan"]),
            "akademik_durum": analiz["durum"],
            "akademik_gerekce": analiz.get("gerekce"),
            "sosyal_risk": float(analiz["sosyal_puan"]),
            "sosyal_durum": analiz["sosyal_durum"],
            "sosyal_nedenler": analiz.get("sosyal_nedenler", []),
            "sosyal_oneriler": analiz.get("sosyal_oneriler", []),
            "sosyal_bilesenler": analiz.get("sosyal_bilesenler", {}),
            "genel_destek": analiz["genel_destek"],
        }

        sonuc = client.table("analiz_gecmisi").insert(kayit).execute()

        if not sonuc.data:
            return False, "Analiz kaydı veritabanına eklenemedi.", None

        if yeni_ogrenci:
            return True, (
                f"✅ Yeni öğrenci **{gercek_kod}** koduyla oluşturuldu ve analiz kalıcı olarak kaydedildi."
            ), gercek_kod

        return True, "✅ Analiz mevcut öğrenci kaydına kalıcı olarak eklendi.", gercek_kod

    except ValueError as e:
        return False, str(e), None
    except Exception:
        return False, (
            "Analiz kaydedilemedi. Öğretmen yetkisini, RLS politikalarını ve tablo sütunlarını kontrol edin."
        ), None


def smartclass_ai_yanit_al(soru, analiz_baglami, sohbet_gecmisi):
    """Gemini'den öğretmene gösterilecek yalnızca nihai Türkçe yanıtı alır."""

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return (
            "AI asistanı için gerekli `google-genai` paketi bulunamadı. "
            "requirements.txt dosyasına `google-genai` satırını ekleyin."
        )

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return (
            "Gemini API anahtarı bulunamadı. Streamlit App Settings → Secrets "
            "bölümünde `GEMINI_API_KEY` tanımlı olmalıdır."
        )

    # Veri minimizasyonu: gerçek öğrenci adı harici AI servisine gönderilmez.
    ogrenci_tanimlayici = str(analiz_baglami.get("ogrenci_adi", "Seçili öğrenci"))
    if not ogrenci_tanimlayici.strip().upper().startswith("ST"):
        modele_giden_ogrenci = "Seçili öğrenci"
        guvenli_soru = soru.replace(ogrenci_tanimlayici, "[ÖĞRENCİ]")
    else:
        modele_giden_ogrenci = ogrenci_tanimlayici
        guvenli_soru = soru

    guvenli_baglam = {
        "ogrenci": modele_giden_ogrenci,
        "akademik_risk_puani": analiz_baglami.get("puan"),
        "akademik_risk_durumu": analiz_baglami.get("durum"),
        "akademik_gerekceler": analiz_baglami.get("gerekce"),
        "sosyal_risk_puani": analiz_baglami.get("sosyal_puan"),
        "sosyal_risk_durumu": analiz_baglami.get("sosyal_durum"),
        "sosyal_risk_nedenleri": analiz_baglami.get("sosyal_nedenler"),
        "sosyal_mudahale_onerileri": analiz_baglami.get("sosyal_oneriler"),
        "sosyal_risk_bilesenleri": analiz_baglami.get("sosyal_bilesenler"),
        "genel_destek_durumu": analiz_baglami.get("genel_destek"),
        "birinci_sinav": analiz_baglami.get("ilk_not"),
        "ikinci_sinav": analiz_baglami.get("ikinci_not"),
        "not_ortalamasi": analiz_baglami.get("not_ort"),
        "devamsizlik_gun": analiz_baglami.get("devamsizlik"),
        "odev_tamamlama_yuzdesi": analiz_baglami.get("odev_yuzdesi"),
        "derse_katilim_yuzdesi": analiz_baglami.get("katilim_yuzdesi"),
        "oturma_duzeni": analiz_baglami.get("duzen2"),
        "sosyal_oturma_konumu": analiz_baglami.get("oturma_konumu"),
    }

    gecmis_parcalari = []
    for mesaj in sohbet_gecmisi[-4:]:
        icerik = str(mesaj.get("content", ""))
        if not ogrenci_tanimlayici.strip().upper().startswith("ST"):
            icerik = icerik.replace(ogrenci_tanimlayici, "[ÖĞRENCİ]")
        rol = "Öğretmen" if mesaj.get("role") == "user" else "Asistan"
        gecmis_parcalari.append(f"{rol}: {icerik}")

    system_instruction = """
Sen SmartClass Twin projesinin Twin AI Asistanısın.
Öğretmenin verdiği öğrenci analizini açıkla ve uygulanabilir destek önerileri sun.

Çıktı kuralları:
- Sadece öğretmene gösterilecek son cevabı yaz.
- Cevabın tamamı Türkçe olsun.
- İç muhakeme, kontrol listesi, güvenlik denetimi, meta açıklama veya İngilizce not yazma.
- Yalnızca verilen verilere dayan; olmayan bilgi üretme.
- Akademik ve sosyal riski ayrı değerlendir.
- Öğrenciyi etiketleme, psikolojik/sağlık tanısı koyma.
- Kanıtlanmamış kesin neden-sonuç, kesin gelecek tahmini veya uydurma yüzde üretme.
- Önerileri kısa, uygulanabilir ve mevcut göstergelerle bağlantılı ver.
- Yanıtı tercihen 60-180 kelime arasında tut. Öğretmen özellikle ayrıntı isterse biraz daha uzat.
- Cevabı yarıda kesme. Uzunluk sınırına yaklaşırsan ayrıntıyı azalt, fakat son cümleyi mutlaka tamamla.
- Uygunsa nihai pedagojik kararın öğretmene ait olduğunu bir cümleyle belirt.
""".strip()

    kullanici_icerigi = (
        "ÖĞRENCİ ANALİZİ:\n"
        + json.dumps(guvenli_baglam, ensure_ascii=False, default=str, indent=2)
        + "\n\nÖNCEKİ SOHBET:\n"
        + ("\n".join(gecmis_parcalari) if gecmis_parcalari else "Yok")
        + "\n\nÖĞRETMENİN SORUSU:\n"
        + guvenli_soru
        + "\n\nDoğrudan Türkçe son cevabı ver."
    )

    client = genai.Client(api_key=api_key)
    son_hata = None

    # Jüri/demonstrasyon kullanımında gecikmeyi azaltmak için düşük gecikmeli
    # Flash-Lite modeli önceliklidir. Daha ağır modele yalnızca erişim hatasında düşülür.
    model_listesi = ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite"]

    for model_adi in model_listesi:
        try:
            if model_adi == "gemini-3.5-flash-lite":
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=900,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="minimal",
                        include_thoughts=False,
                    ),
                )
            else:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    max_output_tokens=900,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0,
                        include_thoughts=False,
                    ),
                )

            response = client.models.generate_content(
                model=model_adi,
                contents=kullanici_icerigi,
                config=config,
            )

            # Yalnızca thought=False olan görünür cevap parçalarını topla.
            gorunen_parcalar = []
            if getattr(response, "candidates", None):
                for candidate in response.candidates:
                    content = getattr(candidate, "content", None)
                    if not content:
                        continue
                    for part in getattr(content, "parts", []) or []:
                        if getattr(part, "thought", False):
                            continue
                        part_text = getattr(part, "text", None)
                        if part_text:
                            gorunen_parcalar.append(part_text.strip())

            ham_yanit = "\n".join(gorunen_parcalar).strip()
            if not ham_yanit and response and getattr(response, "text", None):
                ham_yanit = response.text.strip()

            if not ham_yanit:
                continue

            # Önceki ekranda görülen meta kontrol satırlarını son bir güvenlik katmanında süz.
            yasak_meta = (
                "no diagnoses",
                "cautious language",
                "final answer",
                "safety check",
                "policy check",
                "internal reasoning",
                "reasoning:",
                "analysis:",
                "checklist",
            )
            temiz_satirlar = []
            for satir in ham_yanit.splitlines():
                kucuk = satir.strip().lower()
                if any(ifade in kucuk for ifade in yasak_meta):
                    continue
                temiz_satirlar.append(satir)

            temiz_yanit = "\n".join(temiz_satirlar).strip()
            if temiz_yanit:
                return temiz_yanit

        except Exception as e:
            son_hata = e

    return (
        "Şu anda AI servisine ulaşılamadı. Bağlantı veya model erişimi kontrol edilmeli. "
        f"Teknik ayrıntı: {son_hata}"
    )


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




if not supabase_oturum_acik_mi():

    st.markdown(
        "<h3 style='text-align: center;'>🔐 Öğretmen Girişi</h3>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        e_posta = st.text_input(
            "E-posta",
            placeholder="ogretmen@okul.edu.tr"
        )
        sifre = st.text_input("Şifre", type="password")

        if st.button(
            "Sisteme Giriş Yap",
            use_container_width=True,
            type="primary"
        ):
            basarili, mesaj = supabase_giris_yap(e_posta, sifre)
            if basarili:
                st.success("✅ Güvenli öğretmen oturumu açıldı.")
                st.rerun()
            else:
                st.error(f"🚨 {mesaj}")

        st.caption(
            "Giriş doğrulaması Supabase Auth üzerinden yapılır. "
            "Veritabanı erişimi öğretmen hesabına bağlı RLS politikalarıyla sınırlandırılır."
        )


else:

    st.write(
        "Öğrencinin verilerini girerek yapay zeka ve ağırlıklı "
        "risk puanı analizini anında görebilirsiniz."
    )




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



    st.sidebar.header("⚙️ Veri Giriş Paneli")

    aktif_ogretmen_email = st.session_state.get("sb_user_email", "")
    if aktif_ogretmen_email:
        st.sidebar.caption(f"🔐 Oturum: {aktif_ogretmen_email}")

    st.sidebar.subheader("👤 Öğrenci Bilgileri")

    kayitli_ogrenciler, ogrenci_liste_hatasi = kayitli_ogrencileri_getir()
    if ogrenci_liste_hatasi:
        st.sidebar.warning(ogrenci_liste_hatasi)

    ogrenci_modu = st.sidebar.radio(
        "Öğrenci İşlemi",
        ["Kayıtlı Öğrenci Seç", "Yeni Öğrenci Ekle"],
        key="ogrenci_modu",
    )

    if ogrenci_modu == "Kayıtlı Öğrenci Seç" and kayitli_ogrenciler:
        secenekler = {}
        for kayit in kayitli_ogrenciler:
            etiket = (
                f"{kayit.get('ad_soyad', '')} — {kayit.get('sinif', '')} "
                f"({kayit.get('ogrenci_kodu', '')})"
            )
            secenekler[etiket] = kayit

        secilen_etiket = st.sidebar.selectbox(
            "Kayıtlı Öğrenci",
            list(secenekler.keys()),
        )
        secilen_ogrenci = secenekler[secilen_etiket]
        ogrenci_kodu = _temiz_metin(secilen_ogrenci.get("ogrenci_kodu")).upper()
        ogrenci_adi = _temiz_metin(secilen_ogrenci.get("ad_soyad"))
        sinif = _temiz_metin(secilen_ogrenci.get("sinif")).upper()

        st.sidebar.caption(f"🔑 Sistem kodu: **{ogrenci_kodu}**")

    elif ogrenci_modu == "Kayıtlı Öğrenci Seç":
        st.sidebar.info(
            "Henüz kayıtlı öğrenci bulunmuyor. Yeni öğrenci eklemek için aşağıdaki modu seçin."
        )
        ogrenci_kodu = ""
        ogrenci_adi = ""
        sinif = "9/A"

    else:
        ogrenci_kodu = ""
        ogrenci_adi = st.sidebar.text_input(
            "Ad Soyad",
            value="",
            placeholder="Örn: Ayşe Yılmaz",
        ).strip()
        sinif = st.sidebar.text_input(
            "Sınıf",
            value="9/A",
            placeholder="Örn: 9/A, 10/D, 11/E",
            help="Sınıf ve şubeyi okulunuzdaki kullanıma göre serbestçe yazabilirsiniz.",
        ).strip().upper()
        st.sidebar.caption(
            "🔑 Öğrenci kodu ilk analiz kaydedilirken sistem tarafından otomatik oluşturulur "
            "(ST0001, ST0002, ...)."
        )

    with st.sidebar.expander("🗄️ Veritabanı Durumu"):
        st.caption(
            "Öğrenci ve analiz kayıtları Supabase/PostgreSQL üzerinde kalıcı tutulur."
        )
        if st.button(
            "🔌 Bağlantıyı Test Et",
            key="supabase_baglanti_test",
            use_container_width=True
        ):
            basarili, mesaj = supabase_baglanti_testi()
            if basarili:
                st.success(mesaj)
            else:
                st.error(mesaj)

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

        supabase_cikis_yap()
        st.session_state["smartclass_ai_messages"] = []
        st.session_state["son_analiz"] = None
        st.session_state["yeni_analiz_yapildi"] = False
        st.session_state["analiz_kaydedildi"] = False
        st.rerun()


    def analiz_raporunu_goster(a):
        ogrenci_adi = a["ogrenci_adi"]
        ogrenci_kodu = a.get("ogrenci_kodu", "")
        sinif = a.get("sinif", "")
        ilk_not = a["ilk_not"]
        ikinci_not = a["ikinci_not"]
        duzen2 = a["duzen2"]
        oturma_konumu = a["oturma_konumu"]
        odev_yuzdesi = a["odev_yuzdesi"]
        katilim_yuzdesi = a["katilim_yuzdesi"]
        devamsizlik = a["devamsizlik"]
        puan = a["puan"]
        durum = a["durum"]
        gerekce = a["gerekce"]
        sosyal_puan = a["sosyal_puan"]
        sosyal_durum = a["sosyal_durum"]
        sosyal_nedenler = a["sosyal_nedenler"]
        sosyal_oneriler = a["sosyal_oneriler"]
        sosyal_bilesenler = a["sosyal_bilesenler"]
        genel_destek = a["genel_destek"]
        genel_destek_ikon = a["genel_destek_ikon"]
        genel_destek_aciklama = a["genel_destek_aciklama"]
        egri_metni = a["egri_metni"]
        oneri_mesaji = a["oneri_mesaji"]
        oneri_ikon = a["oneri_ikon"]
        not_ort = a["not_ort"]
        ai_tahmin = a["ai_tahmin"]
        risk_olasiligi = a["risk_olasiligi"]

        kimlik_parcalari = [x for x in [ogrenci_kodu, sinif] if x]
        kimlik_eki = (
            " (" + " · ".join(kimlik_parcalari) + ")"
            if kimlik_parcalari
            else ""
        )

        st.subheader(
            f"📋 {ogrenci_adi}{kimlik_eki} İçin Risk Analiz Raporu"
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

        if (
            durum == "Risk Yok"
            and sosyal_durum == "Düşük Sosyal Risk"
            and st.session_state.get("yeni_analiz_yapildi", False)
        ):
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




    ogrenci_bilgisi_hazir = bool(_temiz_metin(ogrenci_adi) and _temiz_metin(sinif))
    if not ogrenci_bilgisi_hazir:
        st.info("👤 Analiz için önce bir kayıtlı öğrenci seçin veya yeni öğrencinin adını girin.")

    if st.button(
        "📊 Öğrenci Risk Analizini Yap",
        type="primary",
        use_container_width=True,
        disabled=not ogrenci_bilgisi_hazir,
    ):

        puan, durum, gerekce = risk_hesapla(
            ilk_not,
            ikinci_not,
            devamsizlik,
            odev_yuzdesi,
            katilim_yuzdesi
        )


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

        st.session_state["son_analiz"] = {
            "ogrenci_kodu": ogrenci_kodu,
            "ogrenci_adi": ogrenci_adi,
            "sinif": sinif,
            "ilk_not": ilk_not,
            "ikinci_not": ikinci_not,
            "duzen1": duzen1,
            "duzen2": duzen2,
            "odev_yuzdesi": odev_yuzdesi,
            "katilim_yuzdesi": katilim_yuzdesi,
            "devamsizlik": devamsizlik,
            "grup_katilimi": grup_katilimi,
            "akran_destegi": akran_destegi,
            "arkadas_baglantisi": arkadas_baglantisi,
            "ogretmen_iletisimi": ogretmen_iletisimi,
            "sosyal_izolasyon": sosyal_izolasyon,
            "oturma_konumu": oturma_konumu,
            "puan": puan,
            "durum": durum,
            "gerekce": gerekce,
            "sosyal_puan": sosyal_puan,
            "sosyal_durum": sosyal_durum,
            "sosyal_nedenler": sosyal_nedenler,
            "sosyal_oneriler": sosyal_oneriler,
            "sosyal_bilesenler": sosyal_bilesenler,
            "genel_destek": genel_destek,
            "genel_destek_ikon": genel_destek_ikon,
            "genel_destek_aciklama": genel_destek_aciklama,
            "egri_metni": egri_metni,
            "oneri_mesaji": oneri_mesaji,
            "oneri_ikon": oneri_ikon,
            "not_ort": not_ort,
            "performans_dususu": performans_dususu,
            "ai_tahmin": int(ai_tahmin),
            "risk_olasiligi": float(risk_olasiligi),
        }

        # Yeni öğrenci/analiz bağlamında eski sohbet karışmasın.
        st.session_state["smartclass_ai_messages"] = []
        st.session_state["yeni_analiz_yapildi"] = True
        st.session_state["analiz_kaydedildi"] = False

    if st.session_state.get("son_analiz"):
        analiz_raporunu_goster(st.session_state["son_analiz"])
        st.session_state["yeni_analiz_yapildi"] = False

        st.markdown("---")
        st.subheader("💾 Analizi Kalıcı Olarak Kaydet")

        kayit_analizi = st.session_state["son_analiz"]
        st.caption(
            "Kayıt sırasında öğrenci kimliği `ogrenciler` tablosunda, analiz verileri "
            "ise öğrenci ID'si üzerinden `analiz_gecmisi` tablosunda tutulur."
        )
        kod_gosterimi = kayit_analizi.get("ogrenci_kodu") or "Kod otomatik oluşturulacak"
        st.info(
            f"👤 **{kayit_analizi['ogrenci_adi']}** · "
            f"{kod_gosterimi} · {kayit_analizi['sinif']}  |  "
            f"📚 Akademik: **{kayit_analizi['puan']}/100**  |  "
            f"🤝 Sosyal: **{kayit_analizi['sosyal_puan']}/100**"
        )

        if st.session_state.get("analiz_kaydedildi", False):
            st.success("✅ Bu analiz veritabanına kaydedildi.")
        else:
            if st.button(
                "💾 Bu Analizi Kaydet",
                type="primary",
                use_container_width=True,
                key="analizi_supabase_kaydet"
            ):
                with st.spinner("Analiz Supabase/PostgreSQL'e kaydediliyor..."):
                    basarili, mesaj, kaydedilen_kod = analizi_supabase_kaydet(kayit_analizi)

                if basarili:
                    st.session_state["analiz_kaydedildi"] = True
                    if kaydedilen_kod:
                        st.session_state["son_analiz"]["ogrenci_kodu"] = kaydedilen_kod
                    st.success(mesaj)
                else:
                    st.error(mesaj)


    # ----------------------------------------------------------------------
    # RİSK ZAMAN ÇİZELGESİ
    # ----------------------------------------------------------------------
    st.markdown("---")
    st.header("📈 Risk Zaman Çizelgesi")
    st.write(
        "Kayıtlı analizleri karşılaştırarak akademik ve sosyal riskin zaman içindeki "
        "değişimini izleyebilirsiniz. Puan değişimleri bir neden-sonuç kanıtı değil, "
        "takip göstergesidir."
    )

    if kayitli_ogrenciler:
        timeline_secenekler = {}
        for kayit in kayitli_ogrenciler:
            etiket = (
                f"{kayit.get('ad_soyad', '')} — {kayit.get('sinif', '')} "
                f"({kayit.get('ogrenci_kodu', '')})"
            )
            timeline_secenekler[etiket] = kayit

        timeline_etiketleri = list(timeline_secenekler.keys())
        varsayilan_timeline_index = 0
        aktif_kod = _temiz_metin(
            st.session_state.get("son_analiz", {}).get("ogrenci_kodu", "")
            if st.session_state.get("son_analiz")
            else ""
        ).upper()

        if aktif_kod:
            for i, etiket in enumerate(timeline_etiketleri):
                if _temiz_metin(
                    timeline_secenekler[etiket].get("ogrenci_kodu")
                ).upper() == aktif_kod:
                    varsayilan_timeline_index = i
                    break

        timeline_secim = st.selectbox(
            "Geçmişi görüntülenecek öğrenci",
            timeline_etiketleri,
            index=varsayilan_timeline_index,
            key="timeline_ogrenci_secimi",
        )
        timeline_ogrenci = timeline_secenekler[timeline_secim]

        gecmis_kayitlari, gecmis_hatasi = ogrenci_analiz_gecmisini_getir(
            timeline_ogrenci["id"]
        )

        if gecmis_hatasi:
            st.error(gecmis_hatasi)
        elif not gecmis_kayitlari:
            st.info(
                "Bu öğrenci için henüz kalıcı analiz kaydı yok. Bir analiz oluşturup "
                "**Bu Analizi Kaydet** butonuyla kaydettikten sonra zaman çizelgesi oluşacaktır."
            )
        else:
            gecmis_df = pd.DataFrame(gecmis_kayitlari)
            gecmis_df["analiz_tarihi"] = pd.to_datetime(
                gecmis_df["analiz_tarihi"],
                utc=True,
                errors="coerce",
            )
            gecmis_df = (
                gecmis_df.dropna(subset=["analiz_tarihi"])
                .sort_values("analiz_tarihi")
                .reset_index(drop=True)
            )

            if gecmis_df.empty:
                st.warning("Kayıtların tarih bilgisi okunamadı.")
            else:
                try:
                    gecmis_df["yerel_tarih"] = gecmis_df["analiz_tarihi"].dt.tz_convert(
                        "Europe/Istanbul"
                    )
                except Exception:
                    gecmis_df["yerel_tarih"] = gecmis_df["analiz_tarihi"]

                gecmis_df["akademik_risk"] = pd.to_numeric(
                    gecmis_df["akademik_risk"], errors="coerce"
                )
                gecmis_df["sosyal_risk"] = pd.to_numeric(
                    gecmis_df["sosyal_risk"], errors="coerce"
                )

                son = gecmis_df.iloc[-1]
                onceki = gecmis_df.iloc[-2] if len(gecmis_df) >= 2 else None

                delta_akademik = None
                delta_sosyal = None
                if onceki is not None:
                    delta_akademik = float(son["akademik_risk"]) - float(
                        onceki["akademik_risk"]
                    )
                    delta_sosyal = float(son["sosyal_risk"]) - float(
                        onceki["sosyal_risk"]
                    )

                m_tarih, m_akademik, m_sosyal, m_kayit = st.columns(4)
                m_tarih.metric(
                    "Son Analiz",
                    son["yerel_tarih"].strftime("%d.%m.%Y"),
                )
                m_akademik.metric(
                    "📚 Akademik Risk",
                    f"{float(son['akademik_risk']):.1f}/100",
                    delta=(
                        f"{delta_akademik:+.1f} puan"
                        if delta_akademik is not None
                        else None
                    ),
                    delta_color="inverse",
                )
                m_sosyal.metric(
                    "🤝 Sosyal Risk",
                    f"{float(son['sosyal_risk']):.1f}/100",
                    delta=(
                        f"{delta_sosyal:+.1f} puan"
                        if delta_sosyal is not None
                        else None
                    ),
                    delta_color="inverse",
                )
                m_kayit.metric("Kayıt Sayısı", len(gecmis_df))

                st.caption(
                    f"Son genel destek durumu: **{son.get('genel_destek', '-')}** · "
                    "Risk puanında azalma olumlu yönde, artış ise daha yakından izleme "
                    "gereksinimi olarak yorumlanabilir."
                )

                fig_timeline = go.Figure()
                fig_timeline.add_trace(
                    go.Scatter(
                        x=gecmis_df["yerel_tarih"],
                        y=gecmis_df["akademik_risk"],
                        mode="lines+markers",
                        name="Akademik Risk",
                        hovertemplate="%{x|%d.%m.%Y %H:%M}<br>Akademik Risk: %{y:.1f}<extra></extra>",
                    )
                )
                fig_timeline.add_trace(
                    go.Scatter(
                        x=gecmis_df["yerel_tarih"],
                        y=gecmis_df["sosyal_risk"],
                        mode="lines+markers",
                        name="Sosyal Risk",
                        hovertemplate="%{x|%d.%m.%Y %H:%M}<br>Sosyal Risk: %{y:.1f}<extra></extra>",
                    )
                )
                fig_timeline.update_layout(
                    yaxis=dict(title="Risk Puanı", range=[0, 100]),
                    xaxis=dict(title="Analiz Tarihi"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                    margin=dict(l=20, r=20, t=55, b=20),
                    height=420,
                    hovermode="x unified",
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

                if onceki is not None:
                    st.markdown("#### 🔄 Son İki Analiz Karşılaştırması")

                    def risk_degisimi_metni(ad, onceki_deger, son_deger):
                        fark = float(son_deger) - float(onceki_deger)
                        if abs(fark) < 0.05:
                            return f"**{ad}:** {onceki_deger:.1f} → {son_deger:.1f} · değişim yok"
                        if fark < 0:
                            return (
                                f"**{ad}:** {onceki_deger:.1f} → {son_deger:.1f} · "
                                f"**{abs(fark):.1f} puan azaldı**"
                            )
                        return (
                            f"**{ad}:** {onceki_deger:.1f} → {son_deger:.1f} · "
                            f"**{fark:.1f} puan arttı**"
                        )

                    st.write(
                        risk_degisimi_metni(
                            "Akademik risk",
                            float(onceki["akademik_risk"]),
                            float(son["akademik_risk"]),
                        )
                    )
                    st.write(
                        risk_degisimi_metni(
                            "Sosyal risk",
                            float(onceki["sosyal_risk"]),
                            float(son["sosyal_risk"]),
                        )
                    )
                else:
                    st.info(
                        "Karşılaştırma için en az iki kalıcı analiz kaydı gerekir. "
                        "Aynı öğrenci için ileride yeni bir analiz kaydettiğinizde değişim otomatik hesaplanacaktır."
                    )

                with st.expander("🗂️ Kayıtlı analizleri tablo olarak görüntüle"):
                    tablo_df = gecmis_df[
                        [
                            "yerel_tarih",
                            "akademik_risk",
                            "akademik_durum",
                            "sosyal_risk",
                            "sosyal_durum",
                            "genel_destek",
                        ]
                    ].copy()
                    tablo_df["yerel_tarih"] = tablo_df["yerel_tarih"].dt.strftime(
                        "%d.%m.%Y %H:%M"
                    )
                    tablo_df.columns = [
                        "Analiz Tarihi",
                        "Akademik Risk",
                        "Akademik Durum",
                        "Sosyal Risk",
                        "Sosyal Durum",
                        "Genel Destek",
                    ]
                    st.dataframe(
                        tablo_df.sort_index(ascending=False),
                        use_container_width=True,
                        hide_index=True,
                    )
    else:
        st.info(
            "Risk zaman çizelgesi için önce en az bir öğrenci ve analiz kaydı oluşturun."
        )


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

    # ----------------------------------------------------------------------
    # SAĞ ALTTA AÇILIR SMARTCLASS AI ÖĞRETMEN ASİSTANI
    # ----------------------------------------------------------------------
    st.markdown(
        """
        <style>
        /* Twin AI Asistan popover düğmesini sağ alta sabitle */
        div[data-testid="stPopover"] {
            position: fixed !important;
            right: 24px !important;
            bottom: 24px !important;
            z-index: 999999 !important;
        }

        div[data-testid="stPopover"] button {
            border-radius: 999px !important;
            padding: 0.70rem 1rem !important;
            font-weight: 700 !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22) !important;
        }

        @media (max-width: 700px) {
            div[data-testid="stPopover"] {
                right: 12px !important;
                bottom: 12px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    def ai_panel_icerigi():
        st.markdown("### 🤖 Twin AI Asistan")
        st.caption(
            "Mevcut akademik ve sosyal analizleri açıklamak ve öğretmene "
            "destek seçenekleri sunmak için kullanılır. Nihai karar öğretmene aittir."
        )

        analiz = st.session_state.get("son_analiz")

        if analiz:
            st.info(
                f"📌 **Bağlı analiz:** {analiz['ogrenci_adi']} ({analiz.get('ogrenci_kodu', '')})  ·  "
                f"Akademik: {analiz['puan']}/100  ·  "
                f"Sosyal: {analiz['sosyal_puan']}/100"
            )
        else:
            st.warning(
                "Öğrenciye özel öneri için önce **Öğrenci Risk Analizini Yap** butonuyla "
                "bir analiz oluşturun."
            )

        st.caption(
            "🔐 Gizlilik: AI servisine gerçek öğrenci adı otomatik olarak gönderilmez. "
            "Asistana TC, telefon, adres gibi kişisel veriler yazmayın."
        )

        # Sohbet geçmişini göster
        for mesaj in st.session_state["smartclass_ai_messages"][-8:]:
            with st.chat_message(mesaj["role"]):
                st.markdown(mesaj["content"])

        soru = None

        if analiz:
            q1 = st.button(
                "🎯 Öncelikli destek alanını açıkla",
                key="ai_hizli_oncelik",
                use_container_width=True,
            )
            q2 = st.button(
                "🔎 Riskin temel nedenlerini özetle",
                key="ai_hizli_neden",
                use_container_width=True,
            )
            q3 = st.button(
                "🧩 İlk müdahale adımlarını öner",
                key="ai_hizli_mudahale",
                use_container_width=True,
            )

            if q1:
                soru = "Bu öğrenci için öncelikli destek alanı nedir? Verilere dayanarak kısa gerekçe ver."
            elif q2:
                soru = "Bu öğrencinin akademik ve sosyal risklerinin temel nedenlerini ayrı ayrı özetle."
            elif q3:
                soru = "Bu öğrenci için uygulanabilecek ilk 3 destek adımını öncelik sırasıyla öner ve her birini verideki göstergeyle ilişkilendir."

        with st.form("smartclass_ai_form", clear_on_submit=True):
            yazili_soru = st.text_input(
                "Mesajınız",
                placeholder="Örn: Bu öğrenci için ilk olarak ne yapmalıyım?",
                disabled=not bool(analiz),
            )
            gonder = st.form_submit_button(
                "Gönder",
                use_container_width=True,
                disabled=not bool(analiz),
            )

        if gonder and yazili_soru.strip():
            soru = yazili_soru.strip()

        if soru and analiz:
            st.session_state["smartclass_ai_messages"].append(
                {"role": "user", "content": soru}
            )

            with st.spinner("Twin AI Asistan analiz ediyor..."):
                yanit = smartclass_ai_yanit_al(
                    soru,
                    analiz,
                    st.session_state["smartclass_ai_messages"][:-1],
                )

            st.session_state["smartclass_ai_messages"].append(
                {"role": "assistant", "content": yanit}
            )

            with st.chat_message("user"):
                st.markdown(soru)
            with st.chat_message("assistant"):
                st.markdown(yanit)

        if st.session_state["smartclass_ai_messages"]:
            if st.button(
                "🗑️ Sohbeti Temizle",
                key="ai_sohbet_temizle",
                use_container_width=True,
            ):
                st.session_state["smartclass_ai_messages"] = []
                st.rerun()

    if hasattr(st, "popover"):
        with st.popover("🤖 Twin AI Asistan"):
            ai_panel_icerigi()
    else:
        # Eski Streamlit sürümleri için güvenli geri dönüş.
        with st.expander("🤖 Twin AI Asistan"):
            ai_panel_icerigi()

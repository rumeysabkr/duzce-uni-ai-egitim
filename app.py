"""
Masraf Onay Agent'ı: Gradio arayüzü.

Çalıştırmak için:  python app.py
Hugging Face Spaces bu dosyayı otomatik olarak çalıştırır.

Bu dosyada yapay zekâ ile ilgili bir mantık yok; sadece arayüz var.
Asıl iş agents/ klasöründe.
"""

import threading
import time

import gradio as gr

import config
from agents import koordinator
from iz_kaydi import IzKaydi
from rag.politika_arama import POLITIKA_DOSYASI
from tools.onay_araclari import kayit_tablosu, yonetici_karari

TABLO_BASLIKLARI = ["Kayıt No", "Saat", "Kalem", "Tutar (TL)", "Durum", "Gerekçe"]

ORNEK_TALEPLER = [
    "Ankara'daki müşteri toplantısı için 2 gece otelde kaldım, toplam 5.400 TL. "
    "Otelden toplantıya taksi 650 TL. Akşam müşteriyle 3 kişi yemek yedik, hesap 85 USD tuttu. Tüm fişlerim var.",

    "İstanbul'da 1 gece otel 4.600 TL ödedim, faturası var. "
    "Havalimanından otele transfer 1.100 TL.",

    "Berlin'deki fuar için 3 gece otel 690 EUR. Fuardan sonra 4 kişilik ekip yemeği 3.600 TL. "
    "Odadaki minibardan 40 EUR harcama oldu. Faturalar elimde.",

    "Müşteri firmayla İzmir'de akşam yemeği yedik, 2 kişiydik. Toplam hesap 2.800 TL, bunun 600 TL'si şarap.",
]


def masraf_degerlendir(talep: str):
    """
    "Değerlendir" butonuna basılınca çalışır.

    Agent'lar birkaç tur döndüğü için iş biraz sürer. Kullanıcı beklerken adımları
    canlı görebilsin diye agent'ları arka planda çalıştırıp her saniye iz kaydını
    ekrana yansıtıyoruz (yield ile).
    """
    if not talep or not talep.strip():
        yield "Lütfen bir masraf talebi yazın.", "", kayit_tablosu()
        return

    if not config.api_anahtari_var_mi():
        yield (
            "OPENAI_API_KEY tanımlı değil. Lokal çalışıyorsan .env dosyasına, "
            "Hugging Face'teysen Space ayarlarındaki Secrets bölümüne ekle.",
            "",
            kayit_tablosu(),
        )
        return

    iz = IzKaydi()
    sonuc = {}

    def arka_planda_calistir():
        try:
            ekip = koordinator.olustur(iz)
            sonuc["rapor"] = ekip.calistir(talep, iz)
        except Exception as hata:
            sonuc["rapor"] = f"Bir hata oluştu: {hata}"

    is_parcacigi = threading.Thread(target=arka_planda_calistir)
    is_parcacigi.start()

    while is_parcacigi.is_alive():
        yield "Agent'lar çalışıyor, adımları sağ tarafta izleyebilirsin...", iz.markdown(), kayit_tablosu()
        time.sleep(1)

    yield sonuc.get("rapor", ""), iz.markdown(), kayit_tablosu()


def yonetici_onayla(kayit_no: str):
    return yonetici_karari(kayit_no, onay=True), kayit_tablosu()


def yonetici_reddet(kayit_no: str):
    return yonetici_karari(kayit_no, onay=False), kayit_tablosu()


NASIL_CALISIR = """
### Ekip

| Agent | Görevi | Kullandığı |
|---|---|---|
| **Koordinatör** | Talebi kalemlere ayırır, uzmanlara iş dağıtır, raporu yazar | Diğer agent'lar |
| **Politika Uzmanı** | Her kalemin kuralını ve limitini bulur | RAG: `politika_ara` |
| **Hesap Uzmanı** | Döviz çevirir, toplam ve kişi başı tutarı hesaplar, limitle karşılaştırır | Tool: `doviz_cevir`, `hesapla`, `limit_karsilastir` |
| **Onay Uzmanı** | Onay kurallarına göre her kalemi onaylar, yöneticiye gönderir veya reddeder | RAG + Tool: `masraf_onayla`, `yoneticiye_gonder`, `masraf_reddet` |

### Akış

1. Çalışan masraf talebini yazar.
2. **Koordinatör** talebi kalemlere ayırır.
3. **Politika Uzmanı** her kalemin limitini politikadan bulur.
4. **Hesap Uzmanı** tutarları TL'ye çevirip limitle karşılaştırır.
5. **Onay Uzmanı** kararı uygular. Sınırı aşan kalemler **Yönetici Onayı** sekmesine düşer.
6. Kararı bir **insan** verir (human-in-the-loop).

Her agent aynı döngüyle çalışır: **düşün -> araç çağır -> sonuca bak -> tekrar**.
Kodun tamamı `agents/` klasöründe; her agent ayrı bir dosyada.
"""


with gr.Blocks(title="Masraf Onay Agent'ı") as demo:
    gr.Markdown(
        "# Masraf Onay Agent'ı\n"
        "Çok agent'lı, RAG kullanan ve araç çağıran bir eğitim projesi. "
        "Tüm veriler, limitler ve kurlar **hayalidir**."
    )

    with gr.Tab("Masraf Talebi"):
        with gr.Row():
            with gr.Column(scale=1):
                talep_kutusu = gr.Textbox(
                    label="Masraf talebin",
                    placeholder="Örn: Ankara'da 2 gece otel 5.400 TL, taksi 650 TL...",
                    lines=6,
                )
                degerlendir_butonu = gr.Button("Değerlendir", variant="primary")
                gr.Examples(examples=ORNEK_TALEPLER, inputs=talep_kutusu, label="Örnek talepler")
            with gr.Column(scale=1):
                gr.Markdown("### Adım adım: agent'lar ne yaptı?")
                adimlar_kutusu = gr.Markdown("Henüz bir adım yok.")

        gr.Markdown("### Sonuç")
        rapor_kutusu = gr.Markdown()

    with gr.Tab("Yönetici Onayı"):
        gr.Markdown(
            "Limiti aşan masraflar burada bir insanın kararını bekler. "
            "Kayıt numarasını yazıp onaylayabilir ya da reddedebilirsin."
        )
        kayit_tablosu_kutusu = gr.Dataframe(
            value=kayit_tablosu(),
            headers=TABLO_BASLIKLARI,
            interactive=False,
            wrap=True,
        )
        with gr.Row():
            kayit_no_kutusu = gr.Textbox(label="Kayıt No", placeholder="M-1001")
            onayla_butonu = gr.Button("Onayla", variant="primary")
            reddet_butonu = gr.Button("Reddet", variant="stop")
            yenile_butonu = gr.Button("Tabloyu yenile")
        yonetici_mesaji = gr.Markdown()

    with gr.Tab("Masraf Politikası (RAG kaynağı)"):
        gr.Markdown(
            "Politika Uzmanı ve Onay Uzmanı kuralları bu dokümanda arar. "
            "Dosya: `data/masraf_politikasi.md`"
        )
        gr.Markdown(POLITIKA_DOSYASI.read_text(encoding="utf-8"))

    with gr.Tab("Nasıl çalışır?"):
        gr.Markdown(NASIL_CALISIR)

    # Butonları fonksiyonlara bağlıyoruz
    degerlendir_butonu.click(
        masraf_degerlendir,
        inputs=talep_kutusu,
        outputs=[rapor_kutusu, adimlar_kutusu, kayit_tablosu_kutusu],
    )
    onayla_butonu.click(yonetici_onayla, inputs=kayit_no_kutusu, outputs=[yonetici_mesaji, kayit_tablosu_kutusu])
    reddet_butonu.click(yonetici_reddet, inputs=kayit_no_kutusu, outputs=[yonetici_mesaji, kayit_tablosu_kutusu])
    yenile_butonu.click(kayit_tablosu, outputs=kayit_tablosu_kutusu)


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())

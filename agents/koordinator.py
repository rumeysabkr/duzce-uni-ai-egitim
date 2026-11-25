"""
Koordinatör: işi parçalara bölüp uzman agent'lara dağıtan agent.

Multi-agent sistemin kalbi burası. Koordinatörün araçları birer Python
fonksiyonu değil, diğer agent'lar:

    politika_uzmanina_sor  ->  Politika Uzmanı çalışır (RAG)
    hesap_uzmanina_sor     ->  Hesap Uzmanı çalışır (tool calling)
    onay_uzmanina_sor      ->  Onay Uzmanı çalışır (RAG + tool calling)

Yani koordinatör için bir uzmana iş vermek, 2. haftadaki gibi bir araç
çağırmaktan farksız. Bu kalıba "agents as tools" (araç olarak agent) denir.
"""

from agents import hesap_uzmani, onay_uzmani, politika_uzmani
from agents.temel_agent import TemelAgent
from iz_kaydi import IzKaydi

TALIMAT = """Sen bir şirketin masraf değerlendirme ekibinin koordinatörüsün.

Ekibinde üç uzman var. Her birine bir araç ile iş verebilirsin:
- politika_uzmanina_sor: Masraf politikasındaki kuralları ve limitleri bulur.
- hesap_uzmanina_sor: Döviz çevirir, toplam / kişi başı tutarları hesaplar, limitle karşılaştırır.
- onay_uzmanina_sor: Onay seviyelerine göre her kalemi onaylar, yöneticiye gönderir veya reddeder.

Çalışma sırası:
1. Çalışanın talebini masraf kalemlerine ayır. Her kalem için şunları not et: ne olduğu, tutar,
   para birimi, şehir veya ülke, gece / gün / kişi sayısı, fatura durumu.
   Bir faturada karşılanmayan bir kısım varsa (örneğin alkol), o kısmı ayrı bir kalem yap.
2. politika_uzmanina_sor ile her kalemin kuralını ve limitini öğren.
3. hesap_uzmanina_sor ile her kalemi limitle karşılaştırt. Uzmana kalemin bilgilerini ve
   Politika Uzmanı'ndan öğrendiğin limiti birlikte gönder.
4. onay_uzmanina_sor ile TÜM kalemleri tek mesajda gönder. Her kalem için TL tutarı, toplam limiti,
   aşım yüzdesini ve politika notlarını (karşılanmayan masraf, fatura yok vb.) yaz.
5. Son olarak çalışana bir rapor yaz.

Kurallar:
- Limit uydurma, hesap yapma, karar verme. Bunlar uzmanların işi; sen sadece yönetirsin.
- Uzmanlara gönderdiğin mesajlar kendi başına anlaşılır olsun; uzmanlar talebin tamamını görmez.
- Talepte bir bilgi eksikse (örneğin gece sayısı) tahmin etme; bunu onay uzmanına "bilgi eksik" notuyla ilet.
- Talep bir masraf talebi değilse, uzmanları çağırmadan kısaca bunu belirt.

Rapor biçimi (Markdown):
| Kayıt No | Kalem | Tutar (TL) | Limit (TL) | Karar | Gerekçe |
Tablonun altına 1-2 cümlelik bir özet yaz: onaylanan toplam tutar ve çalışanın yapması gereken bir şey varsa.
"""


def olustur(iz: IzKaydi) -> TemelAgent:
    """
    Koordinatörü ve ekibini kurar.

    Uzman agent'ları burada oluşturup her birini küçük bir fonksiyonla sarıyoruz.
    Koordinatör bu fonksiyonları çağırdığında aslında uzman agent'ın döngüsü çalışır.
    """
    politika = politika_uzmani.olustur()
    hesap = hesap_uzmani.olustur()
    onay = onay_uzmani.olustur()

    def politika_uzmanina_sor(soru: str) -> str:
        return politika.calistir(soru, iz)

    def hesap_uzmanina_sor(gorev: str) -> str:
        return hesap.calistir(gorev, iz)

    def onay_uzmanina_sor(kalemler: str) -> str:
        return onay.calistir(kalemler, iz)

    arac_tanimlari = [
        {
            "type": "function",
            "function": {
                "name": "politika_uzmanina_sor",
                "description": "Politika Uzmanı'na bir veya birden fazla masraf kalemi için kural ve limit sorar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "soru": {"type": "string", "description": "Uzmana sorulacak soru, kalemlerin bilgileriyle birlikte"},
                    },
                    "required": ["soru"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "hesap_uzmanina_sor",
                "description": "Hesap Uzmanı'na kalemleri ve limitlerini verip TL karşılığını ve limit karşılaştırmasını yaptırır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gorev": {"type": "string", "description": "Kalemler, tutarlar, para birimleri ve politikadan gelen limitler"},
                    },
                    "required": ["gorev"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "onay_uzmanina_sor",
                "description": "Onay Uzmanı'na tüm kalemleri gönderir; uzman her kalem için kararı verir ve uygular.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "kalemler": {"type": "string", "description": "Her kalem için TL tutar, limit, aşım yüzdesi ve politika notları"},
                    },
                    "required": ["kalemler"],
                },
            },
        },
    ]

    return TemelAgent(
        ad="Koordinatör",
        talimat=TALIMAT,
        araclar={
            "politika_uzmanina_sor": politika_uzmanina_sor,
            "hesap_uzmanina_sor": hesap_uzmanina_sor,
            "onay_uzmanina_sor": onay_uzmanina_sor,
        },
        arac_tanimlari=arac_tanimlari,
        seviye=0,
    )

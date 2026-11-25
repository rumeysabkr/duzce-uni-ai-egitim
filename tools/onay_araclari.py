"""
Onay Uzmanı'nın araçları: onaylamak, yöneticiye göndermek, reddetmek.

Bu araçlar dünyada bir şey "değiştiren" araçlar (2. haftadaki "eylem" araçları).
Gerçek bir sistemde bir veritabanına yazarlardı. Burada basit tutmak için
kayıtları bellekteki bir listede saklıyoruz.

Önemli: Uygulama yeniden başladığında bu liste sıfırlanır ve aynı uygulamayı
kullanan herkes aynı listeyi görür. Eğitim demosu için bu yeterli.
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Sunucu (örneğin Hugging Face) farklı bir saat diliminde olabilir; saati Türkiye saatiyle yazıyoruz
SAAT_DILIMI = ZoneInfo("Europe/Istanbul")

# Tüm masraf kararları burada tutulur
KAYITLAR = []

DURUM_ONAYLANDI = "Onaylandı"
DURUM_YONETICIDE = "Yönetici onayı bekliyor"
DURUM_REDDEDILDI = "Reddedildi"


def _kayit_ekle(kalem: str, tutar_tl: float, durum: str, gerekce: str) -> str:
    kayit_no = f"M-{1001 + len(KAYITLAR)}"
    KAYITLAR.append({
        "kayit_no": kayit_no,
        "kalem": kalem,
        "tutar_tl": round(float(tutar_tl), 2),
        "durum": durum,
        "gerekce": gerekce,
        "zaman": datetime.now(SAAT_DILIMI).strftime("%H:%M:%S"),
    })
    return json.dumps({"kayit_no": kayit_no, "durum": durum}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Agent'ın çağırdığı araçlar
# ---------------------------------------------------------------------------

def masraf_onayla(kalem: str, tutar_tl: float, gerekce: str) -> str:
    """Limit içindeki bir masrafı onaylar."""
    return _kayit_ekle(kalem, tutar_tl, DURUM_ONAYLANDI, gerekce)


def yoneticiye_gonder(kalem: str, tutar_tl: float, gerekce: str) -> str:
    """
    Kararı bir insana bırakır (human-in-the-loop).
    Agent burada karar vermez; masraf yönetici onay ekranına düşer.
    """
    return _kayit_ekle(kalem, tutar_tl, DURUM_YONETICIDE, gerekce)


def masraf_reddet(kalem: str, tutar_tl: float, gerekce: str) -> str:
    """Politikaya uymayan bir masrafı reddeder."""
    return _kayit_ekle(kalem, tutar_tl, DURUM_REDDEDILDI, gerekce)


# ---------------------------------------------------------------------------
# Arayüzün kullandığı yardımcı fonksiyonlar (agent bunları görmez)
# ---------------------------------------------------------------------------

def kayit_tablosu() -> list[list]:
    """Tüm kayıtları arayüzdeki tablo için satırlar halinde döndürür."""
    return [
        [k["kayit_no"], k["zaman"], k["kalem"], k["tutar_tl"], k["durum"], k["gerekce"]]
        for k in KAYITLAR
    ]


def yonetici_karari(kayit_no: str, onay: bool) -> str:
    """Yönetici onay ekranından gelen kararı uygular. Bu adımı agent değil, insan yapar."""
    kayit_no = kayit_no.strip().upper()
    for kayit in KAYITLAR:
        if kayit["kayit_no"] == kayit_no:
            if kayit["durum"] != DURUM_YONETICIDE:
                return f"{kayit_no} zaten sonuçlanmış: {kayit['durum']}"
            kayit["durum"] = "Yönetici onayladı" if onay else "Yönetici reddetti"
            return f"{kayit_no} için karar kaydedildi: {kayit['durum']}"
    return f"{kayit_no} numaralı kayıt bulunamadı."


# ---------------------------------------------------------------------------
# Modele gösterilen araç tanımları
# ---------------------------------------------------------------------------

def _tanim(ad: str, aciklama: str) -> dict:
    """Üç aracın parametreleri aynı olduğu için tanımları bu fonksiyonla üretiyoruz."""
    return {
        "type": "function",
        "function": {
            "name": ad,
            "description": aciklama,
            "parameters": {
                "type": "object",
                "properties": {
                    "kalem": {"type": "string", "description": "Masraf kalemi, örn. 'Ankara otel, 2 gece'"},
                    "tutar_tl": {"type": "number", "description": "Kalemin Türk lirası karşılığı"},
                    "gerekce": {"type": "string", "description": "Kararın kısa gerekçesi; ilgili limiti ve aşım yüzdesini belirt"},
                },
                "required": ["kalem", "tutar_tl", "gerekce"],
            },
        },
    }


MASRAF_ONAYLA_TANIMI = _tanim(
    "masraf_onayla",
    "Limit içinde kalan ve politikaya uygun bir masraf kalemini onaylar.",
)

YONETICIYE_GONDER_TANIMI = _tanim(
    "yoneticiye_gonder",
    "Limiti en fazla yüzde 20 aşan bir masraf kalemini karar için çalışanın yöneticisine gönderir.",
)

MASRAF_REDDET_TANIMI = _tanim(
    "masraf_reddet",
    "Limiti yüzde 20'den fazla aşan, politikada karşılanmayan ya da faturası olmayan bir masraf kalemini reddeder.",
)

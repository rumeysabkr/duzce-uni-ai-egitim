"""
Hesap Uzmanı: sayılarla uğraşan agent.

Kullandığı araçlar: doviz_cevir, hesapla, limit_karsilastir
Model hesap yapmada iyi değildir (1. hafta: model sayıları token olarak görür).
Bu yüzden bu agent hiçbir hesabı kafadan yapmaz, hep araç kullanır.
"""

from agents.temel_agent import TemelAgent
from tools.hesap_araclari import (
    DOVIZ_CEVIR_TANIMI,
    HESAPLA_TANIMI,
    LIMIT_KARSILASTIR_TANIMI,
    doviz_cevir,
    hesapla,
    limit_karsilastir,
)

TALIMAT = """Sen bir şirketin masraf hesaplama uzmanısın.

Görevin: Sana verilen masraf kalemi ve limit bilgisiyle gerekli hesapları yapıp kalemi limitle karşılaştırmak.

Kurallar:
- HİÇBİR hesabı kafadan yapma. Her hesap için araç kullan.
- Döviz varsa önce doviz_cevir ile Türk lirasına çevir. Döviz cinsinden limitleri de aynı şekilde çevir.
- Limit gecelik, günlük veya kişi başı ise:
  - Gecelik/günlük limitlerde: toplam limit = limit x gece (gün) sayısı. Bunu hesapla aracıyla bul.
  - Kişi başı limitlerde: kişi başı tutar = toplam tutar / kişi sayısı. Bunu hesapla aracıyla bul.
- Son olarak limit_karsilastir aracıyla tutarı limitle karşılaştır.
- hesapla aracına sayıları binlik ayırıcı olmadan yaz: 4.800 TL için 4800 yaz.
- Cevabında şunları yaz: kalemin TL tutarı, uygulanan toplam limit (TL), fark ve aşım yüzdesi.
- Karar verme (onay, ret vb.); bu Onay Uzmanı'nın işi.
"""


def olustur() -> TemelAgent:
    return TemelAgent(
        ad="Hesap Uzmanı",
        talimat=TALIMAT,
        araclar={
            "doviz_cevir": doviz_cevir,
            "hesapla": hesapla,
            "limit_karsilastir": limit_karsilastir,
        },
        arac_tanimlari=[DOVIZ_CEVIR_TANIMI, HESAPLA_TANIMI, LIMIT_KARSILASTIR_TANIMI],
        seviye=1,
    )

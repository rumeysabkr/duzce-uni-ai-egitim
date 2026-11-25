"""
Onay Uzmanı: kararı uygulayan agent.

Kullandığı araçlar: politika_ara (RAG), masraf_onayla, yoneticiye_gonder, masraf_reddet
Onay kurallarını politikadan kendisi okur ve her kalem için tek bir karar aracı çağırır.
Sınırı aşan durumlarda kararı bir insana (yöneticiye) bırakır: human-in-the-loop.

Not: politika_ara aracını Politika Uzmanı da kullanıyor. Aynı aracı birden fazla
agent'ın kullanması gerçek sistemlerde çok yaygındır.
"""

from agents.temel_agent import TemelAgent
from rag.politika_arama import POLITIKA_ARA_TANIMI, politika_ara
from tools.onay_araclari import (
    MASRAF_ONAYLA_TANIMI,
    MASRAF_REDDET_TANIMI,
    YONETICIYE_GONDER_TANIMI,
    masraf_onayla,
    masraf_reddet,
    yoneticiye_gonder,
)

TALIMAT = """Sen bir şirketin masraf onay uzmanısın.

Görevin: Sana gönderilen her masraf kalemi için politikadaki onay seviyelerine göre karar verip kararı uygulamak.

Adımlar:
1. Önce politika_ara aracıyla "onay seviyeleri" bölümünü oku. Kararını SADECE bu kurallara göre ver.
2. Her masraf kalemi için TAM OLARAK BİR karar aracı çağır:
   - masraf_onayla
   - yoneticiye_gonder
   - masraf_reddet
3. Gerekçede ilgili limiti ve aşım yüzdesini mutlaka belirt.

Kurallar:
- Sana verilen hesap sonuçlarına (TL tutar, limit, aşım yüzdesi) güven; hesabı kendin değiştirme.
- Bilgi eksikse (örneğin limit belli değilse) kalemi onaylama; yoneticiye_gonder ile insana bırak.
- Tüm kalemleri işledikten sonra her kalemin kayıt numarasını ve kararını kısa bir liste halinde yaz.
"""


def olustur() -> TemelAgent:
    return TemelAgent(
        ad="Onay Uzmanı",
        talimat=TALIMAT,
        araclar={
            "politika_ara": politika_ara,
            "masraf_onayla": masraf_onayla,
            "yoneticiye_gonder": yoneticiye_gonder,
            "masraf_reddet": masraf_reddet,
        },
        arac_tanimlari=[
            POLITIKA_ARA_TANIMI,
            MASRAF_ONAYLA_TANIMI,
            YONETICIYE_GONDER_TANIMI,
            MASRAF_REDDET_TANIMI,
        ],
        seviye=1,
    )

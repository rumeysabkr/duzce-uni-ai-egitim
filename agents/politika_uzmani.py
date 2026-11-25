"""
Politika Uzmanı: masraf politikasını bilen agent.

Kullandığı araç: politika_ara (RAG)
Modelin şirketin masraf kurallarını bilmesi mümkün değil. Bu agent kuralları
ezberden değil, her seferinde dokümanda arayarak bulur.
"""

from agents.temel_agent import TemelAgent
from rag.politika_arama import POLITIKA_ARA_TANIMI, politika_ara

TALIMAT = """Sen bir şirketin masraf politikası uzmanısın.

Görevin: Sana sorulan masraf kalemi için politikadaki ilgili kuralı ve limiti bulmak.

Kurallar:
- Cevabını SADECE politika_ara aracının getirdiği metne dayandır. Asla tahmin yürütme, limit uydurma.
- Gerekirse farklı kelimelerle birden fazla arama yap.
- Cevabında şunları açıkça yaz:
  1. İlgili politika bölümünün başlığı
  2. Limit (tutar, para birimi ve neye göre uygulandığı: gecelik, kişi başı, günlük, tek seferlik)
  3. Varsa karşılanmayan kısımlar veya özel şartlar (alkol, minibar, fatura zorunluluğu vb.)
- Politikada bilgi bulamazsan "Politikada bu konuda bir kural bulunamadı." de.
- Kısa ve net yaz. Hesap yapma; hesaplar Hesap Uzmanı'nın işi.
"""


def olustur() -> TemelAgent:
    return TemelAgent(
        ad="Politika Uzmanı",
        talimat=TALIMAT,
        araclar={"politika_ara": politika_ara},
        arac_tanimlari=[POLITIKA_ARA_TANIMI],
        seviye=1,
    )

"""
İz kaydı: agent'ların attığı her adımı sırayla not eder.

Arayüzdeki "Adım adım" bölümü bu kayıttan oluşur. Böylece hangi agent'ın
hangi aracı, hangi bilgiyle çağırdığını ve ne sonuç aldığını görebiliriz.
"""


class IzKaydi:
    def __init__(self):
        self.satirlar = []

    def ekle(self, seviye: int, agent_adi: str, metin: str):
        """
        seviye: 0 = koordinatör, 1 = uzman agent.
        Uzmanların satırları biraz içeriden başlar, böylece kimin kimi
        çağırdığı görsel olarak anlaşılır.
        """
        girinti = "    " * seviye
        self.satirlar.append(f"{girinti}- **{agent_adi}**: {metin}")

    def markdown(self) -> str:
        if not self.satirlar:
            return "Henüz bir adım yok."
        return "\n".join(self.satirlar)


def kisalt(metin: str, uzunluk: int = 300) -> str:
    """Uzun metinleri iz kaydında okunabilir tutmak için kısaltır."""
    metin = str(metin).replace("\n", " ")
    if len(metin) <= uzunluk:
        return metin
    return metin[:uzunluk] + " ..."

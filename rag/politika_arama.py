"""
RAG: masraf politikasında anlamca en yakın bölümleri bulur.

3. haftada gördüğümüz adımların aynısı:
1. Dokümanı parçalara böl (chunking)
2. Her parçayı bir vektöre çevir (embedding)
3. Soruyu da vektöre çevir
4. Soruya en çok benzeyen parçaları getir (vector search)

Vektör veritabanı yerine numpy kullanıyoruz. Doküman küçük olduğu için
bütün vektörleri bellekte tutmak yeterli ve mantığı görmek daha kolay.
"""

import json
from pathlib import Path

import numpy as np

import config

POLITIKA_DOSYASI = Path(__file__).resolve().parent.parent / "data" / "masraf_politikasi.md"


def parcalara_bol(metin: str) -> list[dict]:
    """
    Markdown dokümanı başlıklara göre parçalara böler.

    Her "##" ve "###" başlığı yeni bir parça başlatır. Alt başlıklarda
    üst başlığı da parçanın adına ekleriz ki parça tek başına okunduğunda
    neyle ilgili olduğu anlaşılsın. Örnek: "3. Konaklama > 3.1 Yurt İçi ..."
    """
    parcalar = []
    ust_baslik = ""
    baslik = None
    satirlar = []

    def parcayi_kaydet():
        icerik = "\n".join(satirlar).strip()
        if baslik and icerik:
            parcalar.append({"baslik": baslik, "icerik": icerik})

    for satir in metin.splitlines():
        if satir.startswith("## "):
            parcayi_kaydet()
            ust_baslik = satir[3:].strip()
            baslik = ust_baslik
            satirlar = []
        elif satir.startswith("### "):
            parcayi_kaydet()
            baslik = f"{ust_baslik} > {satir[4:].strip()}"
            satirlar = []
        elif baslik is not None:
            satirlar.append(satir)

    parcayi_kaydet()
    return parcalar


def vektore_cevir(metinler: list[str]) -> np.ndarray:
    """Metin listesini embedding modeliyle vektörlere çevirir."""
    yanit = config.istemci().embeddings.create(
        model=config.EMBEDDING_MODELI,
        input=metinler,
    )
    vektorler = np.array([veri.embedding for veri in yanit.data])
    return vektorler / np.linalg.norm(vektorler, axis=1, keepdims=True)


class PolitikaArama:
    def __init__(self):
        self.parcalar = []
        self.vektorler = None

    def hazirla(self):
        """Dokümanı okur, parçalara böler ve tüm parçaları vektöre çevirir."""
        metin = POLITIKA_DOSYASI.read_text(encoding="utf-8")
        self.parcalar = parcalara_bol(metin)

        # Başlığı da metne katıyoruz; arama yaparken başlık da önemli bir ipucu.
        metinler = [f"{p['baslik']}\n{p['icerik']}" for p in self.parcalar]
        self.vektorler = vektore_cevir(metinler)

    def ara(self, sorgu: str, adet: int = 3) -> list[dict]:
        """Sorguya anlamca en yakın 'adet' kadar parçayı döndürür."""
        if self.vektorler is None:
            self.hazirla()

        sorgu_vektoru = vektore_cevir([sorgu])[0]

        # Her parçanın soruya benzerliği (kosinüs benzerliği, -1 ile 1 arası)
        benzerlikler = self.vektorler @ sorgu_vektoru

        # En yüksek benzerlikten en düşüğe doğru sırala, ilk 'adet' tanesini al
        en_iyiler = np.argsort(benzerlikler)[::-1][:adet]

        return [
            {
                "baslik": self.parcalar[i]["baslik"],
                "icerik": self.parcalar[i]["icerik"],
                "benzerlik": round(float(benzerlikler[i]), 3),
            }
            for i in en_iyiler
        ]


# Uygulama boyunca tek bir arama nesnesi kullanırız.
# İlk aramada doküman vektöre çevrilir, sonraki aramalar hazır vektörleri kullanır.
_arama = PolitikaArama()


# ---------------------------------------------------------------------------
# Agent'lara verilecek araç
# ---------------------------------------------------------------------------

def politika_ara(sorgu: str) -> str:
    """Agent'ların çağırdığı araç: politikada arama yapar, sonucu JSON metni olarak döndürür."""
    sonuclar = _arama.ara(sorgu, adet=3)
    return json.dumps(sonuclar, ensure_ascii=False)


POLITIKA_ARA_TANIMI = {
    "type": "function",
    "function": {
        "name": "politika_ara",
        "description": (
            "Şirketin masraf politikasında arama yapar ve soruya en yakın 3 bölümü getirir. "
            "Limitler, karşılanmayan masraflar ve onay seviyeleri gibi kuralları bulmak için kullan."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sorgu": {
                    "type": "string",
                    "description": "Aranacak konu, örn. 'Ankara otel gecelik limiti' veya 'onay seviyeleri'",
                },
            },
            "required": ["sorgu"],
        },
    },
}

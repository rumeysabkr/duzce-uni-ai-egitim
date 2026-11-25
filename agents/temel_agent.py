"""
Tüm agent'ların ortak iskeleti.

Bir agent aslında üç şeyden oluşur:
1. Talimat (system prompt): kim olduğu ve nasıl davranacağı
2. Araçlar: kullanabileceği fonksiyonlar
3. Döngü: düşün -> araç çağır -> sonuca bak -> gerekirse tekrar

Bu dosyadaki "calistir" fonksiyonu 2. haftada Colab'da yazdığımız sor()
fonksiyonunun aynısı. Tek fark, artık her agent'ın kendi talimatı ve
kendi araçları var.
"""

import json

import config
from iz_kaydi import IzKaydi, kisalt


class TemelAgent:
    def __init__(self, ad: str, talimat: str, araclar: dict, arac_tanimlari: list, seviye: int = 1):
        """
        ad:             Agent'ın adı (iz kaydında görünür)
        talimat:        Agent'ın system prompt'u
        araclar:        {"arac_adi": python_fonksiyonu} eşlemesi
        arac_tanimlari: Modele gösterilen JSON tanımları
        seviye:         0 = koordinatör, 1 = uzman (iz kaydındaki girinti için)
        """
        self.ad = ad
        self.talimat = talimat
        self.araclar = araclar
        self.arac_tanimlari = arac_tanimlari
        self.seviye = seviye

    def calistir(self, gorev: str, iz: IzKaydi) -> str:
        """Agent'a bir görev verir, iş bitene kadar döngüyü çalıştırır, son cevabı döndürür."""
        iz.ekle(self.seviye, self.ad, f"Görev aldı: {kisalt(gorev, 200)}")

        # Masa (context window): talimat + görev ile başlıyor, her turda büyüyor
        mesajlar = [
            {"role": "system", "content": self.talimat},
            {"role": "user", "content": gorev},
        ]

        for tur in range(1, config.EN_FAZLA_TUR + 1):
            # 1. DÜŞÜN: modeli çağır
            yanit = config.istemci().chat.completions.create(
                model=config.SOHBET_MODELI,
                messages=mesajlar,
                tools=self.arac_tanimlari,
                reasoning_effort=config.DUSUNME_SEVIYESI,
            )
            mesaj = yanit.choices[0].message

            # Modelin cevabını (fişini) masaya ekle; model hatırlamaz, her şeyi biz göndeririz
            asistan_mesaji = {"role": "assistant", "content": mesaj.content}
            if mesaj.tool_calls:
                asistan_mesaji["tool_calls"] = [
                    {
                        "id": cagri.id,
                        "type": "function",
                        "function": {"name": cagri.function.name, "arguments": cagri.function.arguments},
                    }
                    for cagri in mesaj.tool_calls
                ]
            mesajlar.append(asistan_mesaji)

            # Fiş yoksa model işini bitirdi demektir: son cevabı döndür
            if not mesaj.tool_calls:
                iz.ekle(self.seviye, self.ad, f"Bitirdi ({tur}. tur): {kisalt(mesaj.content)}")
                return mesaj.content or ""

            # 2. HAREKETE GEÇ: modelin istediği her aracı biz çalıştırırız
            for cagri in mesaj.tool_calls:
                arac_adi = cagri.function.name
                parametreler = json.loads(cagri.function.arguments or "{}")
                iz.ekle(self.seviye, self.ad, f"`{arac_adi}` çağırdı: {kisalt(parametreler, 200)}")

                sonuc = self._araci_calistir(arac_adi, parametreler)

                # 3. GÖZLEMLE: sonucu masaya ekle, bir sonraki turda model buna bakacak
                mesajlar.append({
                    "role": "tool",
                    "tool_call_id": cagri.id,
                    "content": sonuc,
                })

                # Adı "_sor" ile biten araçlar başka bir agent'ı çağırır (bkz. koordinator.py).
                # O agent'ın cevabı zaten kendi satırlarında göründüğü için tekrar yazmıyoruz.
                if not arac_adi.endswith("_sor"):
                    iz.ekle(self.seviye, self.ad, f"Sonuç: {kisalt(sonuc, 200)}")

        # Güvenlik sınırı: agent hedefe ulaşamadan tur sınırı doldu
        iz.ekle(self.seviye, self.ad, "Tur sınırına ulaşıldı, durduruldu.")
        return "Tur sınırına ulaşıldı; görev tamamlanamadı."

    def _araci_calistir(self, arac_adi: str, parametreler: dict) -> str:
        """
        Modelin istediği aracı bulur ve çalıştırır.
        Model olmayan bir araç uydurursa ya da parametreleri yanlış gönderirse
        programı çökertmek yerine hatayı modele geri bildiririz; model düzeltebilir.
        """
        fonksiyon = self.araclar.get(arac_adi)
        if fonksiyon is None:
            return json.dumps({"hata": f"'{arac_adi}' diye bir araç yok."}, ensure_ascii=False)
        try:
            return str(fonksiyon(**parametreler))
        except Exception as hata:
            return json.dumps({"hata": str(hata)}, ensure_ascii=False)

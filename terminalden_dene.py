"""
Arayüz olmadan, terminalden tek bir masraf talebi dener.

Çalıştırmak için:  python terminalden_dene.py
Agent'ların her adımı ve son rapor ekrana yazılır.
"""

from agents import koordinator
from iz_kaydi import IzKaydi
from tools.onay_araclari import KAYITLAR

TALEP = (
    "Ankara'daki müşteri toplantısı için 2 gece otelde kaldım, toplam 5.400 TL. "
    "Otelden toplantıya taksi 650 TL. Akşam müşteriyle 3 kişi yemek yedik, hesap 85 USD tuttu. "
    "Tüm fişlerim var."
)

if __name__ == "__main__":
    iz = IzKaydi()
    ekip = koordinator.olustur(iz)
    rapor = ekip.calistir(TALEP, iz)

    print("=" * 70)
    print("ADIM ADIM")
    print("=" * 70)
    print(iz.markdown())

    print("\n" + "=" * 70)
    print("RAPOR")
    print("=" * 70)
    print(rapor)

    print("\n" + "=" * 70)
    print("KAYITLAR")
    print("=" * 70)
    for kayit in KAYITLAR:
        print(kayit)

"""
Projenin tüm ayarları tek bir yerde.

Model adını veya düşünme seviyesini değiştirmek istersen sadece bu dosyaya
(ya da .env dosyasına) bakman yeterli.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Lokal çalışırken .env dosyasındaki değişkenleri okur.
# Hugging Face'te ise değişkenler "Secrets" bölümünden gelir, .env gerekmez.
load_dotenv()

# Agent'ların kullandığı sohbet modeli
SOHBET_MODELI = os.getenv("SOHBET_MODELI", "gpt-5.6-luna")

# RAG için metinleri vektöre çeviren model.
# Not: gpt-5.6-luna embedding üretmez, bu yüzden ayrı bir model kullanıyoruz.
EMBEDDING_MODELI = os.getenv("EMBEDDING_MODELI", "text-embedding-3-small")

# Modelin cevap vermeden önce ne kadar "düşüneceği".
# Seçenekler: none, low, medium, high
# Düşük seviye daha hızlı ve ucuzdur; eğitim demosu için "low" yeterli.
DUSUNME_SEVIYESI = os.getenv("DUSUNME_SEVIYESI", "low")

# Bir agent'ın en fazla kaç tur döneceği.
# Agent hedefe ulaşamazsa sonsuza kadar dönmesin diye bir güvenlik sınırı.
EN_FAZLA_TUR = int(os.getenv("EN_FAZLA_TUR", "10"))


def api_anahtari_var_mi() -> bool:
    """OPENAI_API_KEY tanımlı mı?"""
    return bool(os.getenv("OPENAI_API_KEY"))


_istemci = None


def istemci() -> OpenAI:
    """
    OpenAI istemcisini bir kez oluşturup tekrar tekrar kullanırız.
    API anahtarını OPENAI_API_KEY ortam değişkeninden kendisi okur.
    """
    global _istemci
    if _istemci is None:
        _istemci = OpenAI()
    return _istemci

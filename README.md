---
title: Masraf Onay Agent
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Çok agent'lı, RAG ve tool calling kullanan eğitim projesi
---

# Masraf Onay Agent'ı

Bir çalışanın masraf talebini şirket politikasına göre değerlendiren, çok agent'lı bir eğitim projesi.
LLM eğitiminin 4 haftasında öğrenilen her şeyi bir arada kullanır:

| Hafta | Konu | Bu projede nerede? |
|---|---|---|
| 1 | LLM, prompt, structured output | Her agent'ın talimatı (`TALIMAT`) ve raporun tablo biçimi |
| 2 | Tool calling | `tools/` klasörü ve `agents/temel_agent.py` içindeki döngü |
| 3 | RAG | `rag/politika_arama.py`: masraf politikasında anlamsal arama |
| 4 | Agent ve multi-agent | `agents/koordinator.py`: uzman agent'lara iş dağıtan koordinatör |

> Tüm veriler hayalidir: şirket, masraf politikası, limitler ve döviz kurları eğitim amaçlı uydurulmuştur.

## Ekip

```
                    Çalışanın talebi
                           |
                     [ Koordinatör ]
                    /       |       \
      [Politika Uzmanı] [Hesap Uzmanı] [Onay Uzmanı]
             |               |              |
        politika_ara    doviz_cevir     politika_ara
           (RAG)         hesapla        masraf_onayla
                      limit_karsilastir yoneticiye_gonder
                                        masraf_reddet
                                              |
                                   [ Yönetici (insan) ]
```

- **Koordinatör:** Talebi kalemlere ayırır, uzmanlara iş verir, son raporu yazar. Araçları diğer agent'lardır.
- **Politika Uzmanı:** Her kalemin kuralını ve limitini politikadan bulur (RAG).
- **Hesap Uzmanı:** Dövizi çevirir, toplam ve kişi başı tutarı hesaplar, limitle karşılaştırır. Hiçbir hesabı kafadan yapmaz.
- **Onay Uzmanı:** Onay kurallarına göre her kalemi onaylar, yöneticiye gönderir ya da reddeder.
- **Yönetici:** Limiti biraz aşan kalemlerde son kararı bir insan verir (human-in-the-loop).

## Proje yapısı

```
masraf-onay-agent/
├── app.py                      # Gradio arayüzü (Hugging Face bunu çalıştırır)
├── terminalden_dene.py         # Arayüzsüz, terminalden tek bir talep dener
├── config.py                   # Model adı, düşünme seviyesi, tur sınırı
├── iz_kaydi.py                 # Agent adımlarını kaydeder ("Adım adım" bölümü)
├── agents/
│   ├── temel_agent.py          # Tüm agent'ların ortak döngüsü: düşün -> araç çağır -> gözlemle
│   ├── koordinator.py          # Ekibi yöneten agent
│   ├── politika_uzmani.py
│   ├── hesap_uzmani.py
│   └── onay_uzmani.py
├── tools/
│   ├── hesap_araclari.py       # doviz_cevir, hesapla, limit_karsilastir
│   └── onay_araclari.py        # masraf_onayla, yoneticiye_gonder, masraf_reddet
├── rag/
│   └── politika_arama.py       # Parçalara bölme, embedding, vektör arama
└── data/
    ├── masraf_politikasi.md    # RAG kaynağı
    └── doviz_kurlari.json      # Sahte döviz kurları
```

**Okuma sırası önerisi:** `agents/temel_agent.py` -> `tools/hesap_araclari.py` -> `rag/politika_arama.py` -> `agents/hesap_uzmani.py` -> `agents/koordinator.py` -> `app.py`

## Lokal kurulum

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# .env dosyasını açıp OPENAI_API_KEY değerini yaz

python app.py                      # Arayüz: http://127.0.0.1:7860
python terminalden_dene.py         # Ya da arayüzsüz dene
```

## Hugging Face Spaces'e yükleme

1. [huggingface.co/new-space](https://huggingface.co/new-space) adresinden yeni bir Space oluştur. **SDK** olarak **Gradio** seç.
2. Bu klasördeki tüm dosyaları Space'e yükle (web arayüzünden "Files > Add file > Upload files" ya da git ile). `.env` dosyasını **yükleme**.
3. Space'in **Settings > Variables and secrets** bölümünde **New secret** ile şunu ekle:
   - Ad: `OPENAI_API_KEY`
   - Değer: OpenAI API anahtarın
4. Space kendiliğinden yeniden başlar ve birkaç dakika içinde açılır.

Bu README'nin en üstündeki ayar bloğu (`sdk`, `sdk_version`, `app_file`) Hugging Face'e uygulamanın nasıl çalıştırılacağını söyler. `sdk_version`, `requirements.txt` içindeki `gradio` sürümüyle aynı olmalı.

## Ayarlar

`.env` dosyasından ya da Hugging Face Secrets / Variables bölümünden değiştirilebilir:

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `OPENAI_API_KEY` | (zorunlu) | OpenAI API anahtarı |
| `SOHBET_MODELI` | `gpt-5.6-luna` | Agent'ların kullandığı model |
| `EMBEDDING_MODELI` | `text-embedding-3-small` | RAG için embedding modeli |
| `DUSUNME_SEVIYESI` | `low` | `none`, `low`, `medium`, `high` |
| `EN_FAZLA_TUR` | `10` | Bir agent'ın en fazla kaç tur döneceği |

## Bilinmesi gerekenler

- **Kayıtlar bellekte tutulur.** Uygulama yeniden başlayınca silinir ve Space'i kullanan herkes aynı kayıt listesini görür.
- **Maliyet:** Her talep, agent'lar arasında 10-20 model çağrısı yapabilir. Space herkese açıksa API kullanımını OpenAI panelinden takip et ya da Space'i gizli (private) yap.
- **Embedding modeli:** `gpt-5.6-luna` embedding üretmediği için RAG'da ayrı bir model (`text-embedding-3-small`) kullanılır.

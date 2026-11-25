"""
Hesap Uzmanı'nın araçları: döviz çevirme, hesap yapma, limitle karşılaştırma.

2. haftada gördüğümüz gibi her araç iki parçadan oluşur:
1. Gerçekten çalışan Python fonksiyonu
2. Modele aracı tanıtan JSON tanımı (isim, açıklama, parametreler)

Model fonksiyonun kodunu hiç görmez, sadece JSON tanımını görür.
"""

import ast
import json
import operator
from pathlib import Path

KUR_DOSYASI = Path(__file__).resolve().parent.parent / "data" / "doviz_kurlari.json"


# ---------------------------------------------------------------------------
# 1. Döviz çevirme
# ---------------------------------------------------------------------------

def doviz_cevir(tutar: float, para_birimi: str) -> str:
    """Döviz tutarını Türk lirasına çevirir. Kurlar data/doviz_kurlari.json dosyasından gelir."""
    kurlar = json.loads(KUR_DOSYASI.read_text(encoding="utf-8"))
    kod = str(para_birimi).strip().upper()

    if kod in ("TL", "TRY"):
        return json.dumps({"tutar": tutar, "para_birimi": "TL", "kur": 1, "tutar_tl": round(float(tutar), 2)})

    if kod not in kurlar or kod.startswith("_"):
        return json.dumps({"hata": f"{kod} için kur bulunamadı. Desteklenenler: USD, EUR, GBP"}, ensure_ascii=False)

    kur = kurlar[kod]
    return json.dumps({
        "tutar": tutar,
        "para_birimi": kod,
        "kur": kur,
        "tutar_tl": round(float(tutar) * kur, 2),
    })


# ---------------------------------------------------------------------------
# 2. Hesap makinesi
# ---------------------------------------------------------------------------

# Sadece dört işleme izin veriyoruz.
_ISLEMLER = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _guvenli_hesapla(dugum):
    """
    İfadeyi Python'un ast modülüyle adım adım hesaplar.

    Neden eval() kullanmıyoruz? Çünkü eval() modelin gönderdiği her türlü
    Python kodunu çalıştırır. Model yanlışlıkla ya da kötü niyetli bir girdi
    yüzünden tehlikeli bir şey yazarsa bunu çalıştırmak istemeyiz.
    2. haftadaki kural: modelden gelen fişi kontrol etmeden çalıştırma.
    """
    if isinstance(dugum, ast.Expression):
        return _guvenli_hesapla(dugum.body)
    if isinstance(dugum, ast.Constant) and isinstance(dugum.value, (int, float)):
        return dugum.value
    if isinstance(dugum, ast.BinOp) and type(dugum.op) in _ISLEMLER:
        return _ISLEMLER[type(dugum.op)](_guvenli_hesapla(dugum.left), _guvenli_hesapla(dugum.right))
    if isinstance(dugum, ast.UnaryOp) and isinstance(dugum.op, ast.USub):
        return -_guvenli_hesapla(dugum.operand)
    raise ValueError("Sadece sayılar, + - * / ve parantez kullanılabilir.")


def hesapla(ifade: str) -> str:
    """Matematiksel bir ifadeyi kesin olarak hesaplar."""
    try:
        sonuc = _guvenli_hesapla(ast.parse(ifade, mode="eval"))
        return json.dumps({"ifade": ifade, "sonuc": round(sonuc, 2)})
    except Exception as hata:
        return json.dumps({"ifade": ifade, "hata": str(hata)}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 3. Limit karşılaştırma
# ---------------------------------------------------------------------------

def limit_karsilastir(tutar_tl: float, limit_tl: float) -> str:
    """Bir masrafı limitiyle karşılaştırır ve aşım yüzdesini hesaplar."""
    tutar_tl = float(tutar_tl)
    limit_tl = float(limit_tl)

    if limit_tl <= 0:
        return json.dumps({"hata": "Limit sıfırdan büyük olmalı."}, ensure_ascii=False)

    fark = tutar_tl - limit_tl
    asim_yuzdesi = max(fark, 0) / limit_tl * 100

    return json.dumps({
        "tutar_tl": round(tutar_tl, 2),
        "limit_tl": round(limit_tl, 2),
        "fark_tl": round(fark, 2),
        "asim_yuzdesi": round(asim_yuzdesi, 1),
        "durum": "limit içinde" if fark <= 0 else "limit aşıldı",
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Modele gösterilen araç tanımları
# ---------------------------------------------------------------------------

DOVIZ_CEVIR_TANIMI = {
    "type": "function",
    "function": {
        "name": "doviz_cevir",
        "description": "Döviz cinsinden bir tutarı şirketin masraf sistemindeki kurla Türk lirasına çevirir.",
        "parameters": {
            "type": "object",
            "properties": {
                "tutar": {"type": "number", "description": "Çevrilecek tutar, örn. 85 veya 690.5"},
                "para_birimi": {"type": "string", "description": "Para birimi kodu: USD, EUR veya GBP"},
            },
            "required": ["tutar", "para_birimi"],
        },
    },
}

HESAPLA_TANIMI = {
    "type": "function",
    "function": {
        "name": "hesapla",
        "description": (
            "Matematiksel bir ifadeyi kesin olarak hesaplar. Toplama, çıkarma, çarpma, bölme ve parantez desteklenir. "
            "Sayıları binlik ayırıcı OLMADAN, ondalık için nokta kullanarak yaz: 4800, 3561.5"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ifade": {"type": "string", "description": "Hesaplanacak ifade, örn. (2800 - 600) / 2"},
            },
            "required": ["ifade"],
        },
    },
}

LIMIT_KARSILASTIR_TANIMI = {
    "type": "function",
    "function": {
        "name": "limit_karsilastir",
        "description": "Bir masraf tutarını limitle karşılaştırır; farkı ve aşım yüzdesini hesaplar. İki değer de TL olmalı.",
        "parameters": {
            "type": "object",
            "properties": {
                "tutar_tl": {"type": "number", "description": "Karşılaştırılacak masraf tutarı (TL)"},
                "limit_tl": {"type": "number", "description": "Bu masrafa uygulanan toplam limit (TL)"},
            },
            "required": ["tutar_tl", "limit_tl"],
        },
    },
}

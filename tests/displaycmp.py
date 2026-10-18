"""Ekranda görünen metinle karşılaştırma (SPEC §3).

G*Power değerleri ekranda farklı basamak sayılarıyla gösterir: çoğunlukla
7 ondalık, bazen 4 ondalık, tamsayı ya da bilimsel gösterim. Karşılaştırma,
beklenen metindeki basamak sayısına yuvarlanarak yapılır.
"""

from decimal import Decimal


def display_digits(text: str) -> tuple[str, int]:
    """Metnin gösterim türünü ve basamak sayısını döndürür.

    ("fixed", k): k ondalık basamak; ("sci", k): mantiste k ondalık basamak.
    """
    t = text.strip()
    if "e" in t.lower():
        mantissa = t.lower().split("e")[0]
        return "sci", len(mantissa.split(".")[1]) if "." in mantissa else 0
    return "fixed", len(t.split(".")[1]) if "." in t else 0


def format_like(value: float, text: str) -> str:
    """value'yu text ile aynı basamak sayısında biçimlendirir."""
    kind, k = display_digits(text)
    if kind == "sci":
        return f"{float(value):.{k}e}"
    return f"{float(value):.{k}f}"


def matches_display(value: float, text: str) -> bool:
    """value, text'in gösterildiği basamağa yuvarlanınca text'e eşit mi?"""
    return Decimal(format_like(value, text)) == Decimal(text.strip())

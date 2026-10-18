"""Ortak katman: girdi sözlüğü → motor → JSON'a uygun sözlük.

CLI ve MCP sunucusu motoru yalnızca buradan çağırır. Doğrulama ve hesap
motordadır (engine.py); burada yalnızca mod adı, zorunlu parametre kontrolü,
çıktı alanlarının sırası ve biçimi ile hata nesnesi bulunur.
"""

from __future__ import annotations

import json
import math
from typing import Any, Callable, Mapping

from . import engine

MODES = {"a-priori": "a-priori", "post-hoc": "post-hoc", "posthoc": "post-hoc"}
REQUIRED = {
    "a-priori": ("w", "alpha", "power", "df"),
    "post-hoc": ("w", "alpha", "n", "df"),
}
FIELDS = ("n_total", "actual_power", "critical", "df", "ncp")


class ServiceError(ValueError):
    """Girdi hatası (G*Power'da karşılığı olmayan: eksik parametre, bilinmeyen mod, …)."""


def _finite(label: str, value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        raise ServiceError(f"Invalid numeric value for {label}: {value!r} (must be finite)")
    return value


def compute(
    mode: str | None,
    params: Mapping[str, Any],
    *,
    label: Callable[[str], str] = lambda name: name,
    convert: Callable[[str, Any], Any] | None = None,
) -> dict:
    """Hesabı çalıştırır; başarıda sonuç sözlüğü, girdi hatasında {"error": mesaj} döndürür.

    params: w, alpha, power, n, df (eksik olan None ya da yok). Moda ait olmayan
    parametreler yok sayılır. label: hata mesajlarında parametre adı (CLI: "--w").
    convert: ham değeri sayıya çeviren isteğe bağlı fonksiyon (CLI: metin → float).
    Kontrol sırası: mod → zorunlu parametre → çevirme → motor doğrulaması (SPEC §2.1).
    """
    try:
        if mode is None:
            raise ServiceError(f"Missing required parameter: {label('mode')}")
        canonical = MODES.get(mode)
        if canonical is None:
            raise ServiceError(f"Unknown mode: {mode!r} (supported: a-priori, post-hoc)")
        names = REQUIRED[canonical]
        for name in names:
            if params.get(name) is None:
                raise ServiceError(f"Missing required parameter: {label(name)}")
        values = {}
        for name in names:
            raw = params[name]
            values[name] = _finite(label(name), convert(name, raw) if convert else raw)
        if canonical == "a-priori":
            r = engine.a_priori(**values)
        else:
            r = engine.post_hoc(**values)
    except (ServiceError, engine.InputError) as e:
        return error(str(e))
    return {
        "n_total": r.n_total,
        "actual_power": r.actual_power,
        "critical": r.critical,
        "df": int(r.df) if r.df == math.floor(r.df) else r.df,  # S-3
        "ncp": r.ncp,
    }


def error(message: str) -> dict:
    return {"error": message}


def is_error(result: Mapping[str, Any]) -> bool:
    return "error" in result


def to_json(result: Mapping[str, Any]) -> str:
    """Tek satır JSON (boşluksuz); CLI'nin bastığı ve MCP'nin metin içeriği olarak döndürdüğü biçim."""
    return json.dumps(result, separators=(",", ":"))

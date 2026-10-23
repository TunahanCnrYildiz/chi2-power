"""Ortak katman (arayüz sözleşmesi v1.0.0, SPEC §0): girdi sözlüğü → motor → çıktı sözlüğü.

CLI ve MCP sunucusu motoru yalnızca buradan çağırır; ikisi de ham alan sözlüğünü
(`test`, `mode` ve alanlar) olduğu gibi verir. Böylece aynı girdide aynı çıktı ya da aynı
hata üretilir. Doğrulama sırası §0.4: test → mode → tanınmayan/ilgisiz alan → eksik alan →
tür → alan kuralları (§2.1 sırası, motorda).
"""

from __future__ import annotations

import json
import math
import platform
import re
from importlib.metadata import version as _pkg_version
from typing import Any, Mapping

from . import engine

CONTRACT_VERSION = "1.0.0"
TEST = "chi2-contingency"

# Mod → zorunlu girdi alanları (§0.1, birebir bu adlar ve bu sıra)
MODES: dict[str, tuple[str, ...]] = {
    "a-priori": ("w", "alpha", "power", "df"),
    "post-hoc": ("w", "alpha", "n_total", "df"),
    "compromise": ("w", "beta_alpha_ratio", "n_total", "df"),  # bonus (§0.7)
    "criterion": ("w", "power", "n_total", "df"),               # bonus
    "sensitivity": ("alpha", "power", "n_total", "df"),         # bonus
}
TABLE_FIELDS = ("rows", "cols")  # tek uzantı: df yerine tablo boyutu (§0.1)
INTEGER_FIELDS = {"n_total", "df", "rows", "cols"}
KNOWN_FIELDS = {f for fields in MODES.values() for f in fields} | set(TABLE_FIELDS)

MISSING_PARAM, UNKNOWN_PARAM, UNSUPPORTED = "MISSING_PARAM", "UNKNOWN_PARAM", "UNSUPPORTED"
INVALID_VALUE, INCONSISTENT, NO_SOLUTION, INTERNAL_ERROR = (
    "INVALID_VALUE", "INCONSISTENT", "NO_SOLUTION", "INTERNAL_ERROR")
INPUT_CODES = {MISSING_PARAM, UNKNOWN_PARAM, INVALID_VALUE, engine.OUT_OF_RANGE, INCONSISTENT, UNSUPPORTED}

# Ondalık ayırıcı her zaman nokta (§0.1); NaN/∞ ve virgül bu kalıba uymaz.
_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


class ServiceError(ValueError):
    def __init__(self, message: str, code: str, field: str | None):
        super().__init__(message)
        self.code = code
        self.field = field


def _text(raw: Any) -> str:
    return raw if isinstance(raw, str) else json.dumps(raw)


def _number(name: str, raw: Any) -> float:
    """Tür denetimi: sayı, sonlu; tam sayı alanlarında tam sayı değerli (100, 100.0, 1e2)."""
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise ServiceError(f"Invalid value for {name}: {_text(raw)} (not a number)", INVALID_VALUE, name)
    if isinstance(raw, str):
        if not _NUMBER.fullmatch(raw.strip()):
            raise ServiceError(f"Invalid value for {name}: {raw} (not a number)", INVALID_VALUE, name)
        value = float(raw)
    else:
        value = float(raw)
    if not math.isfinite(value):
        raise ServiceError(f"Invalid value for {name}: {_text(raw)} (must be finite)", INVALID_VALUE, name)
    if name in INTEGER_FIELDS and value != math.floor(value):
        raise ServiceError(f"Invalid value for {name}: {_text(raw)} (must be an integer)", INVALID_VALUE, name)
    return value


def _validate_shape(args: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """test → mode → tanınmayan/ilgisiz alan → eksik alan. (mod, mevcut alanlar) döndürür."""
    present = {k: v for k, v in args.items() if v is not None}
    test = present.get("test")
    if test is None:
        raise ServiceError("Missing required parameter: test", MISSING_PARAM, "test")
    if test != TEST:
        raise ServiceError(f"Unsupported test: {_text(test)} (supported: {TEST})", UNSUPPORTED, "test")
    mode = present.get("mode")
    if mode is None:
        raise ServiceError("Missing required parameter: mode", MISSING_PARAM, "mode")
    if mode not in MODES:
        raise ServiceError(f"Unsupported mode: {_text(mode)} (supported: {', '.join(MODES)})", UNSUPPORTED, "mode")
    allowed = set(MODES[mode]) | set(TABLE_FIELDS)
    for k in present:
        if k in ("test", "mode") or k in allowed:
            continue
        msg = (f"Parameter {k} is not used in mode {mode}" if k in KNOWN_FIELDS else f"Unknown parameter: {k}")
        raise ServiceError(msg, UNKNOWN_PARAM, k)
    fields = {k: v for k, v in present.items() if k not in ("test", "mode")}
    required = list(MODES[mode])
    if any(k in fields for k in TABLE_FIELDS):
        required = [f for f in required if f != "df"] + list(TABLE_FIELDS)
    for name in required:
        if name not in fields:
            extra = " (or rows and cols)" if name == "df" else ""
            raise ServiceError(f"Missing required parameter: {name}{extra}", MISSING_PARAM, name)
    return mode, fields


def _ordered(mode: str, fields: Mapping[str, Any]) -> list[str]:
    order = [f for f in MODES[mode] if f != "df"]
    head = [f for f in ("df",) + TABLE_FIELDS if f in fields]
    return head + [f for f in order if f in fields]


def _run(mode: str, v: dict[str, float]) -> dict:
    """Motoru çağırır ve §0.1 çıktı alanlarını sözleşmenin sırasıyla döndürür."""
    if mode == "a-priori":
        r = engine.a_priori(v["w"], v["alpha"], v["power"], v["df"])
        return {"ncp": r.ncp, "critical_chi2": r.critical, "n_total": r.n_total, "actual_power": r.actual_power}
    if mode == "post-hoc":
        r = engine.post_hoc(v["w"], v["alpha"], v["n_total"], v["df"])
        return {"ncp": r.ncp, "critical_chi2": r.critical, "power": r.actual_power}
    if mode == "compromise":
        c = engine.compromise(v["w"], v["beta_alpha_ratio"], v["n_total"], v["df"])
        return {"ncp": c.ncp, "critical_chi2": c.critical, "alpha": c.alpha, "beta": c.beta, "power": c.power}
    if mode == "criterion":
        k = engine.criterion(v["w"], v["power"], v["n_total"], v["df"])
        return {"ncp": k.ncp, "critical_chi2": k.critical, "alpha": k.alpha}
    s = engine.sensitivity(v["alpha"], v["power"], v["n_total"], v["df"])
    return {"ncp": s.ncp, "critical_chi2": s.critical, "w": s.w}


def compute(args: Mapping[str, Any]) -> dict:
    """Hesabı çalıştırır; başarıda §0.2 çıktı sözlüğü, hatada §0.4 hata sözlüğü döndürür.

    args: `test`, `mode` ve alanlar; değerler metin (CLI) ya da JSON sayısı (MCP) olabilir.
    None değerli alan verilmemiş sayılır.
    """
    try:
        mode, fields = _validate_shape(args)
        values = {name: _number(name, fields[name]) for name in _ordered(mode, fields)}
        if "rows" in values:
            df = engine.df_from_table(values.pop("rows"), values.pop("cols"))
            if "df" in values and values["df"] != df:
                raise ServiceError(f"Inconsistent parameters: df {values['df']:g} does not match "
                                   f"(rows - 1) * (cols - 1) = {df:g}", INCONSISTENT, "df")
            values["df"] = df
        return _run(mode, values)
    except (ServiceError, engine.InputError) as e:
        return error(str(e), e.code, e.field)
    except engine.NoSolution as e:
        return error(str(e), NO_SOLUTION, None)
    except Exception as e:  # beklenmeyen durum: iç hata (çıkış kodu 1)
        return error(f"Internal error: {type(e).__name__}: {e}", INTERNAL_ERROR, None)


def error(message: str, code: str, field: str | None) -> dict:
    return {"error": message, "code": code, "field": field}


def is_error(result: Mapping[str, Any]) -> bool:
    return "error" in result


def exit_code(result: Mapping[str, Any]) -> int:
    """§0.4: 0 başarı, 2 geçersiz girdi, 1 iç hata (NO_SOLUTION dahil)."""
    if not is_error(result):
        return 0
    return 2 if result.get("code") in INPUT_CODES else 1


def version_info() -> dict:
    return {"contract_version": CONTRACT_VERSION, "name": "chi2-power",
            "engine": f"Python {platform.python_version()}, scipy {_pkg_version('scipy')}"}


def to_json(result: Mapping[str, Any]) -> str:
    """Tek satır JSON (boşluksuz); CLI'nin bastığı ve MCP'nin metin içeriği olarak döndürdüğü biçim."""
    return json.dumps(result, separators=(",", ":"))

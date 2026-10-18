"""Sistem 1: soruyu 7 etiketten birine ayıran hızlı sınıflandırıcı (`claude -p --model haiku`).

Araç yok; çıktı JSON şemasıyla {"label", "confidence"} ile sınırlıdır, sayı (N, güç, etki) üretemez.
Jev erişimi olmadığı için ödevin izin verdiği etiket setine kısıtlı LLM kullanılır.
"""

from __future__ import annotations

import json
from typing import Any

from . import claude_cli, prompts

MODEL = "claude-haiku-5-5"  # açık kimlik; "haiku" takma adı claude-haiku-4-5'e çözülüyordu
CONFIDENCE_THRESHOLD = 0.75
SUPPORTED = {"chi2-contingency"}
ASK_LABELS = {"ambiguous", "unsupported"}


def build_command(question: str, model: str = MODEL) -> list[str]:
    return [
        "claude", "-p",
        "--model", model,
        "--output-format", "json",
        "--tools", "",
        "--strict-mcp-config",
        "--json-schema", json.dumps(prompts.SYSTEM1_SCHEMA),
        "--system-prompt", prompts.SYSTEM1_PROMPT,
        *claude_cli.common_flags(),
        question,
    ]


def _valid(pred: Any) -> dict | None:
    if not isinstance(pred, dict) or set(pred) != {"label", "confidence"}:
        return None
    if pred["label"] not in prompts.LABELS or not isinstance(pred["confidence"], (int, float)):
        return None
    if not 0 <= pred["confidence"] <= 1:
        return None
    return {"label": pred["label"], "confidence": float(pred["confidence"])}


def parse_result(res: dict) -> dict[str, Any]:
    pred = res.get("structured_output")
    if pred is None:
        try:
            pred = json.loads(res.get("result") or "")
        except json.JSONDecodeError:
            pred = None
    return {"prediction": _valid(pred), "usage": claude_cli.usage_of(res),
            "duration_api_s": (res.get("duration_ms") or 0) / 1000, "is_error": res.get("is_error"),
            "model_usage": res.get("modelUsage")}


def classify(question: str, model: str = MODEL, cwd: str | None = None) -> dict[str, Any]:
    proc = claude_cli.run(build_command(question, model), cwd=cwd, timeout=180)
    try:
        res = json.loads(proc["stdout"])
    except json.JSONDecodeError:
        res = {"is_error": True, "result": proc["stdout"][-500:]}
    out = parse_result(res)
    out.update(requested_model=model, duration_s=proc["wall_s"], returncode=proc["returncode"],
               raw_result=res.get("result"))
    return out


def route(pred: dict | None) -> str:
    """Yönlendirme kuralı: "agent" (ana ajana geç), "refer" (desteklenmiyor) ya da "ask" (araştırmacıya sor)."""
    if pred is None or pred["confidence"] < CONFIDENCE_THRESHOLD or pred["label"] in ASK_LABELS:
        return "ask"
    if pred["label"] in SUPPORTED:
        return "agent"
    return "refer"


REFER_MESSAGE = ("Bu soru {label} ailesine giriyor; bu araç yalnızca χ² olumsallık tablosunu destekliyor. "
                 "Lütfen araştırmacıya (biyoistatistikçiye) danışın.")
ASK_MESSAGE = ("Sorudan hangi testin uygun olduğunu güvenle belirleyemedim. Lütfen araştırmacıya danışın ya da "
               "sonuç değişkeninin türünü, grup yapısını, etki büyüklüğünü, α ve gücü belirtin.")

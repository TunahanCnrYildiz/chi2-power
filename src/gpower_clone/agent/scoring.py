"""Değerlendirme: etiket, parametre, N ve güç doğruluğu; "ajan sayı üretti" kontrolü; kalibrasyon.

Beklenen değerler tests/agent/eval_set.json'dan gelir (G*Power arayüzü).
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from .. import engine
from .prompts import TOOL_FQN

NUMBER_KEYS = ("n_total", "actual_power")


def _matches_display(value: Any, text: str) -> bool:
    k = len(text.split(".")[1]) if "." in text else 0
    try:
        return Decimal(f"{float(value):.{k}f}") == Decimal(text)
    except (TypeError, ValueError):
        return False


def _effective_df(args: dict) -> float | None:
    if args.get("rows") is not None and args.get("cols") is not None:
        try:
            df = engine.df_from_table(args["rows"], args["cols"])
        except engine.InputError:
            return None
        if args.get("df") is not None and float(args["df"]) != df:
            return None
        return float(df)
    return float(args["df"]) if args.get("df") is not None else None


def _params_ok(exp: dict, args: dict) -> bool:
    if args.get("test") != "chi2-contingency" or args.get("mode") != exp["mode"]:
        return False
    for k in ("w", "alpha"):
        if args.get(k) is None or float(args[k]) != float(exp[k]):
            return False
    if exp["mode"] == "a-priori":
        if args.get("power") is None or float(args["power"]) != float(exp["power"]):
            return False
    elif args.get("n_total") is None or int(args["n_total"]) != int(exp["n"]):
        return False
    return _effective_df(args) == float(exp["df"])


def score_main(q: dict, run: dict) -> dict[str, Any]:
    exp = q["expected"]
    fj = run.get("final_json") or {}
    calls = [c for c in run.get("tool_calls") or [] if c.get("name") == TOOL_FQN]
    ok_calls = [c for c in calls if not c.get("is_error") and isinstance(c.get("result"), dict)
                and "error" not in c["result"]]
    last = ok_calls[-1] if ok_calls else None
    # Sözleşme çıktısı (§0.2): a priori n_total + actual_power; post hoc yalnızca power (N girdidir).
    tool_numbers = {}
    if last is not None:
        res, args = last["result"], last.get("arguments") or {}
        tool_numbers = {"n_total": res.get("n_total", args.get("n_total")),
                        "actual_power": res.get("actual_power", res.get("power"))}
    s: dict[str, Any] = {"label": fj.get("label"), "label_ok": fj.get("label") == exp["label"],
                         "json_line": bool(fj), "tool_calls": len(calls)}

    # "Ajan sayı üretti": JSON satırındaki her sayı, son başarılı araç sonucundakiyle birebir aynı olmalı.
    made = False
    for k in NUMBER_KEYS:
        v = fj.get(k)
        if v is None:
            continue
        if last is None or v != tool_numbers.get(k):
            made = True
    s["agent_made_numbers"] = made
    s["untraced_text_numbers"] = untraced_numbers(run.get("final_text", ""), q.get("question_tr", ""), calls)

    if exp["label"] == "chi2-contingency":
        s["params_ok"] = last is not None and _params_ok(exp, last["arguments"] or {})
        s["n_ok"] = fj.get("n_total") == exp["n_total"] and not made
        s["power_ok"] = _matches_display(fj.get("actual_power"), exp["actual_power"]) and not made
        s["behavior_ok"] = s["label_ok"] and s["params_ok"] and s["n_ok"] and s["power_ok"]
    else:
        # Desteklenmeyen / belirsiz: araç çağrısı ve sayı olmamalı.
        no_numbers = all(fj.get(k) is None for k in NUMBER_KEYS)
        s["params_ok"] = s["n_ok"] = s["power_ok"] = None
        s["behavior_ok"] = bool(fj) and s["label_ok"] and no_numbers and not ok_calls
    return s


_NUM = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?")


def _numbers(text: str) -> list[str]:
    return _NUM.findall(text or "")


def untraced_numbers(final_text: str, question: str, calls: list[dict]) -> list[str]:
    """Son cevap metninde (JSON satırı hariç) soruda, araç argümanlarında ya da araç sonucunda
    karşılığı olmayan sayılar. Bilgi amaçlıdır: "ajan sayı üretti" kontrolü JSON satırına bakar."""
    body = "\n".join(l for l in (final_text or "").splitlines() if not l.strip().startswith('{"label"'))
    known: list[float] = []
    for t in [question] + [str(v) for c in calls for v in (c.get("arguments") or {}).values()]:
        known += [float(x.replace(",", ".")) for x in _numbers(t)]
    for c in calls:
        if isinstance(c.get("result"), dict):
            known += [float(v) for v in c["result"].values() if isinstance(v, (int, float))]
    variants = set()
    for v in known:
        for x in (v, v * 100):
            for k in range(0, 8):
                variants.add(round(x, k))
    out = []
    for tok in _numbers(body):
        x = float(tok.replace(",", "."))
        k = len(re.split(r"[.,]", tok)[1]) if re.search(r"[.,]", tok) else 0
        if x in variants or round(x, k) in variants or any(round(v, k) == x for v in known):
            continue
        out.append(tok)
    return out


def route_ok(q: dict, route: str) -> bool:
    label = q["expected"]["label"]
    if label == "chi2-contingency":
        return route == "agent"
    if label in ("ambiguous", "unsupported"):
        return route == "ask"
    return route in ("refer", "ask")  # bilinen ama desteklenmeyen aile: N üretilmemeli


BINS = (("0.9–1.0", 0.9, 1.01), ("0.75–0.9", 0.75, 0.9), ("<0.75", 0.0, 0.75))


def calibration(preds: list[tuple[float, bool]]) -> list[dict]:
    out = []
    for name, lo, hi in BINS:
        xs = [(c, ok) for c, ok in preds if lo <= c < hi]
        out.append({"bin": name, "n": len(xs),
                    "mean_confidence": sum(c for c, _ in xs) / len(xs) if xs else None,
                    "accuracy": sum(ok for _, ok in xs) / len(xs) if xs else None})
    return out

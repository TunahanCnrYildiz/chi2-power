"""MCP ↔ GUI karşılaştırma bölümü.

Rapora eklemek için:  python -m gpower_clone.agent.evaluate --report-only
Yalnızca bölümü görmek için:  python -m gpower_clone.agent.gui_compare

GUI yolu ayrı bir oturumda G*Power ekran görüntüleriyle ölçülür ve
tests/reports/agent/gui_results.json dosyasına yazılır. Dosya yoksa bölüm "bekleniyor" der.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .claude_cli import USAGE_KEYS


def _shots(g: dict) -> int | None:
    v = g.get("screenshots")
    if isinstance(v, list):
        return len(v)
    return None if v is None else int(v)


def _total(u: dict) -> int:
    return sum(int(u.get(k) or 0) for k in USAGE_KEYS)


def _gui_correct(g: dict, q: dict | None) -> bool | None:
    if q is None:
        return None
    exp = q["expected"]
    if g.get("label") != exp["label"]:
        return False
    if exp["label"] != "chi2-contingency":
        return g.get("n_total") in (None, "")
    return str(g.get("n_total")) == str(exp["n_total"]) and str(g.get("actual_power")) == exp["actual_power"]


FAIRNESS = (
    "**Adalet notu.** MCP yolu her soruyu ayrı bir `claude -p` çağrısında çözer; her soru kendi başlangıç "
    "maliyetini (sistem prompt'u, araç şeması, Claude Code'un arka plan çağrıları) taşır ve ayrı bir hazırlık "
    "maliyeti yoktur. GUI yolu tek uzun bir konuşmadır; her çağrı birikmiş geçmişi ve ekran görüntülerini "
    "yeniden okur (önbellek okuma sütunu), G\\*Power'ı açma ve kapanış özeti gibi pencere dışı çağrılar "
    "`gui_overhead.json` içinde ayrıca sayılır. Q07–Q10'da GUI kullanılmadı ve o pencerelerde model çağrısı yok; "
    "bu sorularda GUI satırının sıfır olması, kararın daha önceki bir çağrıda verildiği anlamına gelir.")


def section(gui_path: Path, mcp_rows: list[dict], eval_questions: list[dict] | None = None) -> str:
    L = ["## MCP ↔ GUI karşılaştırması\n"]
    gui_path = Path(gui_path)
    if not gui_path.exists():
        L.append(f"GUI ölçümleri bekleniyor (`{gui_path.as_posix()}` henüz yok).\n")
        return "\n".join(L)
    gui = {g["id"]: g for g in json.loads(gui_path.read_text(encoding="utf-8"))}
    overhead_path = gui_path.with_name("gui_overhead.json")
    overhead = (json.loads(overhead_path.read_text(encoding="utf-8")).get("overhead", [])
                if overhead_path.exists() else [])
    qs = {q["id"]: q for q in eval_questions or []}
    mcp = {r["id"]: r for r in mcp_rows}
    L.append("Token sütunları: girdi / önbellek yazma / önbellek okuma / çıktı.\n")
    L.append("| Soru | MCP token | MCP toplam | MCP süre (s) | MCP doğru | GUI token | GUI toplam | GUI süre (s) "
             "| GUI model çağrısı | Ekran görüntüsü | GUI doğru |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    tm = {"tok": 0, "dur": 0.0, "ok": 0, "n": 0}
    tg = {"tok": 0, "dur": 0.0, "ok": 0, "n": 0, "calls": 0, "shots": 0}
    for qid in sorted(set(gui) | set(mcp)):
        m, g = mcp.get(qid), gui.get(qid)
        cells = [f"| {qid} |"]
        if m:
            u = m["usage"]
            ok = m["score"]["behavior_ok"]
            cells += [" / ".join(str(u[k]) for k in USAGE_KEYS) + " |", f"{_total(u)} |",
                      f"{m['duration_s']:.1f} |", f"{'✔' if ok else '✘'} |"]
            tm["tok"] += _total(u); tm["dur"] += m["duration_s"]; tm["ok"] += bool(ok); tm["n"] += 1
        else:
            cells += ["— |"] * 4
        if g:
            ok = _gui_correct(g, qs.get(qid))
            cells += [" / ".join(str(g.get(k, 0)) for k in USAGE_KEYS) + " |", f"{_total(g)} |",
                      f"{float(g.get('duration_s') or 0):.1f} |", f"{g.get('model_calls', '—')} |",
                      f"{'—' if _shots(g) is None else _shots(g)} |", f"{'—' if ok is None else ('✔' if ok else '✘')} |"]
            tg["tok"] += _total(g); tg["dur"] += float(g.get("duration_s") or 0)
            tg["ok"] += bool(ok); tg["n"] += 1
            tg["calls"] += int(g.get("model_calls") or 0); tg["shots"] += _shots(g) or 0
        else:
            cells += ["— |"] * 6
        L.append(" ".join(cells))
    L.append(f"| **Toplam (sorular)** | | **{tm['tok']}** | **{tm['dur']:.1f}** | **{tm['ok']}/{tm['n']}** | | "
             f"**{tg['tok']}** | **{tg['dur']:.1f}** | **{tg['calls']}** | **{tg['shots']}** | **{tg['ok']}/{tg['n']}** |")
    oh_tok = sum(_total(o) for o in overhead)
    oh_calls = sum(int(o.get("model_calls") or 0) for o in overhead)
    if overhead:
        for o in overhead:
            L.append(f"| GUI {o['id']} | | | | | " + " / ".join(str(o.get(k, 0)) for k in USAGE_KEYS)
                     + f" | {_total(o)} | | {o.get('model_calls', '—')} | | |")
        L.append(f"| **Hazırlık dahil toplam** | | **{tm['tok']}** | | | | **{tg['tok'] + oh_tok}** | | "
                 f"**{tg['calls'] + oh_calls}** | | |")
    L.append("")
    if tm["tok"] and tg["tok"]:
        L.append(f"- Yalnızca soru pencereleri: GUI yolu MCP yolunun **{tg['tok'] / tm['tok']:.1f}×** token'ını"
                 + (f" ve **{tg['dur'] / tm['dur']:.1f}×** süresini" if tm["dur"] else "") + " harcadı.")
        if overhead:
            L.append(f"- Hazırlık ve kapanış dahil: GUI **{tg['tok'] + oh_tok}**, MCP **{tm['tok']}** token "
                     f"(**{(tg['tok'] + oh_tok) / tm['tok']:.1f}×**).")
        L.append(f"- Doğruluk: MCP {tm['ok']}/{tm['n']}, GUI {tg['ok']}/{tg['n']}.")
    L.append("")
    L.append(FAIRNESS)
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    import sys

    from .evaluate import EVAL, OUT, _latest, _read

    qs = json.loads(EVAL.read_text(encoding="utf-8"))["questions"]
    main_rows = list(_latest(_read(OUT / "main_runs.jsonl")).values())
    sys.stdout.reconfigure(encoding="utf-8")
    print(section(OUT / "gui_results.json", main_rows, eval_questions=qs))

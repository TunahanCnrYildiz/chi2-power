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
    ap = str(g.get("actual_power") or "")
    return str(g.get("n_total")) == str(exp["n_total"]) and ap.startswith(exp["actual_power"][:6])


def section(gui_path: Path, mcp_rows: list[dict], eval_questions: list[dict] | None = None) -> str:
    L = ["## MCP ↔ GUI karşılaştırması\n"]
    if not Path(gui_path).exists():
        L.append(f"GUI ölçümleri bekleniyor (`{Path(gui_path).as_posix()}` henüz yok).\n")
        return "\n".join(L)
    gui = {g["id"]: g for g in json.loads(Path(gui_path).read_text(encoding="utf-8"))}
    qs = {q["id"]: q for q in eval_questions or []}
    mcp = {r["id"]: r for r in mcp_rows}
    L.append("| Soru | MCP token (girdi / önb. yazma / önb. okuma / çıktı) | MCP toplam | MCP süre (s) | MCP doğru "
             "| GUI token (girdi / önb. yazma / önb. okuma / çıktı) | GUI toplam | GUI süre (s) | GUI doğru |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    tot = {"mcp": [0, 0.0, 0, 0], "gui": [0, 0.0, 0, 0]}  # token, süre, doğru, sayı
    for qid in sorted(set(gui) | set(mcp)):
        m, g = mcp.get(qid), gui.get(qid)
        cells = [f"| {qid} |"]
        if m:
            u = m["usage"]
            ok = m["score"]["behavior_ok"]
            cells += [" / ".join(str(u[k]) for k in USAGE_KEYS) + " |", f"{_total(u)} |",
                      f"{m['duration_s']:.1f} |", f"{'✔' if ok else '✘'} |"]
            tot["mcp"][0] += _total(u); tot["mcp"][1] += m["duration_s"]; tot["mcp"][2] += bool(ok); tot["mcp"][3] += 1
        else:
            cells += ["— |"] * 4
        if g:
            ok = _gui_correct(g, qs.get(qid))
            cells += [" / ".join(str(g.get(k, 0)) for k in USAGE_KEYS) + " |", f"{_total(g)} |",
                      f"{float(g.get('duration_s') or 0):.1f} |", f"{'—' if ok is None else ('✔' if ok else '✘')} |"]
            tot["gui"][0] += _total(g); tot["gui"][1] += float(g.get("duration_s") or 0)
            tot["gui"][2] += bool(ok); tot["gui"][3] += 1
        else:
            cells += ["— |"] * 4
        L.append(" ".join(cells))
    m, g = tot["mcp"], tot["gui"]
    L.append(f"| **Toplam** | | **{m[0]}** | **{m[1]:.1f}** | **{m[2]}/{m[3]}** | | **{g[0]}** | **{g[1]:.1f}** "
             f"| **{g[2]}/{g[3]}** |")
    if m[0] and g[0]:
        L.append(f"\nGUI yolu MCP yoluna göre toplam token'da **{g[0] / m[0]:.1f}×**, sürede "
                 f"**{(g[1] / m[1]) if m[1] else float('nan'):.1f}×**.")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    import sys

    from .evaluate import EVAL, OUT, _latest, _read

    qs = json.loads(EVAL.read_text(encoding="utf-8"))["questions"]
    main_rows = list(_latest(_read(OUT / "main_runs.jsonl")).values())
    sys.stdout.reconfigure(encoding="utf-8")
    print(section(OUT / "gui_results.json", main_rows, eval_questions=qs))

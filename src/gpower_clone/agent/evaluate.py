"""Ajan değerlendirmesi: 10 soru, gerçek `claude -p` çalıştırmaları, JSONL kayıtları ve rapor.

Kullanım:
    python -m gpower_clone.agent.evaluate                 # ana ajan + Sistem 1 (3 tekrar × TR/EN)
    python -m gpower_clone.agent.evaluate --only Q01,Q07  # seçili sorular
    python -m gpower_clone.agent.evaluate --skip-main     # yalnızca Sistem 1
    python -m gpower_clone.agent.evaluate --report-only   # mevcut kayıtlardan raporu yeniden üret

Kayıtlar: tests/reports/agent/main_runs.jsonl, tests/reports/agent/system1_runs.jsonl
Rapor:    tests/reports/agent_report.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

from . import gui_compare, main_agent, scoring, system1
from .claude_cli import USAGE_KEYS

ROOT = Path(__file__).resolve().parents[3]
EVAL = ROOT / "tests" / "agent" / "eval_set.json"
OUT = ROOT / "tests" / "reports" / "agent"
REPORT = ROOT / "tests" / "reports" / "agent_report.md"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_main(questions: list[dict], out: Path, cwd: str) -> None:
    for q in questions:
        print(f"[ana ajan] {q['id']} …", file=sys.stderr, flush=True)
        run = main_agent.answer(q["question_tr"], cwd=cwd)
        rec = {"id": q["id"], "timestamp": _now(), **run, "score": scoring.score_main(q, run)}
        _append(out / "main_runs.jsonl", rec)
        print(f"   → {rec['score']}", file=sys.stderr, flush=True)


def run_system1(questions: list[dict], out: Path, cwd: str, repeats: int) -> None:
    for rep in range(repeats):
        for q in questions:
            for lang in ("tr", "en"):
                res = system1.classify(q[f"question_{lang}"], cwd=cwd)
                pred = res["prediction"]
                route = system1.route(pred)
                rec = {"id": q["id"], "lang": lang, "rep": rep, "timestamp": _now(), **res,
                       "expected_label": q["expected"]["label"],
                       "correct": pred is not None and pred["label"] == q["expected"]["label"],
                       "route": route, "route_ok": scoring.route_ok(q, route)}
                _append(out / "system1_runs.jsonl", rec)
                print(f"[sistem 1] {q['id']} {lang} #{rep}: {pred} → {route}", file=sys.stderr, flush=True)


# ---------- rapor ----------

def _latest(records: list[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for r in records:
        by[r["id"]] = r  # aynı soru yeniden çalıştırıldıysa son kayıt geçerlidir
    return by


def _pct(a: int, b: int) -> str:
    return f"{a}/{b} (%{100 * a / b:.0f})" if b else "—"


def _models(rec: dict) -> str:
    mu = rec.get("model_usage") or {}
    return ", ".join(mu) if mu else (rec.get("model") or "?")


def _fmt_args(call: dict | None) -> str:
    if not call:
        return "—"
    return ", ".join(f"{k}={v}" for k, v in (call.get("arguments") or {}).items())


def build_report(questions: list[dict], main_recs: list[dict], s1_recs: list[dict], gui_path: Path) -> str:
    qs = {q["id"]: q for q in questions}
    main = _latest(main_recs)
    L = ["# AI ajanı değerlendirme raporu\n",
         "Mimari: Sistem 1 (etiket, `claude -p --model haiku`, araçsız, JSON şemalı) → MCP ajanı "
         "(`claude -p --model opus`, tek araç `chi2_contingency_power`) → gpower-clone motoru. "
         "Ajan hesap yapmaz; sayılar motordan gelir.\n",
         f"- Değerlendirme seti: `tests/agent/eval_set.json` ({len(questions)} soru)",
         f"- Kayıtlar: `tests/reports/agent/main_runs.jsonl` ({len(main_recs)} çalıştırma), "
         f"`tests/reports/agent/system1_runs.jsonl` ({len(s1_recs)} çalıştırma)",
         f"- Toplam `claude -p` çağrısı: **{len(main_recs) + len(s1_recs)}**"]
    if main:
        models = sorted({_models(r) for r in main.values()})
        L.append(f"- Ana ajan modeli (claude JSON çıktısından): {', '.join(models)}")
    if s1_recs:
        L.append(f"- Sistem 1 modeli: {', '.join(sorted({_models(r) for r in s1_recs}))}")
    L.append("")

    # --- ana ajan ---
    L.append("## Ana ajan (MCP yolu)\n")
    if not main:
        L.append("Henüz çalıştırma yok.\n")
    else:
        rows = [main[i] for i in qs if i in main]
        sc = [r["score"] for r in rows]
        L.append(f"- **Doğru seçim oranı (etiket):** {_pct(sum(s['label_ok'] for s in sc), len(sc))}")
        L.append(f"- **Doğru davranış (etiket + parametre + N/güç ya da sayısız yönlendirme):** "
                 f"{_pct(sum(bool(s['behavior_ok']) for s in sc), len(sc))}")
        chi = [r["score"] for r in rows if qs[r["id"]]["expected"]["label"] == "chi2-contingency"]
        L.append(f"- **χ² sorularında:** parametre {_pct(sum(bool(s['params_ok']) for s in chi), len(chi))}, "
                 f"N {_pct(sum(bool(s['n_ok']) for s in chi), len(chi))}, "
                 f"güç (7 ondalık) {_pct(sum(bool(s['power_ok']) for s in chi), len(chi))}")
        made = [r["id"] for r in rows if r["score"]["agent_made_numbers"]]
        L.append(f"- **\"Ajan sayı üretti\" kontrolü:** {len(made)} soru işaretlendi"
                 + (f" ({', '.join(made)})" if made else "") + ". JSON satırındaki her sayı, son başarılı "
                 "araç sonucundaki değerle birebir karşılaştırılır.")
        L.append("")
        L.append("| Soru | Beklenen | Ajan etiketi | Araç argümanları | n_total | actual_power | Beklenen N / güç "
                 "| Davranış | Sayı üretti |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            q, s, fj = qs[r["id"]], r["score"], r.get("final_json") or {}
            exp = q["expected"]
            calls = r.get("tool_calls") or []
            want = f"{exp['n_total']} / {exp['actual_power']}" if "n_total" in exp else "yönlendir / sor"
            L.append(f"| {r['id']} | {exp['label']} | {fj.get('label', '—')} | {_fmt_args(calls[-1] if calls else None)} "
                     f"| {fj.get('n_total')} | {fj.get('actual_power')} | {want} | "
                     f"{'✔' if s['behavior_ok'] else '✘'} | {'⚠ evet' if s['agent_made_numbers'] else 'hayır'} |")
        L.append("")
        L.append("### MCP yolu: token ve süre\n")
        L.append("| Soru | Girdi | Önbellek yazma | Önbellek okuma | Çıktı | Toplam | Araç çağrısı | Tur | Süre (s, duvar) "
                 "| Süre (s, API) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        tot = Counter()
        dur = dur_api = 0.0
        for r in rows:
            u = r["usage"]
            total = sum(u[k] for k in USAGE_KEYS)
            tot.update({k: u[k] for k in USAGE_KEYS})
            dur += r["duration_s"]
            dur_api += r.get("duration_api_s") or 0
            L.append(f"| {r['id']} | {u['input_tokens']} | {u['cache_creation_input_tokens']} | "
                     f"{u['cache_read_input_tokens']} | {u['output_tokens']} | {total} | {len(r.get('tool_calls') or [])} "
                     f"| {r.get('num_turns')} | {r['duration_s']:.1f} | {(r.get('duration_api_s') or 0):.1f} |")
        L.append(f"| **Toplam** | {tot['input_tokens']} | {tot['cache_creation_input_tokens']} | "
                 f"{tot['cache_read_input_tokens']} | {tot['output_tokens']} | **{sum(tot.values())}** | | | "
                 f"**{dur:.1f}** | {dur_api:.1f} |")
        L.append("")
        L.append("Ajanın erişebildiği araçlar (claude `init` olayından): "
                 + ", ".join(sorted({t for r in rows for t in (r.get('init_tools') or [])})) + "\n")

    # --- Sistem 1 ---
    L.append("## Sistem 1 (etiket sınıflandırıcı)\n")
    if not s1_recs:
        L.append("Henüz çalıştırma yok.\n")
    else:
        reps = max(r["rep"] for r in s1_recs) + 1
        L.append(f"Her soru Türkçe ve İngilizce olarak {reps} kez çalıştırıldı ({len(s1_recs)} çağrı). "
                 f"Kural: confidence < {system1.CONFIDENCE_THRESHOLD} ya da etiket ambiguous/unsupported → "
                 "araştırmacıya sor; chi2-contingency → ana ajan; diğer bilinen aileler → desteklenmiyor, yönlendir.\n")
        L.append("| Dil | Etiket doğruluğu | Yönlendirme doğruluğu | Geçersiz çıktı | Ort. güven |")
        L.append("|---|---|---|---|---|")
        for lang in ("tr", "en"):
            xs = [r for r in s1_recs if r["lang"] == lang]
            confs = [r["prediction"]["confidence"] for r in xs if r["prediction"]]
            L.append(f"| {lang.upper()} | {_pct(sum(r['correct'] for r in xs), len(xs))} | "
                     f"{_pct(sum(r['route_ok'] for r in xs), len(xs))} | {sum(r['prediction'] is None for r in xs)} | "
                     f"{(sum(confs) / len(confs)) if confs else 0:.2f} |")
        L.append("")
        L.append("### Soru bazında (tüm tekrarlar)\n")
        L.append("| Soru | Beklenen | TR tahminleri | EN tahminleri | TR yönlendirme | EN yönlendirme |")
        L.append("|---|---|---|---|---|---|")
        for qid in qs:
            cells = [qid, qs[qid]["expected"]["label"]]
            for lang in ("tr", "en"):
                xs = [r for r in s1_recs if r["id"] == qid and r["lang"] == lang]
                cells.append(", ".join(f"{r['prediction']['label']} ({r['prediction']['confidence']:.2f})"
                                       if r["prediction"] else "geçersiz" for r in xs))
            for lang in ("tr", "en"):
                xs = [r for r in s1_recs if r["id"] == qid and r["lang"] == lang]
                cells.append(", ".join(f"{r['route']}{'' if r['route_ok'] else ' ✘'}" for r in xs))
            L.append("| " + " | ".join(cells) + " |")
        L.append("")
        L.append("### Kalibrasyon\n")
        L.append("Güven aralığına düşen tahminlerin gerçek doğruluğu (\"%90 güven\" dediklerinin kaçı doğru).\n")
        L.append("| Aralık | TR n | TR ort. güven | TR doğruluk | EN n | EN ort. güven | EN doğruluk | Tümü n | Tümü doğruluk |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        cal = {}
        for lang in ("tr", "en", None):
            xs = [r for r in s1_recs if r["prediction"] and (lang is None or r["lang"] == lang)]
            cal[lang] = {b["bin"]: b for b in scoring.calibration([(r["prediction"]["confidence"], r["correct"])
                                                                    for r in xs])}

        def f(b, k):
            v = b[k]
            return "—" if v is None else (f"{v:.2f}" if k == "mean_confidence" else f"%{100 * v:.0f}")
        for name, _, _ in scoring.BINS:
            t, e, a = cal["tr"][name], cal["en"][name], cal[None][name]
            L.append(f"| {name} | {t['n']} | {f(t, 'mean_confidence')} | {f(t, 'accuracy')} | {e['n']} | "
                     f"{f(e, 'mean_confidence')} | {f(e, 'accuracy')} | {a['n']} | {f(a, 'accuracy')} |")
        L.append("")
        tok = Counter()
        for r in s1_recs:
            tok.update(r["usage"])
        L.append(f"Sistem 1 toplam token: girdi {tok['input_tokens']}, önbellek yazma {tok['cache_creation_input_tokens']}, "
                 f"önbellek okuma {tok['cache_read_input_tokens']}, çıktı {tok['output_tokens']}; "
                 f"toplam süre {sum(r['duration_s'] for r in s1_recs):.1f} s.\n")

    # --- GUI ---
    mcp_rows = [main[i] for i in qs if i in main]
    L.append(gui_compare.section(gui_path, mcp_rows, eval_questions=questions))
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eval", type=Path, default=EVAL)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--report", type=Path, default=REPORT)
    ap.add_argument("--only", default=None, help="virgülle ayrılmış soru kimlikleri")
    ap.add_argument("--s1-repeats", type=int, default=3)
    ap.add_argument("--skip-main", action="store_true")
    ap.add_argument("--skip-s1", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args(argv)
    questions = json.loads(a.eval.read_text(encoding="utf-8"))["questions"]
    selected = [q for q in questions if not a.only or q["id"] in a.only.split(",")]
    if not a.report_only:
        # Boş bir çalışma dizini: proje dosyaları (CLAUDE.md vb.) ajanın bağlamına girmez.
        with tempfile.TemporaryDirectory(prefix="gpower-agent-") as cwd:
            if not a.skip_main:
                run_main(selected, a.out, cwd)
            if not a.skip_s1:
                run_system1(selected, a.out, cwd, a.s1_repeats)
    report = build_report(questions, _read(a.out / "main_runs.jsonl"), _read(a.out / "system1_runs.jsonl"),
                          a.out / "gui_results.json")
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(report, encoding="utf-8")
    print(f"Rapor: {a.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

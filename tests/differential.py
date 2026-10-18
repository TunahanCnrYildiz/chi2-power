"""Diferansiyel test düzeneği: oracle/vectors.csv ↔ gpower-clone CLI.

Her satır için CLI gerçek bir alt süreç olarak çalıştırılır ve çıktısı,
G*Power ekranındaki metinle o metnin basamak sayısında karşılaştırılır (SPEC §3).

Kullanım:
    python tests/differential.py [--csv oracle/vectors.csv] [--report tests/reports/differential_report.md]
                                 [--cmd "gpower-clone"] [--gate 0.90]

Çıkış kodu: KAPI sağlanırsa 0, sağlanmazsa 1, CSV yoksa 2.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from displaycmp import display_digits, format_like, matches_display  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = ROOT / "tests" / "reports" / "differential_report.md"
INPUT_COLS = (("w", "--w"), ("alpha", "--alpha"), ("power", "--power"),
              ("n_total_in", "--n"), ("df", "--df"))
# (CSV sütunu, JSON alanı)
OUTPUT_COLS = (("n_total", "n_total"), ("actual_power", "actual_power"),
               ("critical", "critical"), ("df_out", "df"), ("ncp", "ncp"))


@dataclass
class FieldCheck:
    column: str
    expected: str
    found: object
    ok: bool
    note: str = ""


@dataclass
class VectorResult:
    vid: str
    kind: str  # "calc" | "error"
    argv: list[str]
    exit_code: int
    stdout: str
    checks: list[FieldCheck] = field(default_factory=list)
    n_status: str = ""  # "exact" | "mismatch" | "unverifiable" | ""

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)


def default_cmd() -> list[str]:
    return [sys.executable, "-m", "gpower_clone"]


def expected_error(notes: str) -> str | None:
    """notes'taki çift tırnaklı mesaj.

    Hücrenin tamamı CSV tırnağıyla yazılmışsa (`"mesaj"`) csv modülü tırnakları
    kaldırır; bu durumda hücrenin tamamı mesajdır. Metin içinde tırnak varsa
    (ör. not: "mesaj"; CSV'de tırnaklar ikilenerek yazılır) tırnak içi alınır.
    """
    notes = (notes or "").strip()
    m = re.search(r'"([^"]*)"', notes)
    if m:
        return m.group(1)
    return notes or None


def build_argv(row: dict) -> list[str]:
    argv = ["--test", "chi2-contingency", "--mode", row["mode"].strip()]
    for col, flag in INPUT_COLS:
        v = (row.get(col) or "").strip()
        if v:
            argv += [flag, v]
    return argv


def run_vector(row: dict, cmd: list[str]) -> VectorResult:
    argv = build_argv(row)
    p = subprocess.run(cmd + argv, capture_output=True, text=True)
    is_error = all(not (row.get(c) or "").strip() for c, _ in OUTPUT_COLS)
    res = VectorResult(row["id"], "error" if is_error else "calc", argv, p.returncode, p.stdout)

    lines = p.stdout.splitlines()
    try:
        out = json.loads(lines[0]) if len(lines) == 1 else None
    except json.JSONDecodeError:
        out = None
    if out is None:
        res.checks.append(FieldCheck("output", "tek satır JSON", p.stdout + p.stderr, False))
        if not is_error:
            res.n_status = "mismatch"
        return res

    if is_error:
        msg = expected_error(row.get("notes", ""))
        res.checks.append(FieldCheck("exit_code", "!= 0", p.returncode, p.returncode != 0))
        res.checks.append(FieldCheck("error", msg or "(notes'ta mesaj yok)", out.get("error"),
                                     msg is not None and out == {"error": msg}))
        return res

    res.checks.append(FieldCheck("exit_code", "0", p.returncode, p.returncode == 0))
    for col, key in OUTPUT_COLS:
        exp = (row.get(col) or "").strip()
        if not exp:
            continue
        got = out.get(key)
        if got is None or isinstance(got, bool) or not isinstance(got, (int, float)):
            res.checks.append(FieldCheck(col, exp, got, False, "alan yok"))
            if col == "n_total":
                res.n_status = "mismatch"
            continue
        if col == "n_total":
            kind, _ = display_digits(exp)
            if kind == "sci":
                ok = isinstance(got, int) and matches_display(got, exp)
                res.n_status = "unverifiable" if ok else "mismatch"
                res.checks.append(FieldCheck(col, exp, got, ok,
                                             "A-5: ekran hassasiyetinde karşılaştırıldı"))
            else:
                ok = isinstance(got, int) and got == int(exp)
                res.n_status = "exact" if ok else "mismatch"
                res.checks.append(FieldCheck(col, exp, got, ok))
        else:
            ok = matches_display(got, exp)
            res.checks.append(FieldCheck(col, exp, got, ok, "" if ok else f"→ {format_like(got, exp)}"))
    return res


def run_csv(path: Path, cmd: list[str]) -> list[VectorResult]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("id") or "").strip()]
    return [run_vector(r, cmd) for r in rows]


def gate(results: list[VectorResult]) -> dict:
    n_vectors = [r for r in results if r.n_status]
    exact = sum(r.n_status == "exact" for r in n_vectors)
    unver = sum(r.n_status == "unverifiable" for r in n_vectors)
    verifiable = len(n_vectors) - unver
    return {
        "n_vectors": len(n_vectors),
        "exact": exact,
        "unverifiable": unver,
        # Muhafazakâr oran: doğrulanamayan vektör (A-5) tam eşleşme sayılmaz.
        "rate": exact / len(n_vectors) if n_vectors else 0.0,
        "rate_verifiable": exact / verifiable if verifiable else 0.0,
    }


def build_report(results: list[VectorResult], csv_path: Path, threshold: float) -> tuple[str, bool]:
    g = gate(results)
    passed = g["rate"] >= threshold
    calc = [r for r in results if r.kind == "calc"]
    errs = [r for r in results if r.kind == "error"]
    L = []
    L.append("# Diferansiyel test raporu (G*Power kâhini ↔ gpower-clone)\n")
    L.append(f"- Kaynak: `{csv_path}`")
    L.append(f"- Toplam vektör: **{len(results)}** ({len(calc)} hesap, {len(errs)} hata)")
    L.append(f"- Tüm alanları tutan vektör: **{sum(r.ok for r in results)}/{len(results)}**\n")
    L.append("## KAPI: N tam eşleşme oranı\n")
    L.append(f"- `n_total` beklenen vektör: {g['n_vectors']}")
    L.append(f"- Tam eşleşme: {g['exact']}")
    L.append(f"- Tam eşleşmesi doğrulanamayan (A-5, bilimsel gösterim): {g['unverifiable']}")
    L.append(f"- **Oran (doğrulanamayan, eşleşmemiş sayılır): {g['rate']:.2%}** "
             f"— eşik {threshold:.0%} → **{'GEÇTİ' if passed else 'KALDI'}**")
    L.append(f"- Doğrulanabilir vektörler üzerinden oran: {g['rate_verifiable']:.2%}\n")

    L.append("## Alan bazında eşleşme\n")
    L.append("| Alan | Eşleşen | Karşılaştırılan |")
    L.append("|---|---|---|")
    cols = ["exit_code", "n_total", "actual_power", "critical", "df_out", "ncp", "error", "output"]
    for col in cols:
        cs = [c for r in results for c in r.checks if c.column == col]
        if cs:
            L.append(f"| `{col}` | {sum(c.ok for c in cs)} | {len(cs)} |")
    L.append("")

    bad = [r for r in results if not r.ok]
    L.append("## Tutmayan vektörler\n")
    if not bad:
        L.append("Yok.\n")
    for r in bad:
        L.append(f"### {r.vid}\n")
        L.append(f"- Çağrı: `gpower-clone {' '.join(shlex.quote(a) for a in r.argv)}`")
        L.append(f"- Çıkış kodu: {r.exit_code}; çıktı: `{r.stdout.strip()}`")
        L.append("\n| Alan | Beklenen | Bulunan | Not |\n|---|---|---|---|")
        for c in r.checks:
            if not c.ok:
                L.append(f"| `{c.column}` | `{c.expected}` | `{c.found}` | {c.note} |")
        L.append("")

    unver = [r for r in results if r.n_status == "unverifiable"]
    L.append("## Açık noktalar (SPEC §5)\n")
    if unver:
        for r in unver:
            got = next(c.found for c in r.checks if c.column == "n_total")
            exp = next(c.expected for c in r.checks if c.column == "n_total")
            L.append(f"- **A-5** {r.vid}: beklenen `{exp}` (5 anlamlı basamak), bulunan `{got}`. "
                     "Tam tamsayı değeri ekrandan doğrulanamaz; KAPI oranında eşleşmemiş sayıldı.")
    L.append("- **A-1** Parametre adları (`--w`, `--df`, `--n`) CONTRACT.md ile doğrulanmadı; "
             "eş adlar `--n-total`, `--n_total`, `--mode posthoc` kabul ediliyor.")
    L.append("- **A-2** JSON sayıları tam hassasiyetle (yuvarlamasız double) yazılıyor.")
    L.append("- **A-3** Post hoc'ta kesirli N hata veriyor (tasarım kararı); G*Power davranışı gözlenmedi.")
    L.append("- **A-4** Kritik değer scipy `chi2.isf` ile; G*Power'ın iç quantile yöntemi bilinmiyor. "
             "Alan bazında `critical` satırı bu kontrolün sonucudur.")
    L.append("")
    return "\n".join(L), passed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path, default=ROOT / "oracle" / "vectors.csv")
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown rapor dosyası")
    ap.add_argument("--cmd", default=None, help="CLI komutu (varsayılan: python -m gpower_clone)")
    ap.add_argument("--gate", type=float, default=0.90)
    a = ap.parse_args(argv)
    if not a.csv.exists():
        print(f"CSV bulunamadı: {a.csv}", file=sys.stderr)
        return 2
    cmd = shlex.split(a.cmd) if a.cmd else default_cmd()
    results = run_csv(a.csv, cmd)
    report, passed = build_report(results, a.csv, a.gate)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(report, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

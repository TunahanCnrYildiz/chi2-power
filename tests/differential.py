"""Diferansiyel test düzeneği: oracle/vectors.csv ↔ gpower-clone CLI (sözleşme v1.0.0, SPEC §0).

Her satır için CLI gerçek bir alt süreç olarak çalıştırılır. Çıktı, G*Power ekranındaki değerle
§0.6 toleransında karşılaştırılır: tam sayılar tam, ondalıklar |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6.
Sözleşme alanları: a priori `ncp, critical_chi2, n_total, actual_power`; post hoc `ncp, critical_chi2, power`
(çıktıda df yok). CSV'nin `critical` sütunu `critical_chi2` ile, post hoc satırlarının `actual_power`
sütunu `power` ile karşılaştırılır; `df_out` ve post hoc `n_total` artık çıktı olmadığından atlanır.

G-019 (df 2.5), G-023 (w 0) ve G-025 (N 1) sözleşme gereği G*Power'dan farklıdır (§0.5): bu
vektörlerde beklenen sonuç sözleşme hatasıdır; ayrı gösterilir ve uyuşmazlık sayılmaz.

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
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_util import close  # noqa: E402
from displaycmp import display_digits, matches_display  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = ROOT / "tests" / "reports" / "differential_report.md"
INPUT_COLS = (("w", "--w"), ("alpha", "--alpha"), ("power", "--power"),
              ("n_total_in", "--n_total"), ("df", "--df"))
# Hesap sütunları (boşsa satır bir hata vektörüdür)
CALC_COLS = ("ncp", "critical", "df_out", "n_total", "actual_power")
# (CSV sütunu, JSON alanı) — moda göre
OUTPUT_COLS = {
    "a-priori": (("n_total", "n_total"), ("actual_power", "actual_power"), ("critical", "critical_chi2"),
                 ("ncp", "ncp")),
    "post-hoc": (("actual_power", "power"), ("critical", "critical_chi2"), ("ncp", "ncp")),
}
# Sözleşme gereği G*Power'dan farklı vektörler (§0.5): id → (beklenen kod, alan)
CONTRACT_DIFF = {"G-019": ("INVALID_VALUE", "df"), "G-023": ("OUT_OF_RANGE", "w"),
                 "G-025": ("OUT_OF_RANGE", "n_total")}
# G*Power mesajı → (kod, alan) (§0.4)
MESSAGE_CODES = {
    "Degrees of Freedom must be greater or equal one.": ("OUT_OF_RANGE", "df"),
    "Power must be greater than or equal to alpha.": ("INCONSISTENT", "power"),
    "Alpha is outside the admissible range (1e-07, 1).": ("OUT_OF_RANGE", "alpha"),
    "Power is outside the admissible range (1e-07, 1).": ("OUT_OF_RANGE", "power"),
    "Total sample size is outside the admissible range (1, 2147483646)": ("OUT_OF_RANGE", "n_total"),
    "Effect size w must be greater 1e-06.": ("OUT_OF_RANGE", "w"),
    "Effect size w must be non-negative.": ("OUT_OF_RANGE", "w"),
}


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
    kind: str  # "calc" | "error" | "contract"
    argv: list[str]
    exit_code: int
    stdout: str
    seconds: float = 0.0
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


def _check_number(col: str, exp: str, got) -> FieldCheck:
    if got is None or isinstance(got, bool) or not isinstance(got, (int, float)):
        return FieldCheck(col, exp, got, False, "alan yok")
    ok = close(float(got), float(exp))
    return FieldCheck(col, exp, got, ok, "" if ok else f"fark {abs(float(got) - float(exp)):.3g}")


def run_vector(row: dict, cmd: list[str]) -> VectorResult:
    argv = build_argv(row)
    t = time.perf_counter()
    p = subprocess.run(cmd + argv, capture_output=True, text=True)
    seconds = time.perf_counter() - t
    vid = row["id"]
    is_error = all(not (row.get(c) or "").strip() for c in CALC_COLS)
    kind = "contract" if vid in CONTRACT_DIFF else ("error" if is_error else "calc")
    res = VectorResult(vid, kind, argv, p.returncode, p.stdout, seconds)

    lines = p.stdout.splitlines()
    try:
        out = json.loads(lines[0]) if len(lines) == 1 else None
    except json.JSONDecodeError:
        out = None
    if out is None:
        res.checks.append(FieldCheck("output", "tek satır JSON", p.stdout + p.stderr, False))
        if kind == "calc" and (row.get("n_total") or "").strip() and row["mode"].strip() == "a-priori":
            res.n_status = "mismatch"
        return res

    if kind == "contract":
        code, fld = CONTRACT_DIFF[vid]
        res.checks.append(FieldCheck("exit_code", "2", p.returncode, p.returncode == 2))
        res.checks.append(FieldCheck("code", f"{code}/{fld}", f"{out.get('code')}/{out.get('field')}",
                                     (out.get("code"), out.get("field")) == (code, fld)))
        return res

    if kind == "error":
        msg = expected_error(row.get("notes", ""))
        code, fld = MESSAGE_CODES.get(msg or "", (None, None))
        res.checks.append(FieldCheck("exit_code", "2", p.returncode, p.returncode == 2))
        res.checks.append(FieldCheck("error", msg or "(notes'ta mesaj yok)", out.get("error"),
                                     msg is not None and out.get("error") == msg))
        if code:
            res.checks.append(FieldCheck("code", f"{code}/{fld}", f"{out.get('code')}/{out.get('field')}",
                                         (out.get("code"), out.get("field")) == (code, fld)))
        return res

    mode = row["mode"].strip()
    res.checks.append(FieldCheck("exit_code", "0", p.returncode, p.returncode == 0))
    for col, key in OUTPUT_COLS.get(mode, ()):
        exp = (row.get(col) or "").strip()
        if not exp:
            continue
        got = out.get(key)
        if col == "n_total":
            kind_, _ = display_digits(exp)
            if kind_ == "sci":
                ok = isinstance(got, int) and matches_display(got, exp)
                res.n_status = "unverifiable" if ok else "mismatch"
                res.checks.append(FieldCheck(col, exp, got, ok, "A-5: ekran hassasiyetinde karşılaştırıldı"))
            else:
                ok = isinstance(got, int) and not isinstance(got, bool) and got == int(exp)
                res.n_status = "exact" if ok else "mismatch"
                res.checks.append(FieldCheck(col, exp, got, ok))
        else:
            res.checks.append(_check_number(f"{col}→{key}" if col != key else col, exp, got))
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
    contract = [r for r in results if r.kind == "contract"]
    slowest = max(results, key=lambda r: r.seconds) if results else None
    L = []
    L.append("# Diferansiyel test raporu (G*Power kâhini ↔ gpower-clone, sözleşme v1.0.0)\n")
    L.append(f"- Kaynak: `{Path(csv_path).as_posix()}`")
    L.append(f"- Toplam vektör: **{len(results)}** ({len(calc)} hesap, {len(errs)} hata, "
             f"{len(contract)} sözleşme gereği G*Power'dan farklı)")
    L.append(f"- Tüm kontrolleri tutan vektör: **{sum(r.ok for r in results)}/{len(results)}**")
    L.append("- Karşılaştırma (§0.6): tam sayılar tam; ondalıklar |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6.")
    if slowest:
        L.append(f"- Çağrı süresi (alt süreç, duvar saati): en yavaş **{slowest.seconds:.2f} s** ({slowest.vid}), "
                 f"ortalama {sum(r.seconds for r in results) / len(results):.2f} s; sınır 2 s (§0.1).")
    L.append("")
    L.append("## KAPI: N tam eşleşme oranı\n")
    L.append("Payda: `n_total` beklenen a priori hesap vektörleri (post hoc'ta `n_total` artık çıktı değil; "
             "sözleşme gereği farklı vektörler hariç).\n")
    L.append(f"- `n_total` beklenen vektör: {g['n_vectors']}")
    L.append(f"- Tam eşleşme: {g['exact']}")
    L.append(f"- Tam eşleşmesi doğrulanamayan (A-5, bilimsel gösterim): {g['unverifiable']}")
    L.append(f"- **Oran (doğrulanamayan, eşleşmemiş sayılır): {g['rate']:.2%}** "
             f"— eşik {threshold:.0%} → **{'GEÇTİ' if passed else 'KALDI'}**")
    L.append(f"- Doğrulanabilir vektörler üzerinden oran: {g['rate_verifiable']:.2%}\n")

    L.append("## Alan bazında eşleşme\n")
    L.append("| Alan | Eşleşen | Karşılaştırılan |")
    L.append("|---|---|---|")
    cols = []
    for r in results:
        for c in r.checks:
            if c.column not in cols:
                cols.append(c.column)
    for col in cols:
        cs = [c for r in results if r.kind != "contract" for c in r.checks if c.column == col]
        if cs:
            L.append(f"| `{col}` | {sum(c.ok for c in cs)} | {len(cs)} |")
    L.append("")

    L.append("## Sözleşme gereği G*Power'dan farklı (§0.5)\n")
    L.append("Bu vektörlerde G*Power bir sonuç üretir; sözleşme v1.0.0 ise girdiyi reddeder. "
             "Uyuşmazlık sayılmaz; beklenen sözleşme hatası denetlenir.\n")
    L.append("| Vektör | G*Power | Sözleşme kuralı | Beklenen | Bulunan | Durum |")
    L.append("|---|---|---|---|---|---|")
    rules = {"G-019": "df tam sayı (df = 2.5)", "G-023": "w > 0 (w = 0)", "G-025": "n_total ≥ 2 (N = 1)"}
    for r in contract:
        c = next((c for c in r.checks if c.column == "code"), None)
        L.append(f"| {r.vid} | sonuç üretir | {rules.get(r.vid, '')} | {c.expected if c else '—'} | "
                 f"{c.found if c else r.stdout.strip()} | {'✔' if r.ok else '✘'} |")
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
    for r in unver:
        got = next(c.found for c in r.checks if c.column == "n_total")
        exp = next(c.expected for c in r.checks if c.column == "n_total")
        L.append(f"- **A-5** {r.vid}: beklenen `{exp}` (5 anlamlı basamak), bulunan `{got}`. "
                 "Tam tamsayı değeri ekrandan doğrulanamaz; KAPI oranında eşleşmemiş sayıldı.")
    L.append("- **A-1** Parametre adları artık sözleşmede tanımlı (§0.1): `w, alpha, power, n_total, df`.")
    L.append("- **A-2** JSON sayıları tam double hassasiyetle yazılıyor (§0.2).")
    L.append("- **A-3** Post hoc'ta kesirli `n_total` sözleşme gereği `INVALID_VALUE`.")
    L.append("- **A-4** Kritik değer scipy `chi2.isf` ile; alan bazında `critical→critical_chi2` satırı bu "
             "kontrolün sonucudur.")
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

"""statsmodels ile ölçek vektörleri (>500) üretip gpower-clone ile karşılaştırır.

statsmodels.stats.power.GofChisquarePower, χ² uyum iyiliği testinin gücünü
crit = χ²⁻¹(1 − α; df), güç = 1 − F_ncx2(crit; df, λ = w²·N) ile hesaplar
(df = n_bins − 1). Olumsallık tablosu testi aynı formülü kullanır (SPEC §4.1 – §4.3),
bu yüzden n_bins = df + 1 verilerek karşılaştırılabilir.

statsmodels a priori'de N'yi kesirli verir; gpower-clone SPEC §4.5/4 kuralıyla
tamsayıya çevirir: n_total = ⌈ ⌊N·10¹⁰ + 0.5⌋ / 10¹⁰ ⌉. Beklenen ilişki:
n_total = ⌈N_sm⌉ (N_sm bir tamsayıya 5·10⁻¹¹'den yakın değilse).

Kullanım:
    python tests/statsmodels_vectors.py [--out tests/reports]
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import itertools
import json
import math
import sys
import warnings
from pathlib import Path

from statsmodels.stats.power import GofChisquarePower

from gpower_clone import cli, engine

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "tests" / "reports"

A_PRIORI_GRID = dict(
    w=[0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 0.9, 1.2],
    alpha=[0.01, 0.05, 0.1],
    power=[0.8, 0.9, 0.95],
    df=[1, 2, 3, 4, 6, 10],
)
POST_HOC_GRID = dict(
    w=[0.1, 0.2, 0.3, 0.5, 0.8],
    alpha=[0.01, 0.05, 0.1],
    n=[10, 30, 100, 250, 1000],
    df=[1, 2, 4, 8],
)
SM = GofChisquarePower()


def run_cli(argv: list[str]) -> tuple[int, dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(argv)
    return code, json.loads(buf.getvalue())


def sm_power(w, alpha, n, df):
    return float(SM.power(effect_size=w, nobs=n, alpha=alpha, n_bins=df + 1))


def sm_solve_n(w, alpha, power, df):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return float(SM.solve_power(effect_size=w, nobs=None, alpha=alpha, power=power, n_bins=df + 1))


def a_priori_rows():
    for w, alpha, power, df in itertools.product(*A_PRIORI_GRID.values()):
        code, out = run_cli(["--test", "chi2-contingency", "--mode", "a-priori", "--w", repr(w),
                             "--alpha", repr(alpha), "--power", repr(power), "--df", str(df)])
        assert code == 0, out
        n_sm = sm_solve_n(w, alpha, power, df)
        n_ours = engine.fractional_n(w, alpha, power, float(df))
        n_total = out["n_total"]
        expected = math.ceil(n_sm)
        frac_dist = abs(n_sm - round(n_sm))  # en yakın tamsayıya uzaklık
        if n_total == expected:
            status = "ceil-eşleşme"
        elif frac_dist < 1e-6:
            status = "tamsayıya-yakın"  # §4.5/4 ve çözücü toleransıyla açıklanır
        else:
            status = "uyuşmazlık"
        yield dict(
            mode="a-priori", w=w, alpha=alpha, power=power, n=None, df=df,
            n_sm=n_sm, n_ours_frac=n_ours, n_total=n_total, ceil_n_sm=expected,
            frac_dist=frac_dist,
            resid_ours=sm_power(w, alpha, n_ours, df) - power,
            resid_sm=sm_power(w, alpha, n_sm, df) - power,
            power_sm_at_n=sm_power(w, alpha, n_total, df),
            power_sm_at_n_minus_1=sm_power(w, alpha, n_total - 1, df) if n_total > 1 else None,
            actual_power=out["actual_power"],
            status=status,
        )


def post_hoc_rows():
    for w, alpha, n, df in itertools.product(*POST_HOC_GRID.values()):
        code, out = run_cli(["--test", "chi2-contingency", "--mode", "post-hoc", "--w", repr(w),
                             "--alpha", repr(alpha), "--n_total", str(n), "--df", str(df)])
        assert code == 0, out
        p_sm = sm_power(w, alpha, n, df)
        diff = abs(out["power"] - p_sm)
        yield dict(
            mode="post-hoc", w=w, alpha=alpha, power=None, n=n, df=df,
            power_sm=p_sm, actual_power=out["power"], abs_diff=diff,
            status="eşleşme-7" if f"{p_sm:.7f}" == f"{out['power']:.7f}" else "uyuşmazlık",
        )


def build_report(ap: list[dict], ph: list[dict]) -> str:
    n = len(ap) + len(ph)
    ceil_ok = sum(r["status"] == "ceil-eşleşme" for r in ap)
    near = [r for r in ap if r["status"] == "tamsayıya-yakın"]
    bad_ap = [r for r in ap if r["status"] == "uyuşmazlık"]
    max_dn = max(abs(r["n_ours_frac"] - r["n_sm"]) for r in ap)
    max_rel = max(abs(r["n_ours_frac"] - r["n_sm"]) / r["n_sm"] for r in ap)
    minimal = sum(r["power_sm_at_n"] >= r["power"] - 1e-12
                  and (r["power_sm_at_n_minus_1"] is None or r["power_sm_at_n_minus_1"] < r["power"])
                  for r in ap)
    res_ours = max(abs(r["resid_ours"]) for r in ap)
    res_sm = max(abs(r["resid_sm"]) for r in ap)
    ap_pow = max(abs(r["actual_power"] - r["power_sm_at_n"]) for r in ap)
    ph_ok = sum(r["status"] == "eşleşme-7" for r in ph)
    ph_max = max(r["abs_diff"] for r in ph)

    L = ["# statsmodels karşılaştırma raporu\n",
         f"- Kütüphane: `statsmodels.stats.power.GofChisquarePower` (n_bins = df + 1)",
         f"- Toplam vektör: **{n}** ({len(ap)} a priori, {len(ph)} post hoc)\n",
         "## A priori: kesirli N (statsmodels) ↔ tamsayı N (gpower-clone)\n",
         f"- `n_total == ⌈N_sm⌉`: **{ceil_ok}/{len(ap)}**",
         f"- Tamsayıya 1e-6'dan yakın N_sm (yuvarlama kuralıyla açıklanan sınır durumları): {len(near)}",
         f"- Açıklanamayan uyuşmazlık: {len(bad_ap)}",
         f"- Bizim kesirli N ile N_sm arasındaki en büyük fark: {max_dn:.3e} (göreli {max_rel:.3e})",
         f"- Kökte artık |güç(N) − hedef| en büyük değeri: gpower-clone {res_ours:.3e}, "
         f"statsmodels {res_sm:.3e} (fark statsmodels çözücüsünün daha gevşek toleransından)",
         f"- Minimallik (statsmodels gücüyle): güç(n_total) ≥ hedef ve güç(n_total − 1) < hedef: "
         f"**{minimal}/{len(ap)}**",
         f"- `actual_power` ile statsmodels gücü (aynı n_total'da) en büyük mutlak fark: {ap_pow:.3e}\n",
         "### İlişkinin açıklaması (SPEC §4.5/4)\n",
         "İki uygulama aynı denklemi, güç(w, α, N) = hedef güç, N'yi sürekli kabul ederek çözer; "
         "statsmodels kökü kesirli olarak döndürür (ör. 144.2…). gpower-clone kökü önce 10 ondalık "
         "basamağa yuvarlar (N′ = ⌊N·10¹⁰ + 0.5⌋ / 10¹⁰), sonra yukarı yuvarlar (n_total = ⌈N′⌉) ve "
         "en az 1 yapar. Güç N'de artan olduğundan ⌈N⌉, gücü hedefe ulaştıran en küçük tamsayıdır; "
         "bu yüzden n_total = ⌈N_sm⌉ beklenir. Fark ancak kesirli kök bir tamsayıya çok yakınsa "
         "(kesir < 5·10⁻¹¹ ise G*Power kuralı aşağı yuvarlar; ayrıca iki çözücünün toleransları "
         "farklıdır) ortaya çıkabilir. Bu ızgarada böyle bir durumun sayısı yukarıda verilmiştir.\n",
         "## Post hoc: güç\n",
         f"- 7 ondalıkta eşleşme: **{ph_ok}/{len(ph)}**",
         f"- En büyük mutlak fark: {ph_max:.3e}",
         "- Not: statsmodels `ncx2.sf` kullanır; gpower-clone SPEC §4.3'teki gibi `1 − CDF` kullanır. "
         "Fark makine hassasiyeti mertebesindedir.\n"]
    if near or bad_ap:
        L.append("## A priori sınır durumları / uyuşmazlıklar\n")
        L.append("| w | α | güç | df | N_sm | bizim kesirli N | n_total | ⌈N_sm⌉ | durum |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in near + bad_ap:
            L.append(f"| {r['w']} | {r['alpha']} | {r['power']} | {r['df']} | {r['n_sm']!r} | "
                     f"{r['n_ours_frac']!r} | {r['n_total']} | {r['ceil_n_sm']} | {r['status']} |")
        L.append("")
    bad_ph = [r for r in ph if r["status"] != "eşleşme-7"]
    if bad_ph:
        L.append("## Post hoc uyuşmazlıklar\n")
        for r in bad_ph:
            L.append(f"- w={r['w']} α={r['alpha']} n={r['n']} df={r['df']}: "
                     f"sm={r['power_sm']!r} biz={r['actual_power']!r}")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap_ = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap_.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap_.parse_args(argv)
    ap = list(a_priori_rows())
    ph = list(post_hoc_rows())
    a.out.mkdir(parents=True, exist_ok=True)
    cols = sorted({k for r in ap + ph for k in r}, key=lambda k: (k != "mode", k))
    with open(a.out / "statsmodels_vectors.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        wr.writerows(ap + ph)
    report = build_report(ap, ph)
    (a.out / "statsmodels_report.md").write_text(report, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    bad = sum(r["status"] == "uyuşmazlık" for r in ap + ph)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

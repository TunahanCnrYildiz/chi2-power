"""SPEC §6 kabul kriterleri (Gherkin) — her vektör ayrı bir test.

Testler CLI'nin giriş noktasını (gpower_clone.cli.main) süreç içinde çağırır;
gerçek alt süreç çağrıları test_cli.py içindedir.
"""

import json

import pytest

from displaycmp import matches_display
from gpower_clone import cli

TEST = ["--test", "chi2-contingency"]


def run(argv, capsys):
    code = cli.main(argv)
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert len(lines) == 1, f"tek satır JSON bekleniyordu: {out!r}"
    return code, json.loads(lines[0])


# ---------- A priori ----------

# id, w, alpha, power, df, n_total, actual_power, critical, ncp
A_PRIORI = [
    # tipik değerler
    ("G-001", "0.3", "0.05", "0.95", "1", "145", "0.9507851", "3.8414588", "13.0500000"),
    ("G-002", "0.3", "0.05", "0.80", "4", "133", "0.8013043", "9.4877290", "11.9700000"),
    ("G-003", "0.1", "0.05", "0.80", "2", "964", "0.8002316", "5.9914645", "9.6400000"),
    ("G-004", "0.5", "0.01", "0.90", "6", "93", "0.9011611", "16.8118938", "23.2500000"),
    ("G-020", "0.3", "0.10", "0.80", "30", "228", "0.8013717", "40.2560237", "20.5200000"),
    ("G-021", "0.3", "0.001", "0.90", "100", "865", "0.9002502", "149.4493", "77.8500000"),
    # küçük N (aralık daraltma dalı)
    ("G-009", "0.8", "0.05", "0.80", "1", "13", "0.8223816", "3.8414588", "8.3200000"),
    ("G-010", "0.9", "0.05", "0.95", "10", "31", "0.9563998", "18.3070381", "25.1100000"),
    ("G-022", "1.5", "0.05", "0.80", "2", "5", "0.8608329", "5.9914645", "11.2500000"),
    # büyük N (aralık genişletme dalı)
    ("G-011", "0.05", "0.05", "0.95", "1", "5198", "0.9500042", "3.8414588", "12.9950000"),
    ("G-012", "0.02", "0.05", "0.80", "3", "27257", "0.8000095", "7.8147279", "10.9028000"),
    # sınırlar
    ("G-007", "0.3", "0.05", "0.05", "1", "1", "0.0603726", "3.8414588", "0.0900000"),
    ("G-013", "0.000001", "0.05", "0.80", "1", "7.8489e+12", "0.8000000", "3.8414588", "7.8488605"),
    ("G-017", "0.3", "0.05", "0.9999999", "1", "570", "0.9999999", "3.8414588", "51.3000000"),
    ("G-019", "0.3", "0.05", "0.80", "2.5", "115", "0.8017509", "6.9280761", "10.3500000"),
]


@pytest.mark.parametrize(
    "vid,w,alpha,power,df,n_total,actual_power,critical,ncp",
    A_PRIORI,
    ids=[v[0] for v in A_PRIORI],
)
def test_a_priori(vid, w, alpha, power, df, n_total, actual_power, critical, ncp, capsys):
    code, out = run(
        TEST + ["--mode", "a-priori", "--w", w, "--alpha", alpha, "--power", power, "--df", df],
        capsys,
    )
    assert code == 0, out
    assert isinstance(out["n_total"], int)
    if "e" in n_total:
        # A-5: ekran yalnızca 5 anlamlı basamak gösteriyor; tam değer doğrulanamaz.
        assert matches_display(out["n_total"], n_total), out["n_total"]
    else:
        assert out["n_total"] == int(n_total)
    assert matches_display(out["actual_power"], actual_power), out["actual_power"]
    assert matches_display(out["critical"], critical), out["critical"]
    assert matches_display(out["ncp"], ncp), out["ncp"]
    assert out["df"] == float(df)


# ---------- Post hoc ----------

# id, w, alpha, n, df, power, critical, ncp
POST_HOC = [
    ("G-005", "0.3", "0.05", "100", "1", "0.8508388", "3.8414588", "9.0000000"),
    ("G-006", "0.2", "0.05", "250", "3", "0.7610631", "7.8147279", "10.0000000"),
    ("G-028", "0.5", "0.01", "30", "4", "0.3354524", "13.2767041", "7.5000000"),
    ("G-029", "0.3", "0.05", "145", "1", "0.9507851", "3.8414588", "13.0500000"),
    ("G-030", "0.25", "0.05", "200", "6", "0.7584630", "12.5915872", "12.5000000"),
    # sınırlar
    ("G-023", "0", "0.05", "100", "1", "0.0500000", "3.8414588", "0"),
    ("G-025", "0.3", "0.05", "1", "1", "0.0603726", "3.8414588", "0.0900000"),
    ("G-027", "0.1", "0.05", "100000", "5", "1.0000000", "11.0704977", "1000"),
]


@pytest.mark.parametrize(
    "vid,w,alpha,n,df,power,critical,ncp", POST_HOC, ids=[v[0] for v in POST_HOC]
)
def test_post_hoc(vid, w, alpha, n, df, power, critical, ncp, capsys):
    code, out = run(
        TEST + ["--mode", "post-hoc", "--w", w, "--alpha", alpha, "--n", n, "--df", df],
        capsys,
    )
    assert code == 0, out
    assert matches_display(out["actual_power"], power), out["actual_power"]
    assert matches_display(out["critical"], critical), out["critical"]
    assert matches_display(out["ncp"], ncp), out["ncp"]
    assert out["n_total"] == int(n)
    assert isinstance(out["n_total"], int)
    assert out["df"] == float(df)


@pytest.mark.parametrize(
    "w,power,df", [("0.3", "0.95", "1"), ("0.3", "0.05", "1")], ids=["G-001~G-029", "G-007~G-025"]
)
def test_a_priori_and_post_hoc_agree(w, power, df, capsys):
    """G-029 ↔ G-001 ve G-025 ↔ G-007: a priori ve post hoc aynı N'de aynı gücü verir."""
    _, ap = run(TEST + ["--mode", "a-priori", "--w", w, "--alpha", "0.05",
                        "--power", power, "--df", df], capsys)
    _, ph = run(TEST + ["--mode", "post-hoc", "--w", w, "--alpha", "0.05",
                        "--n", str(ap["n_total"]), "--df", df], capsys)
    assert ap["actual_power"] == ph["actual_power"]
    assert ap["ncp"] == ph["ncp"]
    assert ap["critical"] == ph["critical"]


# ---------- Geçersiz girdiler ----------

# id, mode, inputs, mesaj
INVALID = [
    ("G-008", "a-priori", dict(w="0.3", alpha="0.05", power="0.80", df="0"),
     "Degrees of Freedom must be greater or equal one."),
    ("G-014", "a-priori", dict(w="0.0000009", alpha="0.05", power="0.80", df="1"),
     "Effect size w must be greater 1e-06."),
    ("G-015", "a-priori", dict(w="0.3", alpha="0.05", power="0.04", df="1"),
     "Power must be greater than or equal to alpha."),
    ("G-016", "a-priori", dict(w="0.3", alpha="0.00000001", power="0.80", df="1"),
     "Alpha is outside the admissible range (1e-07, 1)."),
    ("G-018", "a-priori", dict(w="0.3", alpha="0.05", power="0.99999999", df="1"),
     "Power is outside the admissible range (1e-07, 1)."),
    ("G-024", "post-hoc", dict(w="-0.1", alpha="0.05", n="100", df="1"),
     "Effect size w must be non-negative."),
    ("G-026", "post-hoc", dict(w="0.3", alpha="0.05", n="0", df="1"),
     "Total sample size is outside the admissible range (1, 2147483646)"),
    # Doğrulama sırası — ilk hatalı kontrol raporlanır (SPEC §6 son senaryo)
    ("order-df-before-w", "a-priori", dict(w="0.0000009", alpha="0.05", power="0.80", df="0"),
     "Degrees of Freedom must be greater or equal one."),
]


@pytest.mark.parametrize("vid,mode,inputs,message", INVALID, ids=[v[0] for v in INVALID])
def test_invalid_inputs(vid, mode, inputs, message, capsys):
    argv = TEST + ["--mode", mode]
    for k, v in inputs.items():
        argv += [f"--{k}", v]
    code, out = run(argv, capsys)
    assert code != 0
    assert out == {"error": message}


# ---------- Yuvarlama kuralı ----------

@pytest.mark.parametrize(
    "n_frac,expected",
    [(104.00000000003, 104), (104.0000001, 105), (144.2, 145)],
    ids=["104.00000000003->104", "104.0000001->105", "144.2->145"],
)
def test_rounding_rule(n_frac, expected):
    from gpower_clone.engine import round_n

    assert round_n(n_frac) == expected

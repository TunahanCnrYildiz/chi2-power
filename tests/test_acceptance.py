"""SPEC §6 kabul kriterleri (Gherkin), sözleşme v1.0.0 (§0) ile — her vektör ayrı bir test.

- Çıktı alanları: a priori `ncp, critical_chi2, n_total, actual_power`; post hoc `ncp, critical_chi2, power`.
- Ondalıklar 1e-6 toleransla (§0.6), n_total tam eşleşir.
- G-019 (df 2.5), G-023 (w 0) ve G-025 (N 1) sözleşme gereği hata verir (§0.5).
- Hata çıktısı `{"error","code","field"}`, çıkış kodu 2.

Testler CLI'nin giriş noktasını (gpower_clone.cli.main) süreç içinde çağırır.
"""

import json

import pytest

from contract_util import close
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
    ("G-001", "0.3", "0.05", "0.95", "1", "145", "0.9507851", "3.8414588", "13.0500000"),
    ("G-002", "0.3", "0.05", "0.80", "4", "133", "0.8013043", "9.4877290", "11.9700000"),
    ("G-003", "0.1", "0.05", "0.80", "2", "964", "0.8002316", "5.9914645", "9.6400000"),
    ("G-004", "0.5", "0.01", "0.90", "6", "93", "0.9011611", "16.8118938", "23.2500000"),
    ("G-020", "0.3", "0.10", "0.80", "30", "228", "0.8013717", "40.2560237", "20.5200000"),
    ("G-021", "0.3", "0.001", "0.90", "100", "865", "0.9002502", "149.4493", "77.8500000"),
    ("G-009", "0.8", "0.05", "0.80", "1", "13", "0.8223816", "3.8414588", "8.3200000"),
    ("G-010", "0.9", "0.05", "0.95", "10", "31", "0.9563998", "18.3070381", "25.1100000"),
    ("G-022", "1.5", "0.05", "0.80", "2", "5", "0.8608329", "5.9914645", "11.2500000"),
    ("G-011", "0.05", "0.05", "0.95", "1", "5198", "0.9500042", "3.8414588", "12.9950000"),
    ("G-012", "0.02", "0.05", "0.80", "3", "27257", "0.8000095", "7.8147279", "10.9028000"),
    ("G-007", "0.3", "0.05", "0.05", "1", "1", "0.0603726", "3.8414588", "0.0900000"),
    ("G-013", "0.000001", "0.05", "0.80", "1", "7.8489e+12", "0.8000000", "3.8414588", "7.8488605"),
    ("G-017", "0.3", "0.05", "0.9999999", "1", "570", "0.9999999", "3.8414588", "51.3000000"),
]


@pytest.mark.parametrize(
    "vid,w,alpha,power,df,n_total,actual_power,critical,ncp", A_PRIORI, ids=[v[0] for v in A_PRIORI])
def test_a_priori(vid, w, alpha, power, df, n_total, actual_power, critical, ncp, capsys):
    code, out = run(TEST + ["--mode", "a-priori", "--w", w, "--alpha", alpha, "--power", power, "--df", df],
                    capsys)
    assert code == 0, out
    assert list(out) == ["ncp", "critical_chi2", "n_total", "actual_power"]
    assert isinstance(out["n_total"], int)
    if "e" in n_total:
        # A-5: ekran yalnızca 5 anlamlı basamak gösteriyor; tam değer doğrulanamaz.
        assert matches_display(out["n_total"], n_total), out["n_total"]
    else:
        assert out["n_total"] == int(n_total)
    assert close(out["actual_power"], float(actual_power)), out["actual_power"]
    assert close(out["critical_chi2"], float(critical)), out["critical_chi2"]
    assert close(out["ncp"], float(ncp)), out["ncp"]


# ---------- Post hoc ----------

# id, w, alpha, n, df, power, critical, ncp
POST_HOC = [
    ("G-005", "0.3", "0.05", "100", "1", "0.8508388", "3.8414588", "9.0000000"),
    ("G-006", "0.2", "0.05", "250", "3", "0.7610631", "7.8147279", "10.0000000"),
    ("G-028", "0.5", "0.01", "30", "4", "0.3354524", "13.2767041", "7.5000000"),
    ("G-029", "0.3", "0.05", "145", "1", "0.9507851", "3.8414588", "13.0500000"),
    ("G-030", "0.25", "0.05", "200", "6", "0.7584630", "12.5915872", "12.5000000"),
    ("G-027", "0.1", "0.05", "100000", "5", "1.0000000", "11.0704977", "1000"),
]


@pytest.mark.parametrize("vid,w,alpha,n,df,power,critical,ncp", POST_HOC, ids=[v[0] for v in POST_HOC])
def test_post_hoc(vid, w, alpha, n, df, power, critical, ncp, capsys):
    code, out = run(TEST + ["--mode", "post-hoc", "--w", w, "--alpha", alpha, "--n_total", n, "--df", df], capsys)
    assert code == 0, out
    assert list(out) == ["ncp", "critical_chi2", "power"]
    assert close(out["power"], float(power)), out["power"]
    assert close(out["critical_chi2"], float(critical)), out["critical_chi2"]
    assert close(out["ncp"], float(ncp)), out["ncp"]


def test_g029_matches_g001(capsys):
    """G-029 ↔ G-001: a priori ve post hoc aynı N'de aynı gücü verir."""
    _, ap = run(TEST + ["--mode", "a-priori", "--w", "0.3", "--alpha", "0.05", "--power", "0.95", "--df", "1"],
                capsys)
    _, ph = run(TEST + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05",
                        "--n_total", str(ap["n_total"]), "--df", "1"], capsys)
    assert ap["actual_power"] == ph["power"]
    assert ap["ncp"] == ph["ncp"] and ap["critical_chi2"] == ph["critical_chi2"]


# ---------- Sözleşme gereği G*Power'dan farklı (§0.5) ----------

CONTRACT_DIFF = [
    ("G-019", ["--mode", "a-priori", "--w", "0.3", "--alpha", "0.05", "--power", "0.80", "--df", "2.5"],
     "INVALID_VALUE", "df"),
    ("G-023", ["--mode", "post-hoc", "--w", "0", "--alpha", "0.05", "--n_total", "100", "--df", "1"],
     "OUT_OF_RANGE", "w"),
    ("G-025", ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n_total", "1", "--df", "1"],
     "OUT_OF_RANGE", "n_total"),
]


@pytest.mark.parametrize("vid,argv,code,field", CONTRACT_DIFF, ids=[v[0] for v in CONTRACT_DIFF])
def test_contract_differs_from_gpower(vid, argv, code, field, capsys):
    rc, out = run(TEST + argv, capsys)
    assert rc == 2
    assert (out["code"], out["field"]) == (code, field)


# ---------- Geçersiz girdiler ----------

INVALID = [
    ("G-008", "a-priori", dict(w="0.3", alpha="0.05", power="0.80", df="0"),
     "Degrees of Freedom must be greater or equal one.", "OUT_OF_RANGE", "df"),
    ("G-014", "a-priori", dict(w="0.0000009", alpha="0.05", power="0.80", df="1"),
     "Effect size w must be greater 1e-06.", "OUT_OF_RANGE", "w"),
    ("G-015", "a-priori", dict(w="0.3", alpha="0.05", power="0.04", df="1"),
     "Power must be greater than or equal to alpha.", "INCONSISTENT", "power"),
    ("G-016", "a-priori", dict(w="0.3", alpha="0.00000001", power="0.80", df="1"),
     "Alpha is outside the admissible range (1e-07, 1).", "OUT_OF_RANGE", "alpha"),
    ("G-018", "a-priori", dict(w="0.3", alpha="0.05", power="0.99999999", df="1"),
     "Power is outside the admissible range (1e-07, 1).", "OUT_OF_RANGE", "power"),
    ("G-024", "post-hoc", dict(w="-0.1", alpha="0.05", n_total="100", df="1"),
     "Effect size w must be non-negative.", "OUT_OF_RANGE", "w"),
    ("G-026", "post-hoc", dict(w="0.3", alpha="0.05", n_total="0", df="1"),
     "Total sample size is outside the admissible range (1, 2147483646)", "OUT_OF_RANGE", "n_total"),
    ("order-df-before-w", "a-priori", dict(w="0.0000009", alpha="0.05", power="0.80", df="0"),
     "Degrees of Freedom must be greater or equal one.", "OUT_OF_RANGE", "df"),
]


@pytest.mark.parametrize("vid,mode,inputs,message,code,field", INVALID, ids=[v[0] for v in INVALID])
def test_invalid_inputs(vid, mode, inputs, message, code, field, capsys):
    argv = TEST + ["--mode", mode]
    for k, v in inputs.items():
        argv += [f"--{k}", v]
    rc, out = run(argv, capsys)
    assert rc == 2
    assert out == {"error": message, "code": code, "field": field}


# ---------- Yuvarlama kuralı ----------

@pytest.mark.parametrize(
    "n_frac,expected",
    [(104.00000000003, 104), (104.0000001, 105), (144.2, 145)],
    ids=["104.00000000003->104", "104.0000001->105", "144.2->145"],
)
def test_rounding_rule(n_frac, expected):
    from gpower_clone.engine import round_n

    assert round_n(n_frac) == expected

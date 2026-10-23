"""Arayüz sözleşmesi v1.0.0 (SPEC §0): açık vektörler, sürüm, hata biçimi, alanlar, aralıklar, süre."""

import json

import pytest

from contract_util import INPUT_CODES, PUBLIC, close, run_cli, to_argv

CHI2_CORE = [v for v in PUBLIC if v["id"] in ("chi2-contingency/a-priori", "chi2-contingency/post-hoc")]
OTHER_FAMILIES = [v for v in PUBLIC if not v["id"].startswith("chi2-contingency/")]


# ---------- açık referans vektörleri ----------

@pytest.mark.parametrize("vec", CHI2_CORE, ids=[v["id"] for v in CHI2_CORE])
def test_public_chi2_vectors(vec):
    code, out, err, dt = run_cli(to_argv(vec["input"]))
    assert code == 0, out
    assert out.count("\n") == 1
    got = json.loads(out)
    assert set(got) == set(vec["expected"])  # yalnızca §0.1 alanları; df yok
    for k, want in vec["expected"].items():
        if isinstance(want, int) and k == "n_total":
            assert got[k] == want and isinstance(got[k], int)
        else:
            assert close(got[k], want), (k, got[k], want)
    assert dt < 2.0


@pytest.mark.parametrize("vec", OTHER_FAMILIES, ids=[v["id"] for v in OTHER_FAMILIES])
def test_public_other_families_unsupported(vec):
    code, out, _, _ = run_cli(to_argv(vec["input"]))
    assert code == 2
    got = json.loads(out)
    assert got["code"] == "UNSUPPORTED" and got["field"] == "test"
    assert set(got) == {"error", "code", "field"}


def test_a_priori_output_order():
    code, out, _, _ = run_cli(to_argv(CHI2_CORE[0]["input"]))
    assert list(json.loads(out)) == ["ncp", "critical_chi2", "n_total", "actual_power"]


def test_post_hoc_output_order():
    code, out, _, _ = run_cli(to_argv(CHI2_CORE[1]["input"]))
    assert list(json.loads(out)) == ["ncp", "critical_chi2", "power"]


# ---------- sürüm ----------

def test_version():
    import platform

    import scipy

    code, out, _, _ = run_cli(["--version"])
    assert code == 0 and out.count("\n") == 1
    assert json.loads(out) == {"contract_version": "1.0.0", "name": "chi2-power",
                               "engine": f"Python {platform.python_version()}, scipy {scipy.__version__}"}


# ---------- hata biçimi ve kodlar (§0.4) ----------

BASE_AP = ["--test", "chi2-contingency", "--mode", "a-priori"]
BASE_PH = ["--test", "chi2-contingency", "--mode", "post-hoc"]
AP = BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "0.95", "--df", "1"]
PH = BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n_total", "100", "--df", "1"]

ERRORS = [
    # (id, argv, code, field)
    ("no-test", ["--mode", "a-priori", "--w", "0.3"], "MISSING_PARAM", "test"),
    ("no-mode", ["--test", "chi2-contingency", "--w", "0.3"], "MISSING_PARAM", "mode"),
    ("unknown-test", ["--test", "t2-indep", "--mode", "a-priori"], "UNSUPPORTED", "test"),
    ("unknown-mode", ["--test", "chi2-contingency", "--mode", "posthoc"], "UNSUPPORTED", "mode"),
    ("alias-n", BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n", "100", "--df", "1"], "UNKNOWN_PARAM", "n"),
    ("alias-n-total", BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n-total", "100", "--df", "1"],
     "UNKNOWN_PARAM", "n-total"),
    ("tails", AP + ["--tails", "2"], "UNKNOWN_PARAM", "tails"),
    ("ratio", AP + ["--ratio", "1"], "UNKNOWN_PARAM", "ratio"),
    ("irrelevant-power-in-post-hoc", PH + ["--power", "0.8"], "UNKNOWN_PARAM", "power"),
    ("irrelevant-n-in-a-priori", AP + ["--n_total", "100"], "UNKNOWN_PARAM", "n_total"),
    ("unknown-before-missing", BASE_AP + ["--bogus", "1"], "UNKNOWN_PARAM", "bogus"),
    ("missing-power", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--df", "1"], "MISSING_PARAM", "power"),
    ("missing-df", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "0.9"], "MISSING_PARAM", "df"),
    ("missing-before-type", BASE_AP + ["--w", "abc", "--alpha", "0.05", "--df", "1"], "MISSING_PARAM", "power"),
    ("not-a-number", BASE_AP + ["--w", "abc", "--alpha", "0.05", "--power", "0.9", "--df", "1"],
     "INVALID_VALUE", "w"),
    ("comma-decimal", BASE_AP + ["--w", "0,3", "--alpha", "0.05", "--power", "0.9", "--df", "1"],
     "INVALID_VALUE", "w"),
    ("nan", BASE_AP + ["--w", "nan", "--alpha", "0.05", "--power", "0.9", "--df", "1"], "INVALID_VALUE", "w"),
    ("inf", BASE_AP + ["--w", "inf", "--alpha", "0.05", "--power", "0.9", "--df", "1"], "INVALID_VALUE", "w"),
    ("fractional-df", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "0.8", "--df", "2.5"],
     "INVALID_VALUE", "df"),
    ("fractional-n", BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n_total", "100.5", "--df", "1"],
     "INVALID_VALUE", "n_total"),
    ("type-before-range", BASE_AP + ["--w", "-1", "--alpha", "0.05", "--power", "0.8", "--df", "2.5"],
     "INVALID_VALUE", "df"),
    ("w-zero-post-hoc", BASE_PH + ["--w", "0", "--alpha", "0.05", "--n_total", "100", "--df", "1"],
     "OUT_OF_RANGE", "w"),
    ("n-one", BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n_total", "1", "--df", "1"], "OUT_OF_RANGE", "n_total"),
    ("alpha-zero", BASE_AP + ["--w", "0.3", "--alpha", "0", "--power", "0.8", "--df", "1"], "OUT_OF_RANGE", "alpha"),
    ("power-one", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "1", "--df", "1"], "OUT_OF_RANGE", "power"),
    ("power-lt-alpha", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "0.04", "--df", "1"],
     "INCONSISTENT", "power"),
    ("missing-value", BASE_AP + ["--w", "0.3", "--alpha", "0.05", "--power", "0.8", "--df"], "INVALID_VALUE", "df"),
    ("positional", AP + ["extra"], "UNKNOWN_PARAM", "extra"),
]


@pytest.mark.parametrize("vid,argv,code,field", ERRORS, ids=[e[0] for e in ERRORS])
def test_errors(vid, argv, code, field):
    rc, out, _, _ = run_cli(argv)
    assert out.count("\n") == 1
    got = json.loads(out)
    assert list(got) == ["error", "code", "field"]
    assert (got["code"], got["field"]) == (code, field), got
    assert isinstance(got["error"], str) and got["error"]
    assert rc == 2  # bütün girdi hataları


def test_input_error_exit_code_two_internal_one(monkeypatch, capsys):
    from gpower_clone import cli, engine

    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(engine, "a_priori", boom)
    assert cli.main(AP) == 1
    got = json.loads(capsys.readouterr().out)
    assert got["field"] is None and got["code"] not in INPUT_CODES


def test_no_solution_exit_code_one(monkeypatch, capsys):
    from gpower_clone import cli, engine

    def overflow(f, *a, **k):
        raise engine.BracketOverflow()

    monkeypatch.setattr(engine, "find_bracket", overflow)
    assert cli.main(AP) == 1
    assert json.loads(capsys.readouterr().out) == {
        "error": engine.MSG_BRACKET_OVERFLOW, "code": "NO_SOLUTION", "field": None}


def test_gpower_message_kept_as_error_text():
    rc, out, _, _ = run_cli(BASE_PH + ["--w", "0.3", "--alpha", "0.05", "--n_total", "0", "--df", "1"])
    assert json.loads(out) == {"error": "Total sample size is outside the admissible range (1, 2147483646)",
                               "code": "OUT_OF_RANGE", "field": "n_total"}


def test_equals_syntax_and_rows_cols_extension():
    rc, out, _, _ = run_cli(["--test=chi2-contingency", "--mode=a-priori", "--w=0.3", "--alpha=0.05",
                             "--power=0.95", "--rows=2", "--cols=6"])
    ref = run_cli(to_argv(CHI2_CORE[0]["input"]))[1]
    assert rc == 0 and json.loads(out) == json.loads(ref)


def test_stdout_only_json_on_success():
    rc, out, err, _ = run_cli(AP)
    assert rc == 0 and out.count("\n") == 1 and out.startswith("{")

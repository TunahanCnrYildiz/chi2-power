"""CLI ayrıntıları: rows/cols uzantısı, negatif değer, gerçek alt süreç (`python -m`, console script)."""

import json
import shutil
import subprocess
import sys

import pytest

from gpower_clone import cli

BASE = ["--test", "chi2-contingency"]


def run(argv, capsys):
    code = cli.main(argv)
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1, repr(out)
    return code, json.loads(out)


@pytest.mark.parametrize("rows,cols,df", [("2", "2", "1"), ("3", "3", "4"), ("2", "3", "2"), ("4", "3", "6")])
def test_rows_cols_equivalent_to_df(rows, cols, df, capsys):
    common = BASE + ["--mode", "a-priori", "--w", "0.3", "--alpha", "0.05", "--power", "0.8"]
    _, by_df = run(common + ["--df", df], capsys)
    code, by_table = run(common + ["--rows", rows, "--cols", cols], capsys)
    assert code == 0 and by_table == by_df
    code, both = run(common + ["--rows", rows, "--cols", cols, "--df", df], capsys)
    assert code == 0 and both == by_df


@pytest.mark.parametrize("extra,code,field", [
    (["--rows", "3"], "MISSING_PARAM", "cols"),
    (["--cols", "3"], "MISSING_PARAM", "rows"),
    ([], "MISSING_PARAM", "df"),
    (["--rows", "3", "--cols", "3", "--df", "2"], "INCONSISTENT", "df"),
    (["--rows", "1", "--cols", "3"], "OUT_OF_RANGE", "rows"),
    (["--rows", "3", "--cols", "2.5"], "INVALID_VALUE", "cols"),
    (["--rows", "x", "--cols", "3"], "INVALID_VALUE", "rows"),
])
def test_rows_cols_errors(extra, code, field, capsys):
    rc, out = run(BASE + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n_total", "100"] + extra,
                  capsys)
    assert rc == 2
    assert (out["code"], out["field"]) == (code, field), out


def test_negative_value_accepted_as_value(capsys):
    rc, out = run(BASE + ["--mode", "post-hoc", "--w", "-0.1", "--alpha", "0.05", "--n_total", "100", "--df", "1"],
                  capsys)
    assert rc == 2
    assert out == {"error": "Effect size w must be non-negative.", "code": "OUT_OF_RANGE", "field": "w"}


def test_integer_valued_decimal_accepted_for_integer_fields(capsys):
    """Tasarım kararı: 100.0 ve 1e2 gibi tam sayı değerli yazımlar n_total/df için kabul edilir."""
    _, a = run(BASE + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n_total", "100", "--df", "1"],
               capsys)
    _, b = run(BASE + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n_total", "1e2", "--df", "1.0"],
               capsys)
    assert a == b


def test_duplicate_field_is_invalid(capsys):
    rc, out = run(BASE + ["--mode", "post-hoc", "--w", "0.3", "--w", "0.4", "--alpha", "0.05",
                          "--n_total", "100", "--df", "1"], capsys)
    assert rc == 2 and (out["code"], out["field"]) == ("INVALID_VALUE", "w")


A_PRIORI_ARGS = ["--test", "chi2-contingency", "--mode", "a-priori", "--w", "0.3",
                 "--alpha", "0.05", "--power", "0.95", "--df", "1"]


def _check_subprocess(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert p.stdout.count("\n") == 1
    assert json.loads(p.stdout)["n_total"] == 145


def test_python_dash_m():
    _check_subprocess([sys.executable, "-m", "gpower_clone"] + A_PRIORI_ARGS)


def test_console_script():
    exe = shutil.which("gpower-clone")
    if exe is None:
        pytest.skip("gpower-clone console script kurulu değil (pip install -e .)")
    _check_subprocess([exe] + A_PRIORI_ARGS)


def test_error_subprocess_exit_code():
    p = subprocess.run([sys.executable, "-m", "gpower_clone", "--test", "chi2-contingency",
                        "--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n_total", "0",
                        "--df", "1"], capture_output=True, text=True)
    assert p.returncode == 2
    assert json.loads(p.stdout) == {"error": "Total sample size is outside the admissible range (1, 2147483646)",
                                    "code": "OUT_OF_RANGE", "field": "n_total"}

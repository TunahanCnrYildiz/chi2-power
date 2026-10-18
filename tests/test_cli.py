"""CLI sözleşmesi: eş adlar, ayrıştırma hataları, çıktı biçimi, gerçek alt süreç."""

import json
import shutil
import subprocess
import sys

import pytest

from gpower_clone import cli

BASE = ["--test", "chi2-contingency"]
POST = BASE + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--df", "1"]


def run(argv, capsys):
    code = cli.main(argv)
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1, repr(out)
    return code, json.loads(out)


def test_output_field_order(capsys):
    code, out = run(POST + ["--n", "100"], capsys)
    assert code == 0
    assert list(out) == ["n_total", "actual_power", "critical", "df", "ncp"]


@pytest.mark.parametrize("flag", ["--n", "--n-total", "--n_total"])
def test_n_aliases(flag, capsys):
    code, out = run(POST + [flag, "100"], capsys)
    assert code == 0 and out["n_total"] == 100


@pytest.mark.parametrize("mode", ["post-hoc", "posthoc"])
def test_mode_aliases(mode, capsys):
    code, out = run(BASE + ["--mode", mode, "--w", "0.3", "--alpha", "0.05",
                            "--n", "100", "--df", "1"], capsys)
    assert code == 0 and out["n_total"] == 100


def test_equals_syntax(capsys):
    code, out = run(["--test=chi2-contingency", "--mode=post-hoc", "--w=0.3",
                     "--alpha=0.05", "--n=100", "--df=1"], capsys)
    assert code == 0 and out["n_total"] == 100


@pytest.mark.parametrize(
    "argv",
    [
        POST,                                                  # N eksik
        POST + ["--n", "abc"],                                 # sayı değil
        POST + ["--n", "100", "--bogus", "1"],                 # bilinmeyen parametre
        POST + ["--n", "100.5"],                               # kesirli N (A-3)
        POST + ["--n", "nan"],
        BASE + ["--mode", "post-hoc", "--w", "inf", "--alpha", "0.05", "--n", "10", "--df", "1"],
        ["--test", "t2-indep", "--mode", "a-priori"],          # bilinmeyen test
        BASE + ["--mode", "sensitivity"],                      # bilinmeyen mod
        ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n", "10", "--df", "1"],  # test eksik
        [],
        POST + ["--n", "100", "extra"],                        # konumsal fazlalık
    ],
)
def test_parse_errors_are_json(argv, capsys):
    code, out = run(argv, capsys)
    assert code != 0
    assert list(out) == ["error"] and isinstance(out["error"], str) and out["error"]


@pytest.mark.parametrize("df,raw", [("1", '"df":1,'), ("1.0", '"df":1,'), ("2.5", '"df":2.5,')])
def test_df_integer_format(df, raw, capsys):
    """S-3: tamsayıya eşit df tamsayı biçiminde, değilse ondalık yazılır."""
    code = cli.main(BASE + ["--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05",
                            "--n", "100", "--df", df])
    out = capsys.readouterr().out
    assert code == 0
    assert raw in out


@pytest.mark.parametrize("mode,extra", [
    ("a-priori", ["--power", "0.95"]),
    ("post-hoc", ["--n", "145"]),
])
def test_tails_and_ratio_ignored(mode, extra, capsys):
    """S-4: sözleşmenin genel parametreleri --tails ve --ratio kabul edilir ve yok sayılır."""
    args = BASE + ["--mode", mode, "--w", "0.3", "--alpha", "0.05", "--df", "1"] + extra
    _, plain = run(args, capsys)
    code, out = run(args + ["--tails", "2", "--ratio", "1"], capsys)
    assert code == 0 and out == plain
    code, out = run(["--tails=1", "--ratio=3"] + args, capsys)
    assert code == 0 and out == plain


def test_known_param_of_other_mode_ignored(capsys):
    """S-4: moda ait olmayan bilinen parametre (a priori'de --n) yok sayılır."""
    code, out = run(BASE + ["--mode", "a-priori", "--w", "0.3", "--alpha", "0.05",
                            "--power", "0.95", "--df", "1", "--n", "7"], capsys)
    assert code == 0 and out["n_total"] == 145


def test_negative_value_accepted_as_value(capsys):
    code, out = run(BASE + ["--mode", "post-hoc", "--w", "-0.1", "--alpha", "0.05",
                            "--n", "100", "--df", "1"], capsys)
    assert code != 0
    assert out == {"error": "Effect size w must be non-negative."}


def _check_subprocess(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert p.stdout.count("\n") == 1
    out = json.loads(p.stdout)
    assert out["n_total"] == 145


A_PRIORI_ARGS = ["--test", "chi2-contingency", "--mode", "a-priori", "--w", "0.3",
                 "--alpha", "0.05", "--power", "0.95", "--df", "1"]


def test_python_dash_m():
    _check_subprocess([sys.executable, "-m", "gpower_clone"] + A_PRIORI_ARGS)


def test_console_script():
    exe = shutil.which("gpower-clone")
    if exe is None:
        pytest.skip("gpower-clone console script kurulu değil (pip install -e .)")
    _check_subprocess([exe] + A_PRIORI_ARGS)


def test_error_subprocess_exit_code():
    p = subprocess.run([sys.executable, "-m", "gpower_clone", "--test", "chi2-contingency",
                        "--mode", "post-hoc", "--w", "0.3", "--alpha", "0.05", "--n", "0",
                        "--df", "1"], capture_output=True, text=True)
    assert p.returncode != 0
    assert p.stdout == '{"error":"Total sample size is outside the admissible range (1, 2147483646)"}\n'

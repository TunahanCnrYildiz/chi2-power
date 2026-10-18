"""gpower-clone komut satırı aracı — motorun üstünde ince katman.

Argümanları ayrıştırır, sayıya çevirir, motoru çağırır ve tek satır JSON basar.
Hesap ve alan doğrulaması motordadır (engine.py).
"""

from __future__ import annotations

import argparse
import json
import math
import sys

from . import engine

TESTS = ("chi2-contingency",)
MODES = {"a-priori": "a-priori", "post-hoc": "post-hoc", "posthoc": "post-hoc"}
REQUIRED = {
    "a-priori": ("w", "alpha", "power", "df"),
    "post-hoc": ("w", "alpha", "n", "df"),
}
FLAG = {"w": "--w", "alpha": "--alpha", "power": "--power", "n": "--n", "df": "--df"}


class CliError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # argparse'ın stderr'e yazıp çıkmasını engeller
        raise CliError(message)


def _build_parser() -> _Parser:
    p = _Parser(prog="gpower-clone", allow_abbrev=False,
                description="Chi-square contingency table power analysis (G*Power compatible).")
    p.add_argument("--test")
    p.add_argument("--mode")
    p.add_argument("--w")
    p.add_argument("--alpha")
    p.add_argument("--power")
    p.add_argument("--n", "--n-total", "--n_total", dest="n")
    p.add_argument("--df")
    # Sözleşmenin genel parametreleri: kabul edilir, yok sayılır (SPEC §5.1, S-4).
    p.add_argument("--tails")
    p.add_argument("--ratio")
    return p


def _number(name: str, text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise CliError(f"Invalid numeric value for {FLAG[name]}: {text!r}") from None
    if not math.isfinite(value):
        raise CliError(f"Invalid numeric value for {FLAG[name]}: {text!r} (must be finite)")
    return value


def _run(argv: list[str]) -> engine.Result:
    args = _build_parser().parse_args(argv)
    if args.test is None:
        raise CliError("Missing required parameter: --test")
    if args.test not in TESTS:
        raise CliError(f"Unknown test: {args.test!r} (supported: {', '.join(TESTS)})")
    if args.mode is None:
        raise CliError("Missing required parameter: --mode")
    mode = MODES.get(args.mode)
    if mode is None:
        raise CliError(f"Unknown mode: {args.mode!r} (supported: a-priori, post-hoc)")
    for name in REQUIRED[mode]:
        if getattr(args, name) is None:
            raise CliError(f"Missing required parameter: {FLAG[name]}")
    values = {name: _number(name, getattr(args, name)) for name in REQUIRED[mode]}
    if mode == "a-priori":
        return engine.a_priori(**values)
    return engine.post_hoc(**values)


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        r = _run(argv)
    except (CliError, engine.InputError) as e:
        _emit({"error": str(e)})
        return 1
    except Exception as e:  # beklenmeyen durumlar da tek satır JSON olarak raporlanır
        _emit({"error": f"Internal error: {e}"})
        return 2
    _emit({
        "n_total": r.n_total,
        "actual_power": r.actual_power,
        "critical": r.critical,
        "df": int(r.df) if r.df == math.floor(r.df) else r.df,  # S-3
        "ncp": r.ncp,
    })
    return 0

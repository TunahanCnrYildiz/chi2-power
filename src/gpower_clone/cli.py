"""gpower-clone komut satırı aracı — motorun üstünde ince katman.

Argümanları ayrıştırır, metni sayıya çevirir, ortak katmanı (service) çağırır
ve tek satır JSON basar. Hesap ve alan doğrulaması motordadır (engine.py).
"""

from __future__ import annotations

import argparse
import math
import sys

from . import service

TESTS = ("chi2-contingency",)
FLAG = {"mode": "--mode", "w": "--w", "alpha": "--alpha", "power": "--power", "n": "--n", "df": "--df",
        "rows": "--rows", "cols": "--cols"}


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
    p.add_argument("--rows")  # df yerine tablo boyutu: df = (rows − 1)(cols − 1), motorda
    p.add_argument("--cols")
    # Sözleşmenin genel parametreleri: kabul edilir, yok sayılır (SPEC §5.1, S-4).
    p.add_argument("--tails")
    p.add_argument("--ratio")
    return p


def _number(name: str, text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise service.ServiceError(f"Invalid numeric value for {FLAG[name]}: {text!r}") from None
    if not math.isfinite(value):
        raise service.ServiceError(f"Invalid numeric value for {FLAG[name]}: {text!r} (must be finite)")
    return value


def _run(argv: list[str]) -> dict:
    try:
        args = _build_parser().parse_args(argv)
    except CliError as e:
        return service.error(str(e))
    if args.test is None:
        return service.error("Missing required parameter: --test")
    if args.test not in TESTS:
        return service.error(f"Unknown test: {args.test!r} (supported: {', '.join(TESTS)})")
    params = {name: getattr(args, name) for name in ("w", "alpha", "power", "n", "df", "rows", "cols")}
    return service.compute(args.mode, params, label=FLAG.__getitem__, convert=_number)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        result = _run(argv)
    except Exception as e:  # beklenmeyen durumlar da tek satır JSON olarak raporlanır
        result, code = service.error(f"Internal error: {e}"), 2
    else:
        code = 1 if service.is_error(result) else 0
    sys.stdout.write(service.to_json(result) + "\n")
    return code

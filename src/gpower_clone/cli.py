"""gpower-clone komut satırı aracı — ortak katmanın (service) üstünde ince katman.

Sözleşme v1.0.0 (SPEC §0): `gpower-clone --test chi2-contingency --mode <MODE> --<alan> <değer> ...`
Argümanları `--alan değer` / `--alan=değer` çiftlerine ayırır, ortak katmanı çağırır ve
stdout'a tek satır JSON basar. Doğrulama ve hesap ortak katmanda ve motordadır.
"""

from __future__ import annotations

import sys

from . import service


class _ParseError(Exception):
    def __init__(self, message: str, code: str, field: str | None):
        super().__init__(message)
        self.result = service.error(message, code, field)


def parse(argv: list[str]) -> dict[str, str]:
    """`--alan değer` çiftleri → sıralı sözlük. Değer `-` ile başlayabilir (ör. `--w -0.1`)."""
    args: dict[str, str] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if not tok.startswith("--") or tok == "--":
            raise _ParseError(f"Unexpected argument: {tok}", service.UNKNOWN_PARAM, tok)
        name, eq, value = tok[2:].partition("=")
        if not eq:
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                raise _ParseError(f"Missing value for parameter: {name}", service.INVALID_VALUE, name)
            value = argv[i + 1]
            i += 1
        if name in args:
            raise _ParseError(f"Parameter given more than once: {name}", service.INVALID_VALUE, name)
        args[name] = value
        i += 1
    return args


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--version"]:
        result = service.version_info()
        code = 0
    else:
        try:
            result = service.compute(parse(argv))
        except _ParseError as e:
            result = e.result
        code = service.exit_code(result)
    sys.stdout.write(service.to_json(result) + "\n")
    return code

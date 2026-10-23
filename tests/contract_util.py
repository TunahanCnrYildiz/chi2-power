"""Sözleşme (SPEC §0) testleri için ortak yardımcılar."""

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PUBLIC = [json.loads(line) for line in (HERE / "fixtures" / "public_vectors.jsonl").read_text(encoding="utf-8").splitlines()
          if line.strip()]
INPUT_CODES = {"MISSING_PARAM", "UNKNOWN_PARAM", "INVALID_VALUE", "OUT_OF_RANGE", "INCONSISTENT", "UNSUPPORTED"}


def to_argv(inputs: dict) -> list[str]:
    """Sözleşme girdi sözlüğü → `--alan değer` argümanları (test ve mode dahil, girdi sırasıyla)."""
    argv = []
    for k, v in inputs.items():
        argv += [f"--{k}", v if isinstance(v, str) else json.dumps(v)]
    return argv


def run_cli(argv: list[str]) -> tuple[int, str, str, float]:
    t = time.perf_counter()
    p = subprocess.run([sys.executable, "-m", "gpower_clone"] + argv, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr, time.perf_counter() - t


def close(got: float, want: float, tol: float = 1e-6) -> bool:
    """§0.6: |fark| ≤ 1e-6 ya da göreli fark ≤ 1e-6."""
    return abs(got - want) <= tol or abs(got - want) <= tol * abs(want)

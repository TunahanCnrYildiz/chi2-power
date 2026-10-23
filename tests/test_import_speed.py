"""Soğuk başlangıç (§0.1, 2 s): motor scipy.stats yerine scipy.special kullanır; sayılar değişmez.

scipy.stats yalnızca bu testte, karşılaştırma için içe aktarılır.
"""

import subprocess
import sys

import pytest
from scipy.stats import chi2, ncx2

from gpower_clone import engine


def test_engine_does_not_import_scipy_stats():
    code = "import sys, gpower_clone.cli, gpower_clone.service; print('scipy.stats' in sys.modules)"
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert p.stdout.strip() == "False", p.stdout + p.stderr


@pytest.mark.parametrize("df", [1.0, 2.0, 2.5, 5.0, 30.0, 100.0])
def test_distribution_functions_identical_to_scipy_stats(df):
    for a in (1e-7, 0.001, 0.01, 0.05, 0.1, 0.5, 0.9999999):
        assert engine.critical_value(a, df) == chi2.isf(a, df)
    for x in (0.0, 0.5, 3.84, 11.07, 149.4, 400.0):
        for lam in (0.0, 0.09, 9.0, 19.78, 1000.0):
            want = float(chi2.cdf(x, df)) if lam < 1e-100 else float(ncx2.cdf(x, df, lam))
            if x <= 0:
                want = 0.0
            assert engine.ncx2_cdf(x, df, lam) == want
        assert engine._alpha_of(x, df) == float(chi2.sf(x, df))

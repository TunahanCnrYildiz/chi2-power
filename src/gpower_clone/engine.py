"""χ² olumsallık tablosu güç analizi motoru — hesap mantığının tek yeri.

SPEC §2 (doğrulama), §4 (hesap kuralları). Dağılım fonksiyonları scipy'den
gelir (SPEC §4.4 izin veriyor); N araması, aralık kurma, kök bulma ve
yuvarlama SPEC §4.5'te yazıldığı gibi burada uygulanır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from scipy.stats import chi2, ncx2

EPS = 2.220446049250313e-16  # makine epsilonu (double)

ALPHA_MIN, ALPHA_MAX = 1e-7, 0.9999999
POWER_MIN, POWER_MAX = 1e-7, 0.9999999
W_MIN_A_PRIORI = 1e-6
N_MIN, N_MAX = 1, 2147483646

BRENT_TOL = 1e-10
BRENT_MAXITER = 300

MSG_DF = "Degrees of Freedom must be greater or equal one."
MSG_POWER_LT_ALPHA = "Power must be greater than or equal to alpha."
MSG_ALPHA_RANGE = "Alpha is outside the admissible range (1e-07, 1)."
MSG_POWER_RANGE = "Power is outside the admissible range (1e-07, 1)."
MSG_N_RANGE = "Total sample size is outside the admissible range (1, 2147483646)"
MSG_W_A_PRIORI = "Effect size w must be greater 1e-06."
MSG_W_POST_HOC = "Effect size w must be non-negative."
# Tasarım kararları (SPEC'te mesaj yok):
MSG_N_INTEGER = "Total sample size must be an integer."  # A-3
MSG_NO_ROOT = "Unable to find a total sample size for the given parameters."


class InputError(ValueError):
    """Geçersiz girdi; mesaj G*Power'ın mesajıyla birebir aynıdır (SPEC §2.2)."""


class RootNotFound(ArithmeticError):
    """Kök bulucu uç noktalarda aynı işaret gördü ya da yakınsamadı (SPEC §4.5/3)."""


@dataclass(frozen=True)
class Result:
    n_total: int
    actual_power: float
    critical: float
    df: float
    ncp: float


# ---------- Dağılımlar (SPEC §4.2 – §4.4) ----------

def ncx2_cdf(x: float, df: float, lam: float) -> float:
    """Merkezi olmayan χ² CDF'i; λ < 1e-100 için merkezi χ² CDF'i."""
    if x <= 0:
        return 0.0
    if math.isinf(x):
        return 1.0
    if lam < 1e-100:
        return float(chi2.cdf(x, df))
    return float(ncx2.cdf(x, df, lam))


def critical_value(alpha: float, df: float) -> float:
    """Merkezi χ²(df) dağılımının (1 − α) quantile'ı."""
    # isf(α) = ppf(1 − α); isf küçük α'da 1 − α'nın yuvarlama kaybını önler.
    return float(chi2.isf(alpha, df))


def power_at(w: float, n: float, critical: float, df: float) -> float:
    """güç = 1 − F(critical; df, λ = w²·N). N kesirli olabilir."""
    return 1.0 - ncx2_cdf(critical, df, w * w * n)


# ---------- N araması (SPEC §4.5) ----------

def find_bracket(f: Callable[[float], float], a: float = 1.0, start: float = 100.0) -> tuple[float, float]:
    """SPEC §4.5/2: kök için [alt, üst] arama aralığı."""
    if f(start) < 0:
        lo, hi = start, start * 1.6
        while f(hi) < 0:
            lo, hi = hi, hi * 1.6
            if math.isinf(hi):
                raise RootNotFound("upper bound overflow")
    else:
        hi = start
        x = (a + start) * 0.5
        while x >= a and f(x) > 0:
            hi = x
            x = (x + a) * 0.5 - a
        lo = x
    if lo < 1:
        lo = 1.0
    return lo, hi


def brent(f: Callable[[float], float], a: float, b: float,
          tol: float = BRENT_TOL, maxiter: int = BRENT_MAXITER) -> float:
    """Brent kök bulucu (ikiye bölme + ters kuadratik / sekant), SPEC §4.5/3."""
    fa, fb = f(a), f(b)
    if fa == 0:
        return a
    if fb == 0:
        return b
    if (fa > 0) == (fb > 0):
        raise RootNotFound("f has the same sign at both ends")
    c, fc = b, fb
    d = e = b - a
    for _ in range(maxiter):
        if (fb > 0) == (fc > 0):
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb
        tol1 = 2.0 * EPS * abs(b) + 0.5 * tol
        xm = 0.5 * (c - b)
        if abs(xm) <= tol1 or fb == 0:
            return b
        if abs(e) >= tol1 and abs(fa) > abs(fb):
            s = fb / fa
            if a == c:  # sekant
                p = 2.0 * xm * s
                q = 1.0 - s
            else:  # ters kuadratik interpolasyon
                q = fa / fc
                r = fb / fc
                p = s * (2.0 * xm * q * (q - r) - (b - a) * (r - 1.0))
                q = (q - 1.0) * (r - 1.0) * (s - 1.0)
            if p > 0:
                q = -q
            p = abs(p)
            if 2.0 * p < min(3.0 * xm * q - abs(tol1 * q), abs(e * q)):
                e, d = d, p / q
            else:  # ikiye bölme
                d = e = xm
        else:
            d = e = xm
        a, fa = b, fb
        b += d if abs(d) > tol1 else math.copysign(tol1, xm)
        fb = f(b)
    raise RootNotFound("maximum number of iterations exceeded")


def round_n(n: float) -> int:
    """SPEC §4.5/4–5: önce 10 ondalığa yuvarla, sonra yukarı yuvarla; en az 1."""
    n10 = math.floor(n * 1e10 + 0.5) / 1e10
    return max(N_MIN, math.ceil(n10))


# ---------- Doğrulama (SPEC §2.1, §2.2) ----------
# Karşılaştırmalar `not (...)` biçiminde yazılır: NaN her kontrolde başarısız olur.

def _check_df(df: float) -> None:
    if not df >= 1:
        raise InputError(MSG_DF)


def _check_alpha(alpha: float) -> None:
    if not ALPHA_MIN <= alpha <= ALPHA_MAX:
        raise InputError(MSG_ALPHA_RANGE)


# ---------- Modlar ----------

def a_priori(w: float, alpha: float, power: float, df: float) -> Result:
    """Hedef güce ulaşmak için gereken toplam N."""
    _check_df(df)
    if not w >= W_MIN_A_PRIORI:
        raise InputError(MSG_W_A_PRIORI)
    _check_alpha(alpha)
    if not POWER_MIN <= power <= POWER_MAX:
        raise InputError(MSG_POWER_RANGE)
    if power < alpha:
        raise InputError(MSG_POWER_LT_ALPHA)

    crit = critical_value(alpha, df)

    def f(n: float) -> float:
        return power_at(w, n, crit, df) - power

    try:
        lo, hi = find_bracket(f)
    except RootNotFound:
        raise InputError(MSG_NO_ROOT) from None
    try:
        n_frac = brent(f, lo, hi)
    except RootNotFound:
        # Tasarım kararı: alt uçta (N = 1) güç hedefe zaten ulaşıyorsa
        # (ör. güç = α, G-007) aralıkta işaret değişimi yoktur; en küçük
        # N alt uçtur. Aksi hâlde hata.
        if f(lo) >= 0:
            n_frac = lo
        else:
            raise InputError(MSG_NO_ROOT) from None

    n_total = round_n(n_frac)
    ncp = w * w * n_total
    return Result(
        n_total=n_total,
        actual_power=1.0 - ncx2_cdf(crit, df, ncp),
        critical=crit,
        df=df,
        ncp=ncp,
    )


def post_hoc(w: float, alpha: float, n: float, df: float) -> Result:
    """Verilen toplam N için güç."""
    _check_df(df)
    if not w >= 0:
        raise InputError(MSG_W_POST_HOC)
    _check_alpha(alpha)
    if not N_MIN <= n <= N_MAX:
        raise InputError(MSG_N_RANGE)
    if n != math.floor(n):
        raise InputError(MSG_N_INTEGER)
    n_total = int(n)

    crit = critical_value(alpha, df)
    ncp = w * w * n_total
    return Result(
        n_total=n_total,
        actual_power=1.0 - ncx2_cdf(crit, df, ncp),
        critical=crit,
        df=df,
        ncp=ncp,
    )

"""Motorun SPEC §4.5 adımlarına dair birim testleri."""

import pytest

from gpower_clone import engine


def test_shrink_branch_x_sequence():
    """§4.5/2, f(100) ≥ 0 dalı: a = 1 için x dizisi 50.5, 24.75, 11.875, 5.4375, 2.21875, 0.609…"""
    seen = []

    def f(x):
        seen.append(x)
        return 1.0  # her yerde pozitif: döngü x < a olana dek sürer

    lo, hi = engine.find_bracket(f)
    assert seen == [100, 50.5, 24.75, 11.875, 5.4375, 2.21875]
    # döngü x = 0.609375 ile biter; alt < 1 olduğundan alt ← 1
    assert (lo, hi) == (1.0, 2.21875)


def test_shrink_branch_stops_when_f_not_positive():
    lo, hi = engine.find_bracket(lambda x: x - 20.0)
    # 100 → 50.5 → 24.75 (f>0) → 11.875 (f≤0): alt = 11.875, üst = 24.75
    assert (lo, hi) == (11.875, 24.75)


def test_shrink_branch_f_zero_at_x_ends_loop():
    """f(x) > 0 koşulu katıdır: f(x) = 0 döngüyü bitirir."""
    lo, hi = engine.find_bracket(lambda x: x - 50.5)
    assert (lo, hi) == (50.5, 100)


def test_expand_branch():
    """§4.5/2, f(100) < 0 dalı: üst 160'tan başlayıp 1.6 katına çıkar."""
    lo, hi = engine.find_bracket(lambda x: x - 500.0)
    # 160 → 256 → 409.6 → 655.36
    assert lo == pytest.approx(409.6)
    assert hi == pytest.approx(655.36)


def test_brent_finds_root():
    root = engine.brent(lambda x: x * x - 2.0, 1.0, 2.0)
    assert root == pytest.approx(2 ** 0.5, abs=1e-10)


def test_brent_same_sign_raises():
    with pytest.raises(engine.RootNotFound):
        engine.brent(lambda x: x * x + 1.0, 1.0, 2.0)


def test_rounding_boundary():
    # kesirli kısmı 5e-11'den küçük → aşağı; büyük → yukarı
    assert engine.round_n(104.00000000004) == 104
    assert engine.round_n(104.00000000006) == 105
    assert engine.round_n(104.0) == 104


def test_round_n_huge():
    assert engine.round_n(7848860500000.3) == 7848860500001


def test_noncentral_cdf_special_cases():
    assert engine.ncx2_cdf(0.0, 1.0, 5.0) == 0.0
    assert engine.ncx2_cdf(-1.0, 1.0, 5.0) == 0.0
    assert engine.ncx2_cdf(float("inf"), 1.0, 5.0) == 1.0


def test_power_w_zero_equals_alpha():
    r = engine.post_hoc(w=0.0, alpha=0.05, n=100, df=1.0)
    assert r.actual_power == pytest.approx(0.05, abs=1e-12)
    assert r.ncp == 0.0


def test_large_n_has_no_upper_limit():
    r = engine.a_priori(w=1e-6, alpha=0.05, power=0.8, df=1.0)
    assert r.n_total > 2147483646
    assert isinstance(r.n_total, int)


@pytest.mark.parametrize(
    "kwargs,message",
    [
        (dict(w=0.3, alpha=0.05, power=0.8, df=0.999), "Degrees of Freedom must be greater or equal one."),
        (dict(w=0.3, alpha=1e-7, power=0.8, df=1.0), None),
        (dict(w=0.3, alpha=0.9999999, power=0.9999999, df=1.0), None),
        (dict(w=0.3, alpha=0.99999999, power=0.9999999, df=1.0), "Alpha is outside the admissible range (1e-07, 1)."),
        (dict(w=0.3, alpha=0.05, power=1e-8, df=1.0), "Power is outside the admissible range (1e-07, 1)."),
        (dict(w=1e-6, alpha=0.05, power=0.8, df=1.0), None),
    ],
)
def test_a_priori_validation(kwargs, message):
    if message is None:
        engine.a_priori(**kwargs)
    else:
        with pytest.raises(engine.InputError) as e:
            engine.a_priori(**kwargs)
        assert str(e.value) == message


def test_post_hoc_validation_order():
    # df → w → α → N
    with pytest.raises(engine.InputError) as e:
        engine.post_hoc(w=-1.0, alpha=2.0, n=0, df=0.5)
    assert str(e.value) == "Degrees of Freedom must be greater or equal one."
    with pytest.raises(engine.InputError) as e:
        engine.post_hoc(w=-1.0, alpha=2.0, n=0, df=1.0)
    assert str(e.value) == "Effect size w must be non-negative."
    with pytest.raises(engine.InputError) as e:
        engine.post_hoc(w=0.1, alpha=2.0, n=0, df=1.0)
    assert str(e.value) == "Alpha is outside the admissible range (1e-07, 1)."


def test_post_hoc_n_upper_limit():
    engine.post_hoc(w=0.1, alpha=0.05, n=2147483646, df=1.0)
    with pytest.raises(engine.InputError) as e:
        engine.post_hoc(w=0.1, alpha=0.05, n=2147483647, df=1.0)
    assert str(e.value) == "Total sample size is outside the admissible range (1, 2147483646)"

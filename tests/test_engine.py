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


def test_brent_same_sign_returns_zero():
    """SPEC v1.2 §4.5/3: uçlarda f aynı işaretliyse hata yok, 0 döner."""
    assert engine.brent(lambda x: x * x + 1.0, 1.0, 2.0) == 0.0
    assert engine.brent(lambda x: -1.0, 1.0, 2.0) == 0.0


def test_brent_maxiter_returns_last_estimate():
    """SPEC v1.2 §4.5/3: 300 iterasyon dolarsa hata yok, son tahmin (b) döner."""
    calls = []

    def f(x):
        calls.append(x)
        return -1.0 if x < 1.234567890123 else 1.0

    b = engine.brent(f, 1.0, 2.0, maxiter=3)
    assert 1.0 <= b <= 2.0
    assert b == calls[-1]  # son değerlendirilen tahmin


def test_brent_relative_stopping_criterion():
    """SPEC v1.2 §4.5/3: |yarım aralık| ≤ 1.1102230246251565e-16·|b| ya da f(b) = 0.

    Basamak fonksiyonunda yalnızca ikiye bölme çalışır; eski mutlak 0.5·1e-10
    toleransı ~5e-11 hatayla dururdu, yeni ölçüt makine hassasiyetine iner.
    """
    c = 1.234567890123

    def step(x):
        return -1.0 if x < c else 1.0

    b = engine.brent(step, 1.0, 2.0)
    assert abs(b - c) <= 4 * 2.220446049250313e-16 * c
    assert engine.BRENT_REL_TOL == 1.1102230246251565e-16


def test_g007_root_finder_returns_zero():
    """S-1: güç = α → aralık [1, 2.21875], uçlar aynı işaretli → kök bulucu 0 → n_total = alt = 1."""
    assert engine.fractional_n(w=0.3, alpha=0.05, power=0.05, df=1.0) == 0.0
    assert engine.a_priori(w=0.3, alpha=0.05, power=0.05, df=1.0).n_total == 1


def test_lower_bound_rule_uses_bracket_lower(monkeypatch):
    """SPEC v1.2 §4.5/5: n_total < alt ise n_total = alt ve yeniden yuvarlanır."""
    monkeypatch.setattr(engine, "find_bracket", lambda f: (11.875, 24.75))
    monkeypatch.setattr(engine, "brent", lambda f, a, b, **kw: 3.2)
    assert engine.a_priori(w=0.3, alpha=0.05, power=0.8, df=1.0).n_total == 12


def test_a_priori_has_no_root_finder_error(monkeypatch):
    """S-1: a priori yolda kök bulucudan kaynaklanan hata mesajı yok."""
    assert not hasattr(engine, "MSG_NO_ROOT")
    monkeypatch.setattr(engine, "brent", lambda f, a, b, **kw: 0.0)
    # Bu girdide aralık [50.5, 100]; kök bulucu 0 dönse de §4.5/5 n_total = ⌈50.5⌉ = 51 yapar.
    assert engine.a_priori(w=0.3, alpha=0.05, power=0.8, df=1.0).n_total == 51


def test_rounding_boundary():
    # kesirli kısmı 5e-11'den küçük → aşağı; büyük → yukarı
    assert engine.round_n(104.00000000004) == 104
    assert engine.round_n(104.00000000006) == 105
    assert engine.round_n(104.0) == 104
    assert engine.round_n(0.0) == 0  # alt sınır kuralı round_n'de değil, §4.5/5'te


def test_round_n_huge():
    assert engine.round_n(7848860500000.3) == 7848860500001


def test_noncentral_cdf_special_cases():
    assert engine.ncx2_cdf(0.0, 1.0, 5.0) == 0.0
    assert engine.ncx2_cdf(-1.0, 1.0, 5.0) == 0.0
    assert engine.ncx2_cdf(float("inf"), 1.0, 5.0) == 1.0


def test_power_w_zero_equals_alpha():
    """G*Power davranışı (contract=False): w = 0 → güç = α (G-023)."""
    r = engine.post_hoc(w=0.0, alpha=0.05, n=100, df=1.0, contract=False)
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


# ---------- Tablo boyutundan df (ajan katmanı için) ----------

@pytest.mark.parametrize("rows,cols,df", [(2, 2, 1.0), (3, 3, 4.0), (2, 3, 2.0), (4, 3, 6.0), (2.0, 5.0, 4.0)])
def test_df_from_table(rows, cols, df):
    assert engine.df_from_table(rows, cols) == df


@pytest.mark.parametrize("rows,cols,message", [
    (1, 3, "Number of rows must be an integer greater or equal two."),
    (2.5, 3, "Number of rows must be an integer greater or equal two."),
    (3, 1, "Number of columns must be an integer greater or equal two."),
    (3, 0.5, "Number of columns must be an integer greater or equal two."),
    (float("nan"), 3, "Number of rows must be an integer greater or equal two."),
])
def test_df_from_table_invalid(rows, cols, message):
    with pytest.raises(engine.InputError) as e:
        engine.df_from_table(rows, cols)
    assert str(e.value) == message



# ---------- Sözleşme (SPEC §0.4 – §0.5): kod ve alan ----------

@pytest.mark.parametrize("fn,kwargs,code,field", [
    ("a_priori", dict(w=0.3, alpha=0.05, power=0.8, df=0.0), "OUT_OF_RANGE", "df"),
    ("a_priori", dict(w=0.3, alpha=0.05, power=0.8, df=2.5), "INVALID_VALUE", "df"),
    ("a_priori", dict(w=0.0, alpha=0.05, power=0.8, df=1.0), "OUT_OF_RANGE", "w"),
    ("a_priori", dict(w=0.3, alpha=0.0, power=0.8, df=1.0), "OUT_OF_RANGE", "alpha"),
    ("a_priori", dict(w=0.3, alpha=0.05, power=1.0, df=1.0), "OUT_OF_RANGE", "power"),
    ("a_priori", dict(w=0.3, alpha=0.05, power=0.04, df=1.0), "INCONSISTENT", "power"),
    ("post_hoc", dict(w=0.0, alpha=0.05, n=100, df=1.0), "OUT_OF_RANGE", "w"),
    ("post_hoc", dict(w=-0.1, alpha=0.05, n=100, df=1.0), "OUT_OF_RANGE", "w"),
    ("post_hoc", dict(w=0.3, alpha=0.05, n=1, df=1.0), "OUT_OF_RANGE", "n_total"),
    ("post_hoc", dict(w=0.3, alpha=0.05, n=0, df=1.0), "OUT_OF_RANGE", "n_total"),
    ("post_hoc", dict(w=0.3, alpha=0.05, n=100.5, df=1.0), "INVALID_VALUE", "n_total"),
])
def test_contract_error_codes(fn, kwargs, code, field):
    with pytest.raises(engine.InputError) as e:
        getattr(engine, fn)(**kwargs)
    assert (e.value.code, e.value.field) == (code, field)


def test_gpower_mode_keeps_gpower_ranges():
    """contract=False: G-019 (kesirli df), G-023 (w = 0), G-025 (N = 1) G*Power gibi kabul edilir."""
    assert engine.a_priori(w=0.3, alpha=0.05, power=0.8, df=2.5, contract=False).n_total == 115
    assert engine.post_hoc(w=0.0, alpha=0.05, n=100, df=1.0, contract=False).ncp == 0.0
    assert engine.post_hoc(w=0.3, alpha=0.05, n=1, df=1.0, contract=False).n_total == 1


@pytest.mark.parametrize("rows,cols,code,field", [
    (1, 3, "OUT_OF_RANGE", "rows"), (2.5, 3, "INVALID_VALUE", "rows"),
    (3, 1, "OUT_OF_RANGE", "cols"), (3, 0.5, "INVALID_VALUE", "cols"),
])
def test_df_from_table_codes(rows, cols, code, field):
    with pytest.raises(engine.InputError) as e:
        engine.df_from_table(rows, cols)
    assert (e.value.code, e.value.field) == (code, field)

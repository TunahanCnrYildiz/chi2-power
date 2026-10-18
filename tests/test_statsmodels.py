"""statsmodels ızgarası (594 a priori + 300 post hoc) üzerinde regresyon testi.

SPEC v1.2 §4.5/3 durma ölçütü değişikliğinin hiçbir vektörü bozmadığını gösterir:
her a priori vektörde n_total = ⌈N_sm⌉ ve minimal; post hoc güç 7 ondalıkta eşit.
"""

import pytest

pytest.importorskip("statsmodels")

import statsmodels_vectors as sv  # noqa: E402


def test_statsmodels_grid_a_priori():
    rows = list(sv.a_priori_rows())
    assert len(rows) == 594
    assert [r for r in rows if r["status"] != "ceil-eşleşme"] == []
    for r in rows:
        assert r["power_sm_at_n"] >= r["power"] - 1e-12
        assert r["power_sm_at_n_minus_1"] is None or r["power_sm_at_n_minus_1"] < r["power"]


def test_statsmodels_grid_post_hoc():
    rows = list(sv.post_hoc_rows())
    assert len(rows) == 300
    assert [r for r in rows if r["status"] != "eşleşme-7"] == []

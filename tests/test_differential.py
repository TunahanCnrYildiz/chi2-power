"""Diferansiyel düzeneğin kendisinin testi ve (varsa) kâhin CSV'si üzerinde KAPI."""

from pathlib import Path

import pytest

import differential

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "spec_vectors.csv"
ORACLE = HERE.parent / "oracle" / "vectors.csv"


def test_harness_on_spec_vectors():
    results = differential.run_csv(FIXTURE, differential.default_cmd())
    assert len(results) == 30
    g = differential.gate(results)
    # a priori n_total vektörleri: 15, G-019 sözleşme gereği hariç → 14 (G-013 doğrulanamayan)
    assert g["n_vectors"] == 14 and g["exact"] == 13 and g["unverifiable"] == 1
    bad = [(r.vid, [c for c in r.checks if not c.ok]) for r in results if not r.ok]
    assert bad == []
    assert sorted(r.vid for r in results if r.kind == "contract") == ["G-019", "G-023", "G-025"]
    assert max(r.seconds for r in results) < 2.0  # §0.1
    report, passed = differential.build_report(results, FIXTURE, 0.90)
    assert passed and "GEÇTİ" in report and "Sözleşme gereği G*Power'dan farklı" in report


def test_harness_detects_mismatch(tmp_path):
    csv = tmp_path / "v.csv"
    csv.write_text(
        "id,source,mode,w,alpha,power,n_total_in,df,ncp,critical,df_out,n_total,actual_power,screenshot,notes\n"
        "X-1,t,a-priori,0.3,0.05,0.95,,1,13.0500000,3.8414588,1,146,0.9507851,,\n"
        'X-2,t,a-priori,0.3,0.05,0.80,,0,,,,,,,"Wrong message."\n'
        'X-3,t,a-priori,0.3,0.05,0.80,,0,,,,,,,"G-008 kopyası: ""Degrees of Freedom must be greater or equal one."""\n',
        encoding="utf-8",
    )
    results = differential.run_csv(csv, differential.default_cmd())
    assert [r.ok for r in results] == [False, False, True]
    assert results[0].n_status == "mismatch"
    _, passed = differential.build_report(results, csv, 0.90)
    assert not passed


def test_report_paths_under_tests():
    """Uyum raporları tests/reports/ altında üretilir."""
    import statsmodels_vectors

    assert differential.DEFAULT_REPORT == HERE / "reports" / "differential_report.md"
    assert statsmodels_vectors.DEFAULT_OUT == HERE / "reports"


@pytest.mark.skipif(not ORACLE.exists(), reason="oracle/vectors.csv henüz yok")
def test_oracle_gate():
    results = differential.run_csv(ORACLE, differential.default_cmd())
    _, passed = differential.build_report(results, ORACLE, 0.90)
    assert passed

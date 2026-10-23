"""MCP sunucusu (SPEC §0.8): tek araç `power_analysis`, CLI ile birebir aynı çıktı.

(a) Araç süreç içinde çağrılır; 25 açık referans vektörü ve 30 SPEC vektörünün her birinde metin içeriği,
    CLI'nin stdout satırıyla birebir aynıdır (hatalar dahil); isError, CLI çıkış kodu ≠ 0 ile eşleşir.
(b) Sunucu stdio üzerinden gerçek bir MCP istemcisiyle başlatılır.
(c) MCP modülü hesap ve ayrıştırma kodu içermez; ortak katmanı (service) çağırır.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

anyio = pytest.importorskip("anyio")
pytest.importorskip("mcp")

from mcp import Client, StdioServerParameters  # noqa: E402

import differential  # noqa: E402
from contract_util import PUBLIC, to_argv  # noqa: E402

HERE = Path(__file__).resolve().parent
TOOL = "power_analysis"

with open(HERE / "fixtures" / "spec_vectors.csv", newline="", encoding="utf-8") as fh:
    ROWS = list(csv.DictReader(fh))


def _num(text: str):
    return int(text) if text.lstrip("-").isdigit() else float(text)


def spec_args(row: dict) -> dict:
    """CSV satırı → MCP argümanları (JSON sayıları)."""
    args = {"test": "chi2-contingency", "mode": row["mode"]}
    for col, name in (("w", "w"), ("alpha", "alpha"), ("power", "power"), ("n_total_in", "n_total"), ("df", "df")):
        if row[col]:
            args[name] = _num(row[col])
    return args


def cli(argv: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-m", "gpower_clone"] + argv, capture_output=True, text=True)
    assert p.stdout.count("\n") == 1
    return p.returncode, p.stdout.rstrip("\n")


def call(args: dict):
    from gpower_clone.mcp_server import server

    async def go():
        async with Client(server) as c:
            return await c.call_tool(TOOL, args)

    return anyio.run(go)


def assert_same(result, code: int, line: str):
    assert len(result.content) == 1
    assert result.content[0].text == line  # birebir aynı metin
    assert result.structured_content == json.loads(line)
    assert result.is_error == (code != 0)


@pytest.mark.parametrize("vec", PUBLIC, ids=[v["id"] for v in PUBLIC])
def test_public_vectors_match_cli(vec):
    code, line = cli(to_argv(vec["input"]))
    assert_same(call(vec["input"]), code, line)
    if not vec["id"].startswith("chi2-contingency/"):
        assert json.loads(line)["code"] == "UNSUPPORTED"


@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_spec_vectors_match_cli(row):
    code, line = cli(differential.build_argv(row))
    assert_same(call(spec_args(row)), code, line)


EXTRA = [
    {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.8, "rows": 3, "cols": 3},
    {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.25, "alpha": 0.05, "n_total": 200, "rows": 4, "cols": 3},
    {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3, "alpha": 0.05, "n_total": 100, "rows": 2, "cols": 2,
     "df": 4},
    {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3, "alpha": 0.05, "n_total": 100, "rows": 3},
    {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3, "alpha": 0.05, "n_total": 100, "df": 1, "power": 0.8},
    {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3, "alpha": 0.05, "n_total": 100, "df": 1, "tails": 2},
    {"test": "chi2-contingency", "mode": "a-priori", "w": "abc", "alpha": 0.05, "power": 0.8, "df": 1},
    {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.8, "df": 2.5},
    {"test": "chi2-contingency", "mode": "posthoc", "w": 0.3},
    {"mode": "a-priori", "w": 0.3},
    {"test": "chi2-contingency"},
    {"test": "chi2-contingency", "mode": "compromise", "w": 0.3, "beta_alpha_ratio": 2, "rows": 3, "cols": 3,
     "n_total": 150},
    {"test": "chi2-contingency", "mode": "compromise", "w": 0.3, "beta_alpha_ratio": 0, "n_total": 100, "df": 5},
    {"test": "chi2-contingency", "mode": "criterion", "w": 0.3, "power": 0.95, "n_total": 100, "df": 5,
     "alpha": 0.05},
    {"test": "chi2-contingency", "mode": "sensitivity", "alpha": 0.05, "power": 0.04, "n_total": 100, "df": 5},
]


@pytest.mark.parametrize("args", EXTRA, ids=[f"extra-{i}" for i in range(len(EXTRA))])
def test_extra_cases_match_cli(args):
    code, line = cli(to_argv(args))
    assert_same(call(args), code, line)


# ---------- (b) uçtan uca: stdio ----------

def test_stdio_end_to_end():
    params = StdioServerParameters(command=sys.executable, args=["-m", "gpower_clone.mcp_server"])
    vecs = [v for v in PUBLIC if v["id"] in ("chi2-contingency/a-priori", "chi2-contingency/post-hoc",
                                              "t2-indep/a-priori")]
    vecs.append({"id": "error", "input": {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3,
                                          "alpha": 0.05, "n_total": 0, "df": 1}})

    async def go():
        async with Client(params) as c:
            tools = (await c.list_tools()).tools
            results = [await c.call_tool(TOOL, v["input"]) for v in vecs]
            return tools, results

    tools, results = anyio.run(go)
    assert [t.name for t in tools] == [TOOL]
    schema = tools[0].input_schema
    assert {"test", "mode", "w", "alpha", "power", "n_total", "df", "rows", "cols",
            "beta_alpha_ratio"} == set(schema["properties"])
    assert schema["properties"]["mode"]["enum"] == ["a-priori", "post-hoc", "compromise", "criterion", "sensitivity"]
    assert set(schema["required"]) == {"test", "mode"}
    assert all(p.get("description") for p in schema["properties"].values())
    for v, r in zip(vecs, results):
        code, line = cli(to_argv(v["input"]))
        assert_same(r, code, line)


# ---------- (c) ince adaptör ----------

def test_mcp_module_is_thin_adapter():
    import gpower_clone.mcp_server as m
    from gpower_clone import engine, service

    src = Path(m.__file__).read_text(encoding="utf-8")
    for banned in ("scipy", "chi2.", "ncx2", "import math", "from .engine", "import engine",
                   "critical_value", "power_at", "round_n", "brent", "float(", "int("):
        assert banned not in src, banned
    assert "from . import service" in src
    assert m.service is service
    assert service.engine is engine


def test_cli_uses_service():
    from gpower_clone import cli as cli_mod, service

    src = Path(cli_mod.__file__).read_text(encoding="utf-8")
    assert cli_mod.service is service
    assert "import engine" not in src and "from .engine" not in src
    assert not hasattr(cli_mod, "engine")

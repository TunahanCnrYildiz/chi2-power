"""MCP sunucusu (bonus katman): CLI ile birebir aynı çıktı, şema, ince adaptör.

(a) Araç süreç içinde çağrılır; spec_vectors.csv'deki tüm vektörlerde sonuç,
    CLI'nin alt süreç çıktısıyla ayrıştırılmış JSON üzerinde birebir karşılaştırılır.
(b) Sunucu stdio üzerinden gerçek bir MCP istemcisiyle başlatılır.
(c) MCP modülü hesap kodu içermez; motoru ortak katman (service) üzerinden çağırır.
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

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "spec_vectors.csv"
TOOL = "chi2_contingency_power"
FIELDS = ["n_total", "actual_power", "critical", "df", "ncp"]

with open(FIXTURE, newline="", encoding="utf-8") as fh:
    ROWS = list(csv.DictReader(fh))


def tool_args(row: dict) -> dict:
    """CSV satırı → MCP araç argümanları (JSON sayıları)."""
    args = {"mode": row["mode"], "w": float(row["w"]), "alpha": float(row["alpha"]),
            "df": float(row["df"])}
    if row["power"]:
        args["power"] = float(row["power"])
    if row["n_total_in"]:
        args["n"] = int(row["n_total_in"])
    return args


def cli_output(row: dict) -> tuple[int, dict]:
    p = subprocess.run([sys.executable, "-m", "gpower_clone"] + differential.build_argv(row),
                       capture_output=True, text=True)
    assert p.stdout.count("\n") == 1
    return p.returncode, json.loads(p.stdout)


def assert_same(result, code: int, cli: dict):
    """MCP sonucu ile CLI çıktısı birebir aynı mı? (tolerans yok)"""
    assert len(result.content) == 1
    text = json.loads(result.content[0].text)
    assert text == cli
    assert result.structured_content == cli
    assert result.is_error == (code != 0)
    if code == 0:
        assert list(result.structured_content) == FIELDS


# ---------- (a) süreç içi: tüm SPEC vektörleri ----------

@pytest.mark.parametrize("row", ROWS, ids=[r["id"] for r in ROWS])
def test_in_process_matches_cli(row):
    from gpower_clone.mcp_server import server

    async def go():
        async with Client(server) as c:
            return await c.call_tool(TOOL, tool_args(row))

    result = anyio.run(go)
    code, cli = cli_output(row)
    assert_same(result, code, cli)


def test_in_process_missing_parameter_is_error():
    from gpower_clone.mcp_server import server

    async def go():
        async with Client(server) as c:
            return await c.call_tool(TOOL, {"mode": "a-priori", "w": 0.3, "alpha": 0.05, "df": 1})

    r = anyio.run(go)
    assert r.is_error
    assert r.structured_content == {"error": "Missing required parameter: power"}


# ---------- (b) uçtan uca: stdio ----------

E2E_IDS = ["G-001", "G-019", "G-005", "G-023", "G-026", "G-015"]


def test_stdio_end_to_end():
    params = StdioServerParameters(command=sys.executable, args=["-m", "gpower_clone.mcp_server"])
    rows = [r for r in ROWS if r["id"] in E2E_IDS]

    async def go():
        async with Client(params) as c:
            tools = (await c.list_tools()).tools
            results = [await c.call_tool(TOOL, tool_args(r)) for r in rows]
            return tools, results

    tools, results = anyio.run(go)

    assert [t.name for t in tools] == [TOOL]
    tool = tools[0]
    props = tool.input_schema["properties"]
    assert set(props) == {"mode", "w", "alpha", "power", "n", "df"}
    assert set(tool.input_schema["required"]) == {"mode", "w", "alpha", "df"}
    assert props["mode"]["enum"] == ["a-priori", "post-hoc"]
    assert all(props[k].get("description") for k in props)
    assert tool.output_schema is not None
    assert set(tool.output_schema["properties"]) == set(FIELDS)

    for row, result in zip(rows, results):
        code, cli = cli_output(row)
        assert_same(result, code, cli)


# ---------- (c) ince adaptör ----------

def test_mcp_module_is_thin_adapter():
    import gpower_clone.mcp_server as m
    from gpower_clone import engine, service

    src = Path(m.__file__).read_text(encoding="utf-8")
    for banned in ("scipy", "chi2.", "ncx2", "import math", "from .engine", "import engine",
                   "critical_value", "power_at", "round_n", "brent", "float("):
        assert banned not in src, banned
    assert "from . import service" in src
    assert m.service is service
    assert service.engine is engine


def test_cli_uses_service():
    from gpower_clone import cli, service

    src = Path(cli.__file__).read_text(encoding="utf-8")
    assert cli.service is service
    assert "engine." not in src  # CLI motoru yalnızca ortak katman üzerinden çağırır

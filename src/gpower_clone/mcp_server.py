"""gpower-clone MCP sunucusu (stdio) — ortak katman (service) üzerinde ince adaptör.

Tek araç: power_analysis (SPEC §0.8). Alan adları CLI ile aynıdır; çıktı, CLI'nin stdout
JSON satırıyla birebir aynı metindir (hatada aynı hata JSON'u, isError = true).

Ham argümanlar doğrudan ortak katmana verilir (call_tool ezilir). Böylece şemada olmayan bir
alan sessizce atılmaz, CLI'deki gibi UNKNOWN_PARAM olur; tür denetimi de CLI ile aynı koddan geçer.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from . import service

TOOL = "power_analysis"


def _result(arguments: dict[str, Any]) -> CallToolResult:
    result = service.compute(arguments)
    return CallToolResult(
        content=[TextContent(type="text", text=service.to_json(result))],
        structured_content=result,
        is_error=service.is_error(result),
    )


class _Server(MCPServer):
    async def call_tool(self, name, arguments, context=None):
        if name == TOOL:
            return _result(dict(arguments or {}))
        return await super().call_tool(name, arguments, context)


server = _Server(
    name="gpower-clone",
    instructions="Power analysis, G*Power 3.1.9.7 compatible. Supported: chi2-contingency.",
)


@server.tool(
    name=TOOL,
    description=(
        "Power analysis (G*Power compatible), test chi2-contingency. "
        "a-priori: w, alpha, power, df -> ncp, critical_chi2, n_total, actual_power. "
        "post-hoc: w, alpha, n_total, df -> ncp, critical_chi2, power. "
        "compromise: w, beta_alpha_ratio, n_total, df -> ncp, critical_chi2, alpha, beta, power. "
        "criterion: w, power, n_total, df -> ncp, critical_chi2, alpha. "
        "sensitivity: alpha, power, n_total, df -> ncp, critical_chi2, w. "
        "rows+cols may replace df. Other tests return code UNSUPPORTED. "
        "Errors: isError with {\"error\", \"code\", \"field\"}."
    ),
)
def power_analysis(
    test: Annotated[str, Field(description="Test family; only chi2-contingency is supported")],
    mode: Annotated[Literal["a-priori", "post-hoc", "compromise", "criterion", "sensitivity"],
                    Field(description="Which quantity to solve; fields per mode are listed in the tool description")],
    w: Annotated[float | None, Field(description="Effect size w > 0 (a-priori: >= 1e-6)")] = None,
    alpha: Annotated[float | None, Field(description="Alpha, 1e-7..0.9999999")] = None,
    power: Annotated[float | None, Field(description="Target power, 1e-7..0.9999999, >= alpha")] = None,
    n_total: Annotated[int | None, Field(description="Total N, integer 2..2147483646")] = None,
    beta_alpha_ratio: Annotated[float | None, Field(description="compromise only: beta/alpha ratio q > 0")] = None,
    df: Annotated[int | None, Field(description="Degrees of freedom, integer >= 1; or give rows+cols")] = None,
    rows: Annotated[int | None, Field(description="Table rows >= 2 (df computed by the engine)")] = None,
    cols: Annotated[int | None, Field(description="Table columns >= 2")] = None,
) -> CallToolResult:
    # Şema ve belge için kayıtlıdır; çağrılar _Server.call_tool üzerinden ham argümanlarla gelir.
    return _result({k: v for k, v in locals().items() if v is not None})


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()

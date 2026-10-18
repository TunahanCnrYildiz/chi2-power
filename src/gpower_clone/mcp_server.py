"""gpower-clone MCP sunucusu (stdio) — ortak katman (service) üzerinde ince adaptör.

Tek araç: chi2_contingency_power. Çıktı, CLI'nin bastığı JSON ile birebir aynıdır;
hesap ve doğrulama motordadır.
"""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent
from pydantic import Field

from . import service

server = MCPServer(
    name="gpower-clone",
    instructions="Chi-square contingency table power analysis, G*Power 3.1.9.7 compatible.",
)


class PowerResult(TypedDict):
    n_total: Annotated[int, Field(description="Total sample size N")]
    actual_power: Annotated[float, Field(description="Power at n_total")]
    critical: Annotated[float, Field(description="Critical chi-square value")]
    df: Annotated[float, Field(description="Degrees of freedom used")]
    ncp: Annotated[float, Field(description="Noncentrality lambda = w^2 * n_total")]


@server.tool(
    name="chi2_contingency_power",
    description=(
        "Chi-square contingency table power analysis (G*Power compatible). "
        "a-priori: give power, returns required n_total. post-hoc: give n, returns actual_power. "
        "Invalid input returns isError with {\"error\": message}."
    ),
)
def chi2_contingency_power(
    mode: Annotated[Literal["a-priori", "post-hoc"], Field(description="a-priori: solve N; post-hoc: solve power")],
    w: Annotated[float, Field(description="Effect size w; a-priori >= 1e-6, post-hoc >= 0")],
    alpha: Annotated[float, Field(description="Alpha, 1e-7..0.9999999")],
    df: Annotated[float | None, Field(description="Degrees of freedom, >= 1; or give rows+cols")] = None,
    rows: Annotated[int | None, Field(description="Table rows >= 2 (df computed by the engine)")] = None,
    cols: Annotated[int | None, Field(description="Table columns >= 2")] = None,
    power: Annotated[float | None, Field(description="a-priori only: target power, 1e-7..0.9999999, >= alpha")] = None,
    n: Annotated[int | None, Field(description="post-hoc only: total N, 1..2147483646")] = None,
) -> Annotated[CallToolResult, PowerResult]:
    result = service.compute(mode, {"w": w, "alpha": alpha, "power": power, "n": n, "df": df,
                                    "rows": rows, "cols": cols})
    return CallToolResult(
        content=[TextContent(type="text", text=service.to_json(result))],
        structured_content=result,
        is_error=service.is_error(result),
    )


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()

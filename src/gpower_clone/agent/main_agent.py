"""Ana ajan: Türkçe soruyu gpower-clone MCP aracını çağırarak yanıtlar (`claude -p`, Opus).

Ajanın erişebildiği tek araç chi2_contingency_power'dır; yerleşik araçlar (Bash, Read,
Write, web, …) kapalıdır. Böylece sayılar yalnızca motordan gelebilir.
"""

from __future__ import annotations

import json
from typing import Any

from . import claude_cli, prompts

# Takma ad ("opus") CLI sürümüne göre farklı modele çözülebildiği için açık kimlik kullanılır.
MODEL = "claude-opus-5-5"


def mcp_config() -> dict:
    cmd = claude_cli.mcp_server_command()
    return {"mcpServers": {prompts.SERVER_NAME: {"command": cmd[0], "args": cmd[1:]}}}


def build_command(question: str, model: str = MODEL) -> list[str]:
    return [
        "claude", "-p",
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--tools", "",
        "--mcp-config", json.dumps(mcp_config()),
        "--strict-mcp-config",
        "--allowedTools", prompts.TOOL_FQN,
        "--permission-mode", "dontAsk",
        "--system-prompt", prompts.MAIN_SYSTEM_PROMPT,
        *claude_cli.common_flags(),
        question,
    ]


def final_json(text: str) -> dict | None:
    """Cevabın sonundaki makinece okunabilir JSON satırı (label içeren son JSON nesnesi)."""
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip().strip("`").strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "label" in obj:
                return obj
    return None


def answer(question: str, model: str = MODEL, cwd: str | None = None) -> dict[str, Any]:
    """Soruyu ajana sorar; araç çağrıları, son cevap, süre ve token kullanımını döndürür."""
    proc = claude_cli.run(build_command(question, model), cwd=cwd)
    run = claude_cli.parse_stream(proc["stdout"])
    run.update(requested_model=model, question=question, duration_s=proc["wall_s"],
               returncode=proc["returncode"], stderr=proc["stderr"][-2000:],
               final_json=final_json(run["final_text"]))
    return run

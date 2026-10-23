"""Ana ajan: Türkçe soruyu gpower-clone MCP aracını çağırarak yanıtlar (`claude -p`, Opus).

Ajanın erişebildiği tek araç chi2_contingency_power'dır; yerleşik araçlar (Bash, Read,
Write, web, …) kapalıdır. Böylece sayılar yalnızca motordan gelebilir.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from . import claude_cli, prompts

# Takma ad ("opus") CLI sürümüne göre farklı modele çözülebildiği için açık kimlik kullanılır.
MODEL = "claude-opus-5-5"
ROOT = Path(__file__).resolve().parents[3]
CALL_LOG = ROOT / "logs" / "agent_calls.jsonl"  # SPEC §0.8


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


def log_calls(question: str, run: dict, path: Path = CALL_LOG, ts: str | None = None) -> None:
    """Her araç çağrısı için bir satır (SPEC §0.8): {ts, question, tool_input, tool_output, tokens_in, tokens_out}.

    Token'lar o sorunun `claude -p` oturumunun ölçülmüş toplamıdır (tokens_in = girdi + önbellek yazma +
    önbellek okuma, tokens_out = çıktı). stream-json, araç çağrısı başına güvenilir token vermediği için bir
    oturumda birden çok çağrı varsa toplam çağrılara eşit bölünür (artan ilk çağrılara).
    """
    calls = run.get("tool_calls") or []
    if not calls:
        return
    u = run.get("usage") or {}
    t_in = sum(int(u.get(k) or 0) for k in claude_cli.USAGE_KEYS if k != "output_tokens")
    t_out = int(u.get("output_tokens") or 0)
    n = len(calls)
    ts = ts or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for i, c in enumerate(calls):
            rec = {"ts": ts, "question": question, "tool_input": c.get("arguments"), "tool_output": c.get("result"),
                   "tokens_in": t_in // n + (1 if i < t_in % n else 0),
                   "tokens_out": t_out // n + (1 if i < t_out % n else 0)}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def answer(question: str, model: str = MODEL, cwd: str | None = None,
           log_path: Path | None = CALL_LOG) -> dict[str, Any]:
    """Soruyu ajana sorar; araç çağrıları, son cevap, süre ve token kullanımını döndürür.

    log_path verilirse (varsayılan logs/agent_calls.jsonl) her araç çağrısı oraya yazılır.
    """
    proc = claude_cli.run(build_command(question, model), cwd=cwd)
    run = claude_cli.parse_stream(proc["stdout"])
    run.update(requested_model=model, tool=prompts.TOOL_FQN, question=question, duration_s=proc["wall_s"],
               returncode=proc["returncode"], stderr=proc["stderr"][-2000:],
               final_json=final_json(run["final_text"]))
    if log_path is not None:
        log_calls(question, run, log_path)
    return run

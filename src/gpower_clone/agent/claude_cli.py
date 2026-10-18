"""`claude -p` (Claude Code CLI) çalıştırıcısı ve çıktı ayrıştırıcısı.

Kimlik doğrulama kullanıcının Claude Code girişidir (Pro abonelik); API anahtarı kullanılmaz.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")

# Ajanı çağıran Claude Code oturumunun ortamı alt sürece geçmemeli: ör. CLAUDE_CODE_SIMPLE
# alt süreci "bare" kipe sokar, ANTHROPIC_BASE_URL istekleri ana oturumun vekiline yollar.
# ANTHROPIC_API_KEY de kaldırılır: ölçüm aboneliğin girişiyle yapılmalıdır.
_DROP_PREFIXES = ("CLAUDE_CODE_", "CLAUDE_AGENT_SDK_", "CLAUDECODE")
_DROP_KEYS = {"ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
              "CLAUDE_PID", "CLAUDE_EFFORT", "CLAUDE_PREVIEW_CLASSIFIER_FLOOR"}


def child_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items()
            if k not in _DROP_KEYS and not k.startswith(_DROP_PREFIXES)}


def claude_exe() -> str:
    return shutil.which("claude") or "claude"


def mcp_server_command() -> list[str]:
    """MCP sunucusunu bu Python yorumlayıcısıyla başlatan komut."""
    return [sys.executable, "-m", "gpower_clone.mcp_server"]


def common_flags() -> list[str]:
    """Kullanıcı ayarları, hook'lar, eklentiler ve beceriler yüklenmez; oturum kaydedilmez."""
    return ["--setting-sources", "", "--disable-slash-commands", "--no-session-persistence"]


def run(cmd: list[str], cwd: str | Path | None = None, timeout: float = 600) -> dict[str, Any]:
    """Komutu çalıştırır; stdout, stderr, çıkış kodu ve duvar saati süresini döndürür."""
    exe = [claude_exe()] + cmd[1:] if cmd and cmd[0] == "claude" else cmd
    t0 = time.perf_counter()
    p = subprocess.run(exe, capture_output=True, text=True, encoding="utf-8", env=child_env(),
                       cwd=cwd, timeout=timeout, stdin=subprocess.DEVNULL)
    return {"stdout": p.stdout, "stderr": p.stderr, "returncode": p.returncode,
            "wall_s": time.perf_counter() - t0}


def usage_of(result_event: dict) -> dict[str, int]:
    u = result_event.get("usage") or {}
    return {k: int(u.get(k) or 0) for k in USAGE_KEYS}


def _tool_result_payload(block: dict) -> tuple[Any, str]:
    content = block.get("content")
    if isinstance(content, list):
        text = "".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
    else:
        text = content if isinstance(content, str) else json.dumps(content)
    try:
        return json.loads(text), text
    except (json.JSONDecodeError, TypeError):
        return text, text


def parse_stream(stdout: str) -> dict[str, Any]:
    """`--output-format stream-json` çıktısından araç çağrıları, son metin, model ve token kullanımı."""
    run: dict[str, Any] = {"model": None, "init_tools": None, "mcp_servers": None, "tool_calls": [],
                           "final_text": "", "usage": {k: 0 for k in USAGE_KEYS}, "duration_api_s": None,
                           "num_turns": None, "is_error": None, "result_subtype": None,
                           "model_usage": None, "permission_denials": None}
    pending: dict[str, dict] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            run["model"] = ev.get("model")
            run["init_tools"] = ev.get("tools")
            run["mcp_servers"] = ev.get("mcp_servers")
        elif t == "assistant":
            for block in (ev.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_use":
                    call = {"name": block.get("name"), "arguments": block.get("input"),
                            "result": None, "is_error": None}
                    pending[block.get("id")] = call
                    run["tool_calls"].append(call)
        elif t == "user":
            content = (ev.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if block.get("type") == "tool_result" and block.get("tool_use_id") in pending:
                    call = pending[block["tool_use_id"]]
                    call["result"], _ = _tool_result_payload(block)
                    call["is_error"] = bool(block.get("is_error"))
        elif t == "result":
            run["final_text"] = ev.get("result") or ""
            run["usage"] = usage_of(ev)
            if ev.get("duration_ms") is not None:
                run["duration_api_s"] = ev["duration_ms"] / 1000
            run["num_turns"] = ev.get("num_turns")
            run["is_error"] = ev.get("is_error")
            run["result_subtype"] = ev.get("subtype")
            run["model_usage"] = ev.get("modelUsage")
            run["permission_denials"] = ev.get("permission_denials")
    return run

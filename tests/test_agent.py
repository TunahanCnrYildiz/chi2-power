"""AI ajanı katmanı: komut kurulumu, akış ayrıştırma, Sistem 1 yönlendirme, puanlama, rapor.

Gerçek `claude -p` çağrısı yapılmaz; çalıştırıcı sahte (fake) bir fonksiyonla değiştirilir.
Gerçek çalıştırmalar `python -m gpower_clone.agent.evaluate` ile yapılır (NOTES.md).
"""

import json
from pathlib import Path

import pytest

from gpower_clone.agent import claude_cli, gui_compare, main_agent, prompts, scoring, system1

HERE = Path(__file__).resolve().parent
EVAL = json.loads((HERE / "agent" / "eval_set.json").read_text(encoding="utf-8"))
Q = {q["id"]: q for q in EVAL["questions"]}
TOOL = "mcp__gpower-clone__power_analysis"


# ---------- komut kurulumu: yalnızca MCP aracı ----------

def test_main_agent_command_is_locked_down():
    cmd = main_agent.build_command("soru")
    assert cmd[:2] == ["claude", "-p"]
    assert cmd[cmd.index("--model") + 1] == "claude-opus-5-5"
    assert cmd[cmd.index("--tools") + 1] == ""          # bütün yerleşik araçlar kapalı
    assert "--strict-mcp-config" in cmd
    assert cmd[cmd.index("--allowedTools") + 1] == TOOL
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    cfg = json.loads(cmd[cmd.index("--mcp-config") + 1])
    assert list(cfg["mcpServers"]) == ["gpower-clone"]
    assert cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert cmd[cmd.index("--system-prompt") + 1] == prompts.MAIN_SYSTEM_PROMPT
    assert cmd[-1] == "soru"


def test_system1_command_has_no_tools_and_schema():
    cmd = system1.build_command("soru")
    assert cmd[cmd.index("--model") + 1] == "claude-haiku-5-5"
    assert cmd[cmd.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in cmd and "--mcp-config" not in cmd
    schema = json.loads(cmd[cmd.index("--json-schema") + 1])
    assert set(schema["properties"]) == {"label", "confidence"}
    assert schema["additionalProperties"] is False
    assert schema["properties"]["label"]["enum"] == EVAL["labels"]


def test_system_prompt_rules():
    p = prompts.MAIN_SYSTEM_PROMPT
    for needle in ("asla", "0,1", "0,3", "0,5", "rows", "cols", "araştırmacı", "JSON"):
        assert needle in p, needle


def test_child_env_drops_host_session_and_api_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SIMPLE", "1")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "p")
    env = claude_cli.child_env()
    assert "CLAUDE_CODE_SIMPLE" not in env and "ANTHROPIC_BASE_URL" not in env
    assert "ANTHROPIC_API_KEY" not in env and "CLAUDECODE" not in env
    assert env["PATH"] == "p"


# ---------- stream-json ayrıştırma ----------

def _stream(tool_input, tool_result_text, final_text, is_error=False):
    events = [
        {"type": "system", "subtype": "init", "model": "claude-opus-x", "tools": [TOOL],
         "mcp_servers": [{"name": "gpower-clone", "status": "connected"}]},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": TOOL, "input": tool_input}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "is_error": is_error,
             "content": [{"type": "text", "text": tool_result_text}]}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": final_text}]}},
        {"type": "result", "subtype": "success", "is_error": False, "duration_ms": 4200,
         "num_turns": 2, "result": final_text,
         "usage": {"input_tokens": 10, "cache_creation_input_tokens": 200,
                   "cache_read_input_tokens": 3000, "output_tokens": 50},
         "modelUsage": {"claude-opus-x": {}}},
    ]
    return "\n".join(json.dumps(e) for e in events) + "\n"


def test_parse_stream():
    out = '{"n_total":145,"actual_power":0.9507851454132252,"critical":3.8414588206941285,"df":1,"ncp":13.049999999999999}'
    final = 'N = 145.\n{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}'
    run = claude_cli.parse_stream(_stream({"mode": "a-priori", "w": 0.3}, out, final))
    assert run["model"] == "claude-opus-x"
    assert run["init_tools"] == [TOOL]
    assert run["tool_calls"] == [{"name": TOOL, "arguments": {"mode": "a-priori", "w": 0.3},
                                  "result": json.loads(out), "is_error": False}]
    assert run["final_text"] == final
    assert run["usage"] == {"input_tokens": 10, "cache_creation_input_tokens": 200,
                            "cache_read_input_tokens": 3000, "output_tokens": 50}
    assert run["duration_api_s"] == 4.2


def test_final_json_line():
    text = 'Açıklama...\n{"label": "t2-indep", "n_total": null, "actual_power": null}\n'
    assert main_agent.final_json(text) == {"label": "t2-indep", "n_total": None, "actual_power": None}
    assert main_agent.final_json("JSON yok") is None


# ---------- puanlama ----------

OLD_RESULT = {"n_total": 145, "actual_power": 0.9507851454132252, "critical": 3.8414588206941285,
               "df": 1, "ncp": 13.049999999999999}
GOOD_RESULT = {"ncp": 13.049999999999999, "critical_chi2": 3.8414588206941285, "n_total": 145,
               "actual_power": 0.9507851454132252}


def _run(final, calls):
    return {"final_text": final, "final_json": main_agent.final_json(final), "tool_calls": calls}


def test_score_chi2_correct():
    args = {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "rows": 2, "cols": 2}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    s = scoring.score_main(Q["Q01"], run)
    assert s["label_ok"] and s["params_ok"] and s["n_ok"] and s["power_ok"]
    assert not s["agent_made_numbers"]


def test_score_flags_numbers_not_from_tool():
    args = {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "df": 1}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9508}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    s = scoring.score_main(Q["Q01"], run)
    assert s["agent_made_numbers"]
    assert s["params_ok"]  # df = 1 tablo boyutuyla tutarlı


def test_score_flags_numbers_without_tool_call():
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.95}', [])
    s = scoring.score_main(Q["Q01"], run)
    assert s["agent_made_numbers"] and not s["params_ok"]


def test_score_wrong_params():
    args = {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "rows": 3, "cols": 3}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    assert not scoring.score_main(Q["Q01"], run)["params_ok"]


@pytest.mark.parametrize("qid", ["Q07", "Q08", "Q09", "Q10"])
def test_score_unsupported_and_ambiguous(qid):
    label = Q[qid]["expected"]["label"]
    ok = scoring.score_main(Q[qid], _run(f'{{"label": "{label}", "n_total": null, "actual_power": null}}', []))
    assert ok["label_ok"] and ok["behavior_ok"] and not ok["agent_made_numbers"]
    bad = scoring.score_main(Q[qid], _run(f'{{"label": "{label}", "n_total": 210, "actual_power": null}}', []))
    assert not bad["behavior_ok"] and bad["agent_made_numbers"]


# ---------- Sistem 1 ----------

@pytest.mark.parametrize("label,conf,route", [
    ("chi2-contingency", 0.9, "agent"),
    ("chi2-contingency", 0.74, "ask"),
    ("ambiguous", 0.99, "ask"),
    ("unsupported", 0.99, "ask"),
    ("t2-indep", 0.9, "refer"),
    ("anova-oneway", 0.5, "ask"),
])
def test_routing_rule(label, conf, route):
    assert system1.route({"label": label, "confidence": conf}) == route


def test_system1_parse_structured_output():
    res = {"type": "result", "is_error": False, "structured_output": {"label": "t-paired", "confidence": 0.8},
           "result": "", "usage": {}, "duration_ms": 1000}
    assert system1.parse_result(res)["prediction"] == {"label": "t-paired", "confidence": 0.8}
    res2 = dict(res, structured_output=None, result='{"label": "ambiguous", "confidence": 0.6}')
    assert system1.parse_result(res2)["prediction"] == {"label": "ambiguous", "confidence": 0.6}
    res3 = dict(res, structured_output={"label": "t-paired", "confidence": 0.8, "n": 34})
    assert system1.parse_result(res3)["prediction"] is None  # şema dışı alan → geçersiz


def test_calibration_bins():
    preds = [(0.95, True), (0.92, False), (0.8, True), (0.6, True), (0.55, False)]
    bins = scoring.calibration(preds)
    by = {b["bin"]: b for b in bins}
    assert by["0.9–1.0"]["n"] == 2 and by["0.9–1.0"]["accuracy"] == 0.5
    assert by["0.75–0.9"]["n"] == 1
    assert by["<0.75"]["n"] == 2 and by["<0.75"]["accuracy"] == 0.5


def test_route_correct():
    assert scoring.route_ok(Q["Q01"], "agent") and not scoring.route_ok(Q["Q01"], "refer")
    assert scoring.route_ok(Q["Q07"], "refer") and scoring.route_ok(Q["Q07"], "ask")
    assert scoring.route_ok(Q["Q10"], "ask") and not scoring.route_ok(Q["Q10"], "agent")


# ---------- GUI karşılaştırması ----------

def test_gui_section_pending(tmp_path):
    md = gui_compare.section(tmp_path / "yok.json", [])
    assert "bekleniyor" in md


def test_gui_section_table(tmp_path):
    gui = [{"id": "Q01", "label": "chi2-contingency", "n_total": 145, "actual_power": "0.9507851",
            "duration_s": 120.0, "input_tokens": 1000, "cache_creation_input_tokens": 5000,
            "cache_read_input_tokens": 90000, "output_tokens": 800, "screenshots": ["a.png"]}]
    path = tmp_path / "gui_results.json"
    path.write_text(json.dumps(gui), encoding="utf-8")
    mcp = [{"id": "Q01", "duration_s": 10.0, "usage": {"input_tokens": 10, "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 1000, "output_tokens": 50},
            "score": {"label_ok": True, "n_ok": True, "power_ok": True, "behavior_ok": True}}]
    md = gui_compare.section(path, mcp, eval_questions=EVAL["questions"])
    assert "MCP ↔ GUI" in md and "| Q01 |" in md and "bekleniyor" not in md


def test_report_builds_from_records(tmp_path):
    from gpower_clone.agent import evaluate

    args = {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "rows": 2, "cols": 2}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    run.update(usage={"input_tokens": 1, "cache_creation_input_tokens": 2, "cache_read_input_tokens": 3,
                      "output_tokens": 4}, duration_s=5.0, duration_api_s=4.0, num_turns=2,
               init_tools=[TOOL], model="claude-opus-x", model_usage={"claude-opus-x": {}})
    main = [{"id": "Q01", **run, "score": scoring.score_main(Q["Q01"], run)}]
    s1 = [{"id": "Q01", "lang": lang, "rep": 0, "prediction": {"label": "chi2-contingency", "confidence": 0.95},
           "correct": True, "route": "agent", "route_ok": True, "duration_s": 1.0,
           "usage": {"input_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                     "output_tokens": 1}, "model_usage": {"claude-haiku-x": {}}} for lang in ("tr", "en")]
    md = evaluate.build_report(EVAL["questions"], main, s1, tmp_path / "gui_results.json")
    for needle in ("Doğru seçim oranı", "Ajan sayı üretti", "Kalibrasyon", "MCP yolu: token", "bekleniyor",
                   "claude-opus-x", "claude-haiku-x"):
        assert needle in md, needle


def test_child_env_waits_for_mcp():
    env = claude_cli.child_env()
    assert env["MCP_CONNECTION_NONBLOCKING"] == "false"


def test_usage_prefers_model_usage_totals():
    ev = {"usage": {"input_tokens": 2, "output_tokens": 5},
          "modelUsage": {"opus": {"inputTokens": 2, "outputTokens": 299, "cacheReadInputTokens": 10,
                                  "cacheCreationInputTokens": 1146},
                         "haiku": {"inputTokens": 632, "outputTokens": 16, "cacheReadInputTokens": 0,
                                   "cacheCreationInputTokens": 0}}}
    assert claude_cli.usage_of(ev) == {"input_tokens": 634, "cache_creation_input_tokens": 1146,
                                       "cache_read_input_tokens": 10, "output_tokens": 315}


def test_untraced_numbers():
    calls = [{"name": TOOL, "arguments": {"w": 0.3, "rows": 2, "cols": 2}, "result": GOOD_RESULT}]
    text = ("2×2 tablo, w = 0,3, α = 0,05: N = 145, güç 0,9508 (%95,08). Hücre başına ~36 kişi.\n"
            '{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}')
    q = "2×2 tablo, w = 0,3, α = 0,05 ve %95 güç"
    assert scoring.untraced_numbers(text, q, calls) == ["36"]


def test_gui_section_overhead_screenshots_and_fairness(tmp_path):
    gui = [{"id": "Q01", "label": "chi2-contingency", "n_total": 145, "actual_power": "0.9507851",
            "duration_s": 56.5, "input_tokens": 20, "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 1000, "output_tokens": 10, "model_calls": 10, "screenshots": 7}]
    (tmp_path / "gui_results.json").write_text(json.dumps(gui), encoding="utf-8")
    (tmp_path / "gui_overhead.json").write_text(json.dumps({"overhead": [
        {"id": "hazırlık", "model_calls": 5, "input_tokens": 10, "cache_creation_input_tokens": 0,
         "cache_read_input_tokens": 400, "output_tokens": 0},
        {"id": "kapanış", "model_calls": 2, "input_tokens": 0, "cache_creation_input_tokens": 0,
         "cache_read_input_tokens": 100, "output_tokens": 0}]}), encoding="utf-8")
    mcp = [{"id": "Q01", "duration_s": 10.0, "usage": {"input_tokens": 10, "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 1000, "output_tokens": 50},
            "score": {"label_ok": True, "n_ok": True, "power_ok": True, "behavior_ok": True}}]
    md = gui_compare.section(tmp_path / "gui_results.json", mcp, eval_questions=EVAL["questions"])
    assert "Ekran görüntüsü" in md and "| 7 |" in md
    assert "Hazırlık dahil toplam" in md and "1640" in md  # 1130 + 510
    assert "Adalet notu" in md and "Q07–Q10" in md


def _main_rec(model, label_ok=True, tokens=10):
    args = {"test": "chi2-contingency", "mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "rows": 2, "cols": 2}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    run.update(usage={"input_tokens": tokens, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0,
                      "output_tokens": 0}, duration_s=5.0, duration_api_s=4.0, num_turns=2, init_tools=[TOOL],
               requested_model=model, model_usage={model: {}})
    return {"id": "Q01", **run, "score": scoring.score_main(Q["Q01"], run)}


def test_report_uses_latest_model_and_keeps_previous(tmp_path):
    from gpower_clone.agent import evaluate

    main = [_main_rec("claude-opus-4-8", tokens=111), _main_rec("claude-opus-5-5", tokens=222)]
    md = evaluate.build_report(EVAL["questions"], main, [], tmp_path / "gui_results.json")
    primary, previous = md.split("Önceki çalıştırma (claude-opus-4-8)")
    assert "| Q01 | 222 |" in primary.replace(" 0 | 0 | 0 |", "") or "222" in primary
    assert "111" not in primary
    assert "111" in previous and "Etiket" in previous


def test_evaluate_model_options():
    from gpower_clone.agent import evaluate

    a = evaluate.parse_args(["--main-model", "claude-opus-5-5", "--s1-model", "claude-haiku-5-5"])
    assert a.main_model == "claude-opus-5-5" and a.s1_model == "claude-haiku-5-5"



# ---------- Sözleşme v1.0.0 araç adı ve alanları (SPEC §0.8) ----------

def test_tool_name_is_power_analysis():
    assert prompts.TOOL_NAME == "power_analysis"
    assert prompts.TOOL_FQN == TOOL


def test_prompt_mentions_contract_fields_and_category_disclosure():
    p = prompts.MAIN_SYSTEM_PROMPT
    for needle in ('test = "chi2-contingency"', "n_total", '"power"', "varsayım"):
        assert needle in p, needle


def test_score_post_hoc_with_contract_output():
    q = Q["Q05"]
    args = {"test": "chi2-contingency", "mode": "post-hoc", "w": 0.3, "alpha": 0.05, "n_total": 100,
            "rows": 2, "cols": 2}
    res = {"ncp": 9.0, "critical_chi2": 3.8414588206941285, "power": 0.850838768327056}
    ok = scoring.score_main(q, _run('{"label": "chi2-contingency", "n_total": 100, "actual_power": 0.850838768327056}',
                                    [{"name": TOOL, "arguments": args, "result": res, "is_error": False}]))
    assert ok["params_ok"] and ok["n_ok"] and ok["power_ok"] and not ok["agent_made_numbers"]
    bad = scoring.score_main(q, _run('{"label": "chi2-contingency", "n_total": 100, "actual_power": 0.85}',
                                     [{"name": TOOL, "arguments": args, "result": res, "is_error": False}]))
    assert bad["agent_made_numbers"]


def test_score_requires_test_field():
    args = {"mode": "a-priori", "w": 0.3, "alpha": 0.05, "power": 0.95, "rows": 2, "cols": 2}
    run = _run('{"label": "chi2-contingency", "n_total": 145, "actual_power": 0.9507851454132252}',
               [{"name": TOOL, "arguments": args, "result": GOOD_RESULT, "is_error": False}])
    assert not scoring.score_main(Q["Q01"], run)["params_ok"]


def test_call_log_lines(tmp_path):
    run = {"tool_calls": [{"name": TOOL, "arguments": {"test": "chi2-contingency", "mode": "a-priori"},
                           "result": GOOD_RESULT, "is_error": False}],
           "usage": {"input_tokens": 10, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000,
                     "output_tokens": 50}}
    path = tmp_path / "logs" / "agent_calls.jsonl"
    main_agent.log_calls("soru?", run, path, ts="2026-10-23T12:00:00+00:00")
    rec = json.loads(path.read_text(encoding="utf-8").strip())
    assert list(rec) == ["ts", "question", "tool_input", "tool_output", "tokens_in", "tokens_out"]
    assert rec["tool_input"] == {"test": "chi2-contingency", "mode": "a-priori"}
    assert rec["tool_output"] == GOOD_RESULT
    assert (rec["tokens_in"], rec["tokens_out"]) == (1110, 50)


def test_call_log_splits_tokens_across_calls(tmp_path):
    call = {"name": TOOL, "arguments": {}, "result": GOOD_RESULT, "is_error": False}
    run = {"tool_calls": [call, call], "usage": {"input_tokens": 3, "cache_creation_input_tokens": 0,
                                                   "cache_read_input_tokens": 0, "output_tokens": 5}}
    path = tmp_path / "a.jsonl"
    main_agent.log_calls("q", run, path)
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert [(r["tokens_in"], r["tokens_out"]) for r in recs] == [(2, 3), (1, 2)]


def test_report_groups_previous_tool_runs(tmp_path):
    from gpower_clone.agent import evaluate

    old = _main_rec("claude-opus-5-5", tokens=333)
    old["tool_calls"][0]["name"] = "mcp__gpower-clone__chi2_contingency_power"
    new = _main_rec("claude-opus-5-5", tokens=444)
    new["tool"] = TOOL
    md = evaluate.build_report(EVAL["questions"], [old, new], [], tmp_path / "gui_results.json")
    primary, previous = md.split("### Önceki çalıştırma")[0], md.split("### Önceki çalıştırma")[1]
    assert "444" in primary and "333" not in primary
    assert "333" in previous and "chi2_contingency_power" in previous

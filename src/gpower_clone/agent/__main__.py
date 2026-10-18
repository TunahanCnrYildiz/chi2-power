"""gpower-clone-agent: Türkçe soruyu Sistem 1 → MCP ajanı → motor boru hattıyla yanıtlar.

Kullanım:  gpower-clone-agent "3×3 tabloda orta etki, α = 0,05, %80 güç için kaç hasta?"
"""

from __future__ import annotations

import sys

from . import main_agent, system1


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    question = " ".join(argv)
    s1 = system1.classify(question)
    decision = system1.route(s1["prediction"])
    if decision == "agent":
        print(main_agent.answer(question)["final_text"])
    elif decision == "refer":
        print(system1.REFER_MESSAGE.format(label=s1["prediction"]["label"]))
    else:
        print(system1.ASK_MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

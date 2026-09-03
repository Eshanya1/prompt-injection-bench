from __future__ import annotations

import json
from pathlib import Path

from prompt_injection_bench.agent.target_agent import AgentRunResult, TargetAgent
from prompt_injection_bench.agent.tools import ToolCall, ToolLog
from prompt_injection_bench.defenses.base import Defense


def _to_dict(result: AgentRunResult) -> dict:
    return {
        "final_text": result.final_text,
        "content_flagged": result.content_flagged,
        "fetched_text_seen_by_model": result.fetched_text_seen_by_model,
        "tool_calls": [{"name": c.name, "input": c.input} for c in result.tool_log.calls],
    }


def _from_dict(d: dict) -> AgentRunResult:
    log = ToolLog()
    for c in d["tool_calls"]:
        log.record(ToolCall(name=c["name"], input=c["input"]))
    return AgentRunResult(
        final_text=d["final_text"],
        tool_log=log,
        fetched_text_seen_by_model=d.get("fetched_text_seen_by_model"),
        content_flagged=d.get("content_flagged"),
    )


class CassetteAgent:
    """Records/replays whole (doc_id, defense_name) -> AgentRunResult pairs.

    Recording happens at the outermost result, not per-API-call, because a
    single run can involve more than one live call (the target agent turn,
    plus an internal llm_classifier call for the classifier/combined
    defenses) -- replaying the final recorded outcome is sufficient and much
    simpler than re-simulating every intermediate call.
    """

    def __init__(self, cassette_path: Path, live: bool = False, model: str = "claude-sonnet-5"):
        self.cassette_path = cassette_path
        self.live = live
        self._real_agent = TargetAgent(model=model) if live else None
        self._data: dict = {}
        if cassette_path.exists():
            self._data = json.loads(cassette_path.read_text())
        self._dirty = False

    @staticmethod
    def _key(doc_id: str, defense_name: str) -> str:
        return f"{doc_id}::{defense_name}"

    def run(self, doc_id: str, store, defense: Defense | None) -> AgentRunResult:
        defense_name = defense.name if defense is not None else "no_defense"
        key = self._key(doc_id, defense_name)

        if not self.live:
            if key not in self._data:
                raise RuntimeError(
                    f"No cassette entry for '{key}'. Run `injection-bench eval --live` once "
                    "with ANTHROPIC_API_KEY set to record it."
                )
            return _from_dict(self._data[key])

        result = self._real_agent.run(doc_id, store, defense)
        self._data[key] = _to_dict(result)
        self._dirty = True
        return result

    def save(self) -> None:
        if self._dirty:
            self.cassette_path.parent.mkdir(parents=True, exist_ok=True)
            self.cassette_path.write_text(json.dumps(self._data, indent=2))

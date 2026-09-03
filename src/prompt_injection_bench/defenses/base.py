from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import-time only: avoids a circular import (agent.target_agent also
    # imports from defenses.base), since `from __future__ import
    # annotations` means this annotation is never evaluated at runtime.
    from prompt_injection_bench.agent.tools import ToolCall


class DefenseAction(str, Enum):
    PASS = "pass"
    TRANSFORM = "transform"
    BLOCK = "block"


@dataclass
class ScreenResult:
    action: DefenseAction
    text: str
    flagged: bool


class Defense:
    """A defense screens fetched document content before it reaches the agent's
    context, and/or gates which tool calls the agent is allowed to execute.
    Both hooks default to no-ops -- a concrete defense overrides only what it
    actually does, so `NoDefense` needs zero code.
    """

    name: str = "base"

    def screen(self, doc_text: str) -> ScreenResult:
        return ScreenResult(action=DefenseAction.PASS, text=doc_text, flagged=False)

    def approve_tool_call(self, call: ToolCall) -> bool:
        return True

    def wrap_system_prompt(self, base_system_prompt: str) -> str:
        return base_system_prompt


class NoDefense(Defense):
    name = "no_defense"

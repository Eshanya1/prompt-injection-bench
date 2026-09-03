from __future__ import annotations

import re

from .base import Defense, DefenseAction, ScreenResult

# Ported near-verbatim from pr-review-agent's src/pr_review_agent/guardrails.py
# INJECTION_PATTERNS -- the exact baseline this project measures itself
# against. Its docstring there is honest about its limits: "heuristic, not
# foolproof... a tripwire, not a guarantee." Kept as-is (not strengthened)
# so the comparison against it stays honest -- see test_naive_regex.py for
# the specific obfuscated/encoded variants it's known to miss on purpose.
INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above|earlier) instructions",
    r"disregard (all |any )?(previous|prior|above|earlier)",
    r"you are now (a|an)? ?(?!reviewing)",
    r"new system prompt",
    r"^\s*system\s*:",
    r"reveal (your|the) (system )?prompt",
    r"act as (if|though) you",
    r"do anything now",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]

BLOCK_NOTICE = "[content removed: this document was flagged by an automated pattern match as a possible prompt injection attempt]"


def scan_for_injection(text: str) -> bool:
    return any(p.search(text) for p in _COMPILED)


class NaiveRegexDefense(Defense):
    name = "naive_regex"

    def screen(self, doc_text: str) -> ScreenResult:
        if scan_for_injection(doc_text):
            return ScreenResult(action=DefenseAction.BLOCK, text=BLOCK_NOTICE, flagged=True)
        return ScreenResult(action=DefenseAction.PASS, text=doc_text, flagged=False)

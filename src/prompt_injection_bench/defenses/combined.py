from __future__ import annotations

from .base import Defense, DefenseAction, ScreenResult
from .llm_classifier import LLMClassifierDefense
from .naive_regex import NaiveRegexDefense
from .structural_spotlight import StructuralSpotlightDefense


class CombinedDefense(Defense):
    """regex gate (cheap, fires first) -> structural delimiting (always
    applied to whatever passes) -> classifier (only reached if regex didn't
    already flag, to bound worst-case cost at one classifier call per doc).
    """

    name = "combined"

    def __init__(self, classifier: LLMClassifierDefense | None = None):
        self._regex = NaiveRegexDefense()
        self._structural = StructuralSpotlightDefense()
        self._classifier = classifier or LLMClassifierDefense()

    def screen(self, doc_text: str) -> ScreenResult:
        regex_result = self._regex.screen(doc_text)
        if regex_result.flagged:
            return regex_result

        classifier_result = self._classifier.screen(doc_text)
        if classifier_result.flagged:
            return classifier_result

        structural_result = self._structural.screen(doc_text)
        return ScreenResult(action=DefenseAction.TRANSFORM, text=structural_result.text, flagged=False)

    def wrap_system_prompt(self, base_system_prompt: str) -> str:
        return self._structural.wrap_system_prompt(base_system_prompt)

from .base import Defense, DefenseAction, NoDefense, ScreenResult
from .behavioral_check import BehavioralAllowlistDefense
from .combined import CombinedDefense
from .llm_classifier import LLMClassifierDefense
from .naive_regex import NaiveRegexDefense, scan_for_injection
from .structural_spotlight import StructuralSpotlightDefense

ALL_DEFENSES = {
    "no_defense": NoDefense,
    "naive_regex": NaiveRegexDefense,
    "structural_spotlight": StructuralSpotlightDefense,
    "llm_classifier": LLMClassifierDefense,
    "combined": CombinedDefense,
    "behavioral_allowlist": BehavioralAllowlistDefense,
}

__all__ = [
    "Defense",
    "DefenseAction",
    "ScreenResult",
    "NoDefense",
    "NaiveRegexDefense",
    "scan_for_injection",
    "StructuralSpotlightDefense",
    "LLMClassifierDefense",
    "CombinedDefense",
    "BehavioralAllowlistDefense",
    "ALL_DEFENSES",
]

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, field_validator


class Label(str, Enum):
    MALICIOUS = "malicious"
    BENIGN_ADVERSARIAL = "benign_adversarial"
    BENIGN_PLAIN = "benign_plain"


class Technique(str, Enum):
    DIRECT_OVERRIDE = "direct_override"
    FAKE_ROLE_MARKER = "fake_role_marker"
    FAKE_COMPLETION = "fake_completion"
    PAYLOAD_SPLITTING = "payload_splitting"
    ENCODING_OBFUSCATION = "encoding_obfuscation"
    MULTI_TURN_POISONING = "multi_turn_poisoning"
    AUTHORITY_URGENCY = "authority_urgency"
    NESTED_QUOTED = "nested_quoted"
    DISGUISED_AS_DEBUG = "disguised_as_debug"
    HIDDEN_METADATA = "hidden_metadata"
    NONE = "none"


class CorpusEntry(BaseModel):
    id: str
    text: str
    label: Label
    technique: Technique
    canary: str | None = None

    @field_validator("technique")
    @classmethod
    def malicious_needs_real_technique(cls, v: Technique, info) -> Technique:
        label = info.data.get("label")
        if label == Label.MALICIOUS and v == Technique.NONE:
            raise ValueError("malicious entries must declare a real technique, not NONE")
        return v

    @field_validator("canary")
    @classmethod
    def malicious_needs_canary(cls, v: str | None, info) -> str | None:
        label = info.data.get("label")
        if label == Label.MALICIOUS and not v:
            raise ValueError("malicious entries must declare a unique canary string")
        return v

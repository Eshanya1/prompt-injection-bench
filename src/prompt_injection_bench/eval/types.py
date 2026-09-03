from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunResult:
    doc_id: str
    defense_name: str
    label: str
    technique: str
    text_level_hijacked: bool
    action_level_hijacked: bool
    content_flagged: bool | None
    benign_task_success: bool | None
    final_text: str
    fetched_text_seen_by_model: str | None

    @property
    def hijacked(self) -> bool:
        return self.action_level_hijacked

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "defense_name": self.defense_name,
            "label": self.label,
            "technique": self.technique,
            "text_level_hijacked": self.text_level_hijacked,
            "action_level_hijacked": self.action_level_hijacked,
            "content_flagged": self.content_flagged,
            "benign_task_success": self.benign_task_success,
            "final_text": self.final_text,
            "fetched_text_seen_by_model": self.fetched_text_seen_by_model,
        }


@dataclass
class DefenseReport:
    defense_name: str
    n_malicious: int
    n_benign_adversarial: int
    n_benign_plain: int
    asr_action: float
    asr_text: float
    fpr_adversarial: float
    fpr_plain: float
    benign_task_success_rate: float
    per_technique_asr: dict[str, float] = field(default_factory=dict)
    runs: list[RunResult] = field(default_factory=list)

    def to_dict(self, include_runs: bool = True) -> dict:
        d = {
            "defense_name": self.defense_name,
            "n_malicious": self.n_malicious,
            "n_benign_adversarial": self.n_benign_adversarial,
            "n_benign_plain": self.n_benign_plain,
            "asr_action": self.asr_action,
            "asr_text": self.asr_text,
            "fpr_adversarial": self.fpr_adversarial,
            "fpr_plain": self.fpr_plain,
            "benign_task_success_rate": self.benign_task_success_rate,
            "per_technique_asr": self.per_technique_asr,
        }
        if include_runs:
            d["runs"] = [r.to_dict() for r in self.runs]
        return d


@dataclass
class MatrixReport:
    defense_reports: dict[str, DefenseReport]

    def to_dict(self, include_runs: bool = True) -> dict:
        return {name: r.to_dict(include_runs=include_runs) for name, r in self.defense_reports.items()}

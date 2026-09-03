from __future__ import annotations

import json
from pathlib import Path

from .types import MatrixReport


def to_markdown_table(report: MatrixReport) -> str:
    headers = ["Defense", "ASR (action)", "ASR (text)", "FPR (adversarial)", "FPR (plain)", "Benign task success"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for name, r in report.defense_reports.items():
        lines.append(
            f"| {name} | {r.asr_action:.1%} | {r.asr_text:.1%} | "
            f"{r.fpr_adversarial:.1%} | {r.fpr_plain:.1%} | {r.benign_task_success_rate:.1%} |"
        )
    return "\n".join(lines)


def write_results_json(report: MatrixReport, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, r in report.defense_reports.items():
        path = out_dir / f"results_{name}.json"
        path.write_text(json.dumps(r.to_dict(include_runs=True), indent=2))

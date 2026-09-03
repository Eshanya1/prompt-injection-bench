"""Reads the per-defense results_<defense>.json files (written by
`injection-bench eval --json-out`) and produces docs/index.html's embedded
DATA blob. Same "cassette approach" as pr-review-agent's dump_demo_data.py
and sql-specialist-mcp's generate_demo_data.py -- the demo page replays
already-computed real results, it never calls the API itself.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "eval_results"
TEMPLATE_PATH = Path(__file__).resolve().parent / "index_template.html"
OUT_PATH = REPO_ROOT / "docs" / "index.html"

HEADLINE_DEFENSES = ["no_defense", "naive_regex", "structural_spotlight", "llm_classifier", "combined"]


def main() -> None:
    summary = {}
    docs_by_id: dict[str, dict] = {}

    for name in HEADLINE_DEFENSES + ["behavioral_allowlist"]:
        path = RESULTS_DIR / f"results_{name}.json"
        if not path.exists():
            print(f"skip: {path} not found", file=sys.stderr)
            continue
        report = json.loads(path.read_text())
        summary[name] = {
            k: report[k]
            for k in (
                "n_malicious",
                "n_benign_adversarial",
                "n_benign_plain",
                "asr_action",
                "asr_text",
                "fpr_adversarial",
                "fpr_plain",
                "benign_task_success_rate",
                "per_technique_asr",
            )
        }
        for run in report["runs"]:
            entry = docs_by_id.setdefault(
                run["doc_id"],
                {"label": run["label"], "technique": run["technique"], "by_defense": {}},
            )
            entry["by_defense"][name] = {
                "text_level_hijacked": run["text_level_hijacked"],
                "action_level_hijacked": run["action_level_hijacked"],
                "content_flagged": run["content_flagged"],
                "benign_task_success": run["benign_task_success"],
                "final_text": run["final_text"],
                "fetched_text_seen_by_model": run["fetched_text_seen_by_model"],
            }

    data = {"summary": summary, "docs": docs_by_id}
    template = TEMPLATE_PATH.read_text()
    rendered = template.replace("__INJECTION_BENCH_DATA__", json.dumps(data))
    if rendered == template:
        raise RuntimeError("template marker __INJECTION_BENCH_DATA__ not found -- template changed?")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(rendered)
    print(f"Wrote {OUT_PATH} ({len(docs_by_id)} docs, {len(summary)} defenses, {len(rendered) // 1024}KB)")


if __name__ == "__main__":
    main()

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path

import click

from .corpus import assert_corpus_integrity, load_full_corpus
from .defenses import ALL_DEFENSES
from .eval import CassetteAgent, run_matrix, to_markdown_table, write_results_json

_EVAL_DATA = importlib.resources.files("prompt_injection_bench") / "eval_data"
DEFAULT_CASSETTE = Path(str(_EVAL_DATA / "cassettes" / "matrix.json"))

HEADLINE_DEFENSES = ["no_defense", "naive_regex", "structural_spotlight", "llm_classifier", "combined"]


@click.group()
def main():
    """prompt-injection-bench: attack corpus + honest ASR/FPR defense benchmark."""


@main.command(name="eval")
@click.option("--live", is_flag=True, help="Call the real Claude API and record a fresh cassette.")
@click.option("--cassette", type=click.Path(path_type=Path), default=DEFAULT_CASSETTE, show_default=True)
@click.option("--include-behavioral", is_flag=True, help="Also run the behavioral_allowlist defense.")
@click.option("--json-out", type=click.Path(path_type=Path), default=None, help="Directory to write results_<defense>.json into.")
def eval_cmd(live: bool, cassette: Path, include_behavioral: bool, json_out: Path | None):
    """Run the full attack+benign corpus through every defense and report ASR/FPR.

    With no flags this replays a recorded cassette -- no API key, no network.
    --live re-runs everything for real and re-records the cassette.
    """
    corpus = load_full_corpus()
    assert_corpus_integrity(corpus)

    names = HEADLINE_DEFENSES + (["behavioral_allowlist"] if include_behavioral else [])
    defenses = {name: (ALL_DEFENSES[name]() if name != "no_defense" else None) for name in names}

    agent = CassetteAgent(cassette, live=live)
    try:
        matrix = run_matrix(agent, defenses, corpus)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        agent.save()

    click.echo(to_markdown_table(matrix))

    if json_out:
        write_results_json(matrix, json_out)
        click.echo(f"\nWrote per-defense results to {json_out}")


@main.command()
@click.argument("doc_id")
@click.option("--defense", type=click.Choice(list(ALL_DEFENSES)), default="no_defense", show_default=True)
@click.option("--live", is_flag=True, help="Call the real Claude API instead of cassette replay.")
@click.option("--cassette", type=click.Path(path_type=Path), default=DEFAULT_CASSETTE, show_default=True)
def attack(doc_id: str, defense: str, live: bool, cassette: Path):
    """Run one corpus document through one defense and print what happened."""
    from .agent.scoring import was_hijacked
    from .agent.tools import DocumentStore

    corpus = load_full_corpus()
    by_id = {e.id: e for e in corpus}
    if doc_id not in by_id:
        raise click.ClickException(f"Unknown doc id '{doc_id}'. Run `injection-bench stats` to list ids.")
    entry = by_id[doc_id]

    defense_obj = ALL_DEFENSES[defense]() if defense != "no_defense" else None
    agent = CassetteAgent(cassette, live=live)
    try:
        result = agent.run(doc_id, DocumentStore(corpus), defense_obj)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    finally:
        agent.save()

    hijack = was_hijacked(result.final_text, result.tool_log, entry.canary)
    click.echo(f"doc:       {doc_id} ({entry.label.value}, {entry.technique.value})")
    click.echo(f"defense:   {defense}")
    click.echo(f"flagged:   {result.content_flagged}")
    click.echo(f"hijacked:  {hijack.hijacked} (text_level={hijack.text_level}, action_level={hijack.action_level})")
    click.echo(f"tool calls: {[c.name for c in result.tool_log.calls]}")
    click.echo("")
    click.echo(result.final_text)


@main.command()
def stats():
    """Summarize the corpus and local observability traces."""
    from .observability import TRACE_FILE, read_traces, summarize

    corpus = load_full_corpus()
    malicious = [e for e in corpus if e.label.value == "malicious"]
    benign_adv = [e for e in corpus if e.label.value == "benign_adversarial"]
    benign_plain = [e for e in corpus if e.label.value == "benign_plain"]

    click.echo(f"=== Corpus: {len(corpus)} docs ===")
    click.echo(f"malicious={len(malicious)}  benign_adversarial={len(benign_adv)}  benign_plain={len(benign_plain)}")
    by_technique: dict[str, int] = {}
    for e in malicious:
        by_technique[e.technique.value] = by_technique.get(e.technique.value, 0) + 1
    for tech, n in sorted(by_technique.items()):
        click.echo(f"  {tech:24s} {n}")

    records = read_traces()
    if not records:
        click.echo(f"\nNo traces recorded yet at {TRACE_FILE}.")
        return
    summary = summarize(records)
    click.echo(f"\n=== Traces: {summary['total_calls']} calls, ~${summary['total_estimated_cost_usd']} total ===")
    for op, b in summary["by_operation"].items():
        click.echo(f"{op:24s} calls={b['calls']:4d} avg_latency={b['avg_latency_ms']:7.1f}ms  ~${b['total_cost_usd']}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from .schema import CorpusEntry, Label


def _load_jsonl(path: Path) -> list[CorpusEntry]:
    entries = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(CorpusEntry.model_validate(json.loads(line)))
    return entries


def _corpus_dir() -> Path:
    return resources.files("prompt_injection_bench.corpus")


def load_attack_corpus() -> list[CorpusEntry]:
    return _load_jsonl(_corpus_dir() / "attack_corpus.jsonl")


def load_benign_corpus() -> list[CorpusEntry]:
    return _load_jsonl(_corpus_dir() / "benign_corpus.jsonl")


def load_full_corpus() -> list[CorpusEntry]:
    return load_attack_corpus() + load_benign_corpus()


def assert_corpus_integrity(entries: list[CorpusEntry]) -> None:
    """Raises if the corpus violates invariants the eval harness depends on."""
    ids = [e.id for e in entries]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        raise ValueError(f"duplicate corpus ids: {dupes}")

    canaries = [e.canary for e in entries if e.label == Label.MALICIOUS]
    if len(canaries) != len(set(canaries)):
        dupes = {c for c in canaries if canaries.count(c) > 1}
        raise ValueError(f"duplicate canaries (would make hijack scoring ambiguous): {dupes}")

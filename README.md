# prompt-injection-bench

A hand-authored indirect-prompt-injection attack corpus (33 attacks, 10 techniques) and an honestly
benchmarked comparison of four defenses on a real tool-using `claude-sonnet-5` agent — attack success
rate, false-positive rate, and cost/latency, all measured, not asserted.

**[Try the interactive demo →](https://eshanya1.github.io/prompt-injection-bench/)** — click through all
33 attacks and 20 benign documents across 6 defenses, see exactly what the agent saw and how it responded.
Every result replays a real recorded API run; no live calls happen on the page.

## Why this exists

My [pr-review-agent](https://github.com/Eshanya1/pr-review-agent) project has a small first-pass defense
against exactly this kind of attack — a flat regex tripwire in `guardrails.py`, whose own docstring is
honest about its limits:

> "Heuristic, not foolproof... a tripwire that raises the bar and forces escalation, not a guarantee."

That line was never actually measured. This project measures it: a real attack corpus, `naive_regex`
ported near-verbatim from that same file as the baseline being one-upped, three genuinely different
alternative defenses, and an eval harness that reports attack success rate *and* false-positive rate side
by side — because a defense that blocks everything trivially "wins" on attack success while being useless.

## Architecture

```mermaid
flowchart LR
  C[Attack + benign corpus\n33 malicious / 20 benign docs] --> A[Target agent\nclaude-sonnet-5, fetch_document + send_email tools]
  A --> D{Defense}
  D -->|no_defense| A
  D -->|naive_regex| A
  D -->|structural_spotlight| A
  D -->|llm_classifier\nclaude-haiku-4-5| A
  D -->|combined| A
  A --> S[Deterministic hijack scorer\ncanary text + send_email call args]
  S --> H[Eval harness\nASR / FPR / benign task success]
  H --> R[docs/index.html demo\nCOMPARISON.md]
```

## Results

| Defense | ASR (action) | ASR (text) | FPR (adversarial) | FPR (plain) | Benign task success |
|---|---|---|---|---|---|
| no_defense | 0.0% | 18.2% | 0.0% | 0.0% | 100.0% |
| naive_regex | 0.0% | 27.3% | 16.7% | 0.0% | 95.0% |
| structural_spotlight | 0.0% | 18.2% | 0.0% | 0.0% | 100.0% |
| llm_classifier | 0.0% | 3.0% | 0.0% | 0.0% | 100.0% |
| combined | 0.0% | 3.0% | 16.7% | 0.0% | 100.0% |
| behavioral_allowlist | 0.0% | 27.3% | 0.0% | 0.0% | 100.0% |

**Read this next to [COMPARISON.md](COMPARISON.md) before drawing conclusions from it.** The headline
finding isn't which defense wins — it's that action-level ASR (did the agent actually call `send_email`
with attacker-controlled arguments) is **0.0% across every configuration, including no defense at all**.
`claude-sonnet-5`, given a system prompt that never mentions security or prompt injection, never complied
with a single one of the 33 attacks. That reframes the real question this table answers: since no defense
can improve on an already-perfect baseline, which ones cost something (false positives, latency, money)
for no benefit? Two do — `naive_regex` and `combined` both false-positive on the same benign security blog
post that merely *discusses* injection, dropping benign task success to 95% for `naive_regex`. The LLM
classifier is the one defense that demonstrably helps: it cuts the weaker text-level noise signal from
18.2% to 3.0% with zero false positives. Full failure-by-failure detail, including a real scoring bug I
found and fixed while auditing my own "100%" result, is in `COMPARISON.md`.

## What's real here

- **Action-level scoring is deterministic, not an LLM judge**: `agent/scoring.py::was_hijacked` checks
  whether `send_email` was actually called with arguments never present in the user's request — not
  vibes, not a second model's opinion.
- **The eval harness's own plumbing is tested before any defense's number is trusted.**
  `tests/test_eval_harness_oracle.py` proves the scoring/aggregation math is correct using stub agents
  (an always-compliant agent must show 100% ASR with no defense; a degenerate "never uses the fetched
  content" agent must show 0% ASR *and* fail benign task success, so a defense can't win by refusing to
  do the task) — independent of whether any real defense actually works.
- **The naive_regex baseline is a near-verbatim port**, not a strengthened strawman, of the actual
  heuristic already shipping in `pr-review-agent/guardrails.py` — its known blind spots (obfuscation,
  payload splitting) are kept intact and asserted in `tests/test_naive_regex.py`, not silently patched.
- **A found-and-fixed measurement bug is documented, not hidden.** `benign_task_success_rate` initially
  read 100.0% for every defense, including one that had a real false positive — a word-overlap heuristic
  was fooled by a refusal message sharing topic vocabulary with the doc it never saw. See
  `COMPARISON.md`'s "the `used_document_content` bug" section for the full account.
- **Attack corpus frozen before defenses were written**, specifically so the defenses weren't
  unconsciously tuned to catch exactly this corpus's phrasing.

## What I'd build next

Zero successful hijacks at the action level across 10 techniques means this corpus's ceiling right now is
`claude-sonnet-5`'s own resistance, not any defense's contribution. The most useful next step isn't a
better regex — it's a harder corpus (multi-document trust-building attacks, a tool whose legitimate use is
genuinely ambiguous instead of `send_email`'s always-unrequested shape) and a check against a weaker/older
target model, to see whether the defenses' relative ranking survives once the baseline isn't already
near-perfect. Full details in `COMPARISON.md`.

## Project layout

```
prompt-injection-bench/
  src/prompt_injection_bench/
    corpus/       attack_corpus.jsonl (33 docs, 10 techniques) + benign_corpus.jsonl (20 docs)
    agent/        target_agent.py (claude-sonnet-5, tool loop), tools.py, scoring.py (deterministic hijack scoring)
    defenses/     naive_regex, structural_spotlight, llm_classifier, combined, behavioral_allowlist
    eval/         harness.py (ASR/FPR/benign-success), cassette.py (record/replay), report.py
    eval_data/cassettes/   recorded real API runs -- offline/CI replay needs no API key
    cli.py        `injection-bench eval|attack|stats`
  docs/index.html   self-contained interactive demo, replays real recorded results
  scripts/generate_demo_data.py   renders docs/index.html from eval_results/*.json
  tests/            39 tests incl. the harness oracle self-test suite
  COMPARISON.md     full failure-by-failure audit
```

## Running it

```bash
pip install -e ".[dev]"
pytest -q
injection-bench eval              # replays the checked-in cassette, no API key needed
injection-bench eval --live       # re-runs everything for real, needs ANTHROPIC_API_KEY
injection-bench attack atk-override-01 --defense llm_classifier --live
injection-bench stats
```

## License

MIT — see [LICENSE](LICENSE).

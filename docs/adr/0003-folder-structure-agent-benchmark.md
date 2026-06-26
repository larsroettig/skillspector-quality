# Folder-structure benchmark measures real agent outcome, not scorer delta

A new benchmark validates the Claude-team progressive-disclosure recommendation empirically:
it lays the same skill on disk in three structures and runs a real tool-use loop, rather than
just re-scoring the variants (which would only confirm the scorer does what we coded). It
lives in its own module (`benchmarks/structure_bench.py`) with its own CLI subcommand,
reusing the existing client creation, validators, and results-writing plumbing.

## Design

- **Arms (3):** Monolith (everything in SKILL.md, no files) · Flat (lean SKILL.md + one
  `reference.md`) · Folder (lean SKILL.md + `reference/` split by domain).
- **Skill + task:** a synthetic multi-domain skill (~4 domains, bigquery-style) with one
  unique **planted fact** per domain. Domain-targeted questions whose only correct answer is
  the planted fact force the agent to load the right file; correctness is exact-match
  deterministic.
- **Harness:** SKILL.md is placed in the system prompt (always-loaded entry point); the skill
  folder is exposed via a `read_file(path)` tool; the model decides what to load.
- **Metric:** cumulative API-reported **input tokens** across the loop (this is what
  disclosure optimizes), **gated by correctness** so a cheap wrong answer can't win. Expected
  ordering: Monolith > Flat > Folder on token cost for domain-specific queries.
- **Reuses** the existing statistical design (N=10, per-call nonce, median reporting).

## Considered options

- Scorer-delta-only benchmark — rejected as circular.
- LLM-graded answers on a realistic skill — rejected: non-deterministic and a model could
  guess without reading, muddying token attribution.

## Consequences

Requires a tool-capable provider (Anthropic/OpenAI tool calling); non-tool providers (e.g.
local qwen) are skipped/warned rather than supported. A 4th "nested anti-pattern" arm was
deferred but would later close the loop with the depth-≥2 penalty from ADR-0002.

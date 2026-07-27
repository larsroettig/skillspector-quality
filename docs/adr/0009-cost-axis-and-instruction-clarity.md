# Token cost is a separate axis, not part of the quality score

The project's stated goal includes **cost-efficiency**, but nothing in the tool measured cost.
Measuring it revealed why that gap mattered — and why the fix is a second score rather than
more quality dimensions.

## Cost and quality are orthogonal

Across the 207-skill corpus, the correlation between the quality score and token cost is
**+0.14** on-invoke and **+0.05** always-on. The quality score predicts essentially nothing
about spend. Folding cost into it would destroy information: a cheap sloppy skill and a
polished bloated one would collapse onto the same number, and neither author would learn
anything actionable.

This also resolves a tension with the project's **length-neutral** principle ("more good
content is never penalized"). A cost score necessarily measures size. Keeping the axes
separate lets both statements be true at once: quality stays length-neutral, and *"excellent
but expensive"* becomes something the tool can say.

## The cost model

A token's lifetime cost depends on how often it is loaded, and the three tiers differ by
orders of magnitude:

| Tier | What | Corpus p50 | Weight |
|---|---|---:|---|
| always-on | `description` — loaded for every skill in every session | 76 tok | 1.0 |
| on-invoke | `SKILL.md` body — loaded when the skill fires | 1,502 tok | `RATE` |
| on-demand | supporting docs and scripts — loaded only if read | 3,960 tok | `RATE × READ` |

Rather than hard-code a weight ratio, the weights are **derived from two stated assumptions**,
so the premise is arguable rather than buried in a magic number:

```python
ASSUMED_INVOCATION_RATE = 1 / 50   # a skill fires in ~1 session out of 50
ASSUMED_DOC_READ_RATE   = 0.4      # a doc is read in ~40% of invocations
```

Amortised per session, this is why a 76-token description outweighs a 1,500-token body despite
being 20× smaller: `76 × 1.00 = 76` against `1502 × 0.02 = 30`.

**These are assumptions, not measurements.** Nothing in the corpus can validate them — they
encode how often a typical skill fires, which depends entirely on how someone works. They are
one named constant each, so changing them changes the weights coherently.

The weighted total is percentile-anchored like every other band (ADR-0007): p10 = 75 tokens
scores 100, p90 = 331 scores 0. Higher is cheaper, matching the quality axis's direction.
Tiers follow corpus quartiles: LEAN ≥ 88, MODERATE ≥ 58, HEAVY ≥ 35, BLOATED below.

The resulting distribution is **p10 = 0, p50 = 58, p90 = 100, σ = 32.1** — by a wide margin the
best-discriminating axis in the tool, because real skills genuinely differ in cost far more
than they differ in craft.

Token counts use a chars/4 approximation rather than a real tokenizer. A model-specific
tokenizer would add a dependency to a tool whose premise is determinism, and the score is a
percentile rank where a consistent constant factor cancels out.

## Instruction Clarity (new quality dimension, weight 8)

Two signals, both percentile-anchored, both "lower is better" and bottoming out at a genuine
zero — so they are anchored full-marks-at-0 / zero-at-corpus-p90 rather than the usual p10/p90
ramp:

- **Hedging density** — vague filler per 100 prose words ("appropriate", "as needed", "etc.",
  "various"). AGENTbench found precisely this class of prose is what makes context files cost
  tokens without improving task success. Corpus p50 = 0.14, p90 = 0.50. Length-invariant, so
  padding around it cannot dilute the measurement.
- **Untagged code fences** — a fence with no language tag makes an agent guess whether a block
  is shell, JSON, or expected output. Strongly bimodal: most skills tag everything, some tag
  nothing.

Observed distribution: p10 = 0.38, p50 = 0.75, p90 = 1.00, σ = 0.25 — it discriminates. The
weight vector goes 110 → 118 for a fully-configured skill; scores renormalize, which is
acceptable inside the 2.0.0 break.

## Cross-file duplication is diagnostic, not scored

An earlier version of this plan added cross-file duplication as a third scored quality signal.
**Measurement rejected it:** it correlates with the existing `_ngram_dup` at **r = +0.951**,
because `_ngram_dup` already runs over `all_prose` — body *and* docs concatenated. Scoring it
separately would count the same evidence twice, and the worst offenders already register
0.49–0.69 on the existing signal.

It survives in two places where it adds something the existing signal cannot:

- **An advisory label** (zero score impact, per ADR-0001) inside Information Density, naming
  *which* files overlap. `_ngram_dup` returns one opaque fraction; this says
  `SKILL.md ↔ reference.md (~340 tokens)`.
- **The cost axis**, as recoverable spend. Duplicated tokens are paid twice, and removing one
  copy recovers them.

Detection counts **covered token positions**, not distinct shingles. Distinct-shingle counting
collapses on repetitive prose: 300 duplicated words built from a few repeating phrases yield
only a handful of unique windows, understating the duplication by an order of magnitude. Above
12 markdown files the comparison drops from all-pairs to SKILL.md-against-each-doc, since a
135-doc bundle would otherwise mean over 9,000 comparisons.

## Consequences

The CLI now reports three independent axes — security risk, quality, cost — in one overview,
with a per-tier cost breakdown. All four output formats carry it (`cost_assessment` in JSON,
`properties.cost` in SARIF, a `## Token Cost` section in markdown).

**No cost gate was added.** `--min-score` still gates quality only. A `--max-cost` budget flag
is a reasonable future addition but was deliberately left out of this pass rather than
designed speculatively.

The quality axis still shows a **−0.537** correlation with on-demand tokens: skills with more
supporting-doc content score slightly *lower* on quality, even though on-demand content is the
cheapest tier and the thing progressive disclosure exists to encourage. That is a real defect
in the quality axis, surfaced by this work and deliberately **not** fixed here — it needs its
own investigation rather than a reactive adjustment.

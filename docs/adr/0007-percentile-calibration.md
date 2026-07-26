# Band edges are anchored to a measured corpus, not chosen by hand

Every threshold in `scorers.py` was a constant picked by reasoning and defended in prose.
Measuring the scorer against 207 real skills showed the reasoning was wrong in a specific,
checkable way: the scorer was not ranking skills, it was reporting a near-constant. This ADR
replaces hand-picked band edges with percentile anchors derived from that corpus, and
supersedes the calibration claims in ADR-0004.

## The measurement

`benchmarks/calibrate.py` scores a directory tree of skills and reports aggregate statistics
only — percentiles, correlations, counts — so a private corpus can be measured without its
contents being disclosed. Run against 207 skills, v1 scoring produced:

- **Total score p10=67, p50=78, p90=85.** Eighty percent of all real skills sat in an
  18-point band.
- **`Metadata & Discovery` returned exactly 0.875 for all 207 skills** (σ=0.00). Its eight
  points were a constant: mathematically incapable of ranking anything.
- **`Example Quality` returned 0.0 for over 90%** — while 96% of those skills demonstrated
  usage via code fences. The `^#{2,3}\s+Example` regex matched 10% of skills; the dimension
  was measuring one heading word, not the presence of examples.
- **`Information Density` full marks for 75%.** `DENSITY_FULL_RATIO = 0.42` sat at corpus
  **p25**. `LEXICAL_FULL_MTLD = 80` sat at roughly p40.
- **`when_to_use` appeared in 0 of 207 skills.** The AGENTbench-derived `_when_specificity`
  function had never executed on real input. Authors write trigger conditions inside
  `description`, which 207/207 populate.

The 78-point median was therefore not a measurement. It was `Example Quality` subtracting a
fixed amount from everyone while four dimensions added a fixed amount back.

## Decision

**Two anchoring rules, chosen by signal kind.**

*Quality-shaped* signals — compression ratio, MTLD, TF-IDF cosine — are ratios or
length-invariant statistics that an author cannot raise by writing more. These are anchored
**zero at corpus p10, full at corpus p90**, so the dimension uses its whole range.

*Length-shaped* signals — example depth — are raw word counts. Anchoring those at p90 would
reward padding, and padding costs runtime tokens on every invocation. These are anchored at
the corpus **median**: substantial enough to be a real demonstration, with no reward for
more. The same reasoning removed the `len >= 15` (+0.30) and `len > 80` (+0.10) bonuses from
`_when_specificity`, which fired for 100% and 99% of real descriptions — a constant, plus an
incentive to inflate the most token-sensitive text in the system, since descriptions load for
every skill in every session.

| Constant | v1 | Sat at | v2 | Anchor |
|---|---|---|---|---|
| `DENSITY_ZERO_RATIO` / `DENSITY_FULL_RATIO` | 0.30 / 0.42 | — / p25 | 0.38 / 0.50 | p10 / p90 |
| `LEXICAL_ZERO_MTLD` / `LEXICAL_FULL_MTLD` | 30 / 80 | — / ~p40 | 53 / 136 | p10 / p90 |
| `COVERAGE_ZERO_COSINE` / `COVERAGE_FULL_COSINE` | 0 / 0.50 | — / ~p85 | 0.23 / 0.57 | p10 / p90 |
| `COHESION_ZERO_COSINE` / `COHESION_FULL_COSINE` | 0 / 0.50 | — / ~p88 | 0.17 / 0.51 | p10 / p90 |
| `EXAMPLE_DEPTH_FULL` | 60 | ~p27 | 84 | **p50** (length-shaped) |
| `READABILITY_BAND` | 8–14 | p10–p78 | 9–14 | p10–p78 (unchanged in substance) |
| `DENSITY_FULL_RATIO_STRICT` | 0.50 | p90 | 0.55 | above p90 |
| `LEXICAL_FULL_MTLD_STRICT` | 100 | ~p65 | 160 | above p90 |

**Two dimensions were repaired rather than re-anchored**, because no threshold could fix
them:

- `Example Quality` now detects demonstrations by heading synonym *or* by a fenced block with
  explanatory prose, and grades richness on a 0/0.5/1 gradient rather than a boolean, so the
  96% that demonstrate something still spread across the range.
- Trigger specificity is scored on `when_to_use` when present and `description` otherwise.

**One guard was tightened.** `Lexical Diversity` was scored from 50 prose tokens; MTLD below
~200 tokens is unstable *and* biased downward (corpus mean 76.3 at 150–300 tokens vs 96.1 at
300–800), so scoring it there penalized a document for being short — a length-neutrality
violation. `LEXICAL_MIN_TOKENS = 200` affects 2 of 207 real skills.

**Tiers were re-anchored to population position**: EXCELLENT ≥ 82 (p90, top decile), GOOD ≥ 73
(p50), FAIR ≥ 61 (p10), POOR ≥ 45 (below the corpus minimum of 48).

## What the data could not justify

An unlabeled corpus reveals where skills sit. It cannot reveal what *should* be valued. The
following were therefore measured and reported but **left unchanged**:

- **Dimension weights** (8/15/6/10/15/13/15/10/8/10). Re-deriving these needs a ground truth
  — either a hand-graded corpus or the benchmark's token-cost outcome — which reintroduces
  exactly the circularity ADR-0003 rejected.
- **Sub-signal mixes** inside dimensions (e.g. `0.6·density + 0.4·(1−dup)`).
- **Link severities** (0.34 / 0.34 / 0.10). Worth recording: across 207 skills there were 59
  broken links and 80 redundant ones, but **zero** case-mismatched and **zero**
  platform-coupled. Those two checks are insurance against a real failure, not
  discriminators on this population.

Three dimensions remain near-constant after calibration, and the honest reading is that they
are violation detectors rather than rankers:

- **`Behavioral Configuration`** — 0.900 for all 15 skills that set any behavioral field, N/A
  for the other 192. Fixing it means touching weights. Out of scope.
- **`Readability`** — real skills genuinely cluster inside the healthy band. The band was not
  narrowed past what the data supports.
- **`Structural Coherence`** — p50 and p90 both at 1.00.

`Metadata & Discovery` improved from σ=0.00 to four distinct levels, but 165 of 207 skills
still score identically, because real descriptions genuinely are homogeneous in trigger
structure. The one property that separates them — an explicit exclusion ("do not use for X")
— appears in **2%** of the corpus. Weighting it heavily is a deliberate incentive: exclusions
are the highest-ROI content per AGENTbench and cost almost nothing in tokens.

## Consequences

**This is a breaking change; the package goes to 2.0.0.** v1 and v2 scores are not
comparable. The corpus median moves from 78 to 73 and the p10–p90 band widens from 18 points
to 21. Anyone running the README's former `--min-score 70` recipe would see roughly half of
all real skills fail; the recommended gate is now 60, which corresponds to the corpus p10.

Calibration is reproducible but **corpus-dependent**: the 207 skills are drawn from one
ecosystem and share authors in places, so the percentiles describe that population, not all
skills everywhere. Re-running `benchmarks/calibrate.py` against a broader corpus is the
intended way to challenge these numbers. No corpus content is committed — only the aggregate
report in `docs/calibration-report.md` and synthetic fixtures authored to sit at the p10 /
p50 / p90 anchors.

The regression guard is `tests/test_calibration.py`, which asserts that calibrated dimensions
produce **more than one value** across the three fixtures. A changed constant is caught by
the band-edge unit tests; a changed code path that silently re-saturates a dimension is
caught by that guard.

# Information Density and Lexical Diversity score healthy bands, not unreachable ceilings

> **Superseded by [ADR-0007](0007-percentile-calibration.md).** The band edges decided here
> (`DENSITY_FULL_RATIO = 0.42`, `LEXICAL_FULL_MTLD = 80`) were reasoned about rather than
> measured. Measurement against 207 real skills placed them at corpus **p25** and roughly
> **p40** — 75% and ~55% of real skills scored full marks, so both dimensions reported a
> near-constant. The argument below for *why* a healthy band beats an unreachable ceiling
> still holds; only the specific numbers were wrong.

`dim_information_density` and `dim_lexical_diversity` are reframed from monotonic
"more-is-always-better" ramps with practically unreachable maxima into **healthy-threshold
bands**, matching the design Readability already uses (full marks for grade 8–14, penalties
on *both* sides). Full marks are now reachable by genuinely dense, varied prose **without
padding**, while thin or repetitive content still falls short.

## Problem: the composite maximum sat outside the feasible region

The two dimensions optimize textual properties that **conflict** with Readability on the
same words:

| Dimension | Maximized by | Effect on bytes |
|---|---|---|
| Information Density | high byte-entropy (rare, varied tokens) | compresses poorly (high `r`) |
| Lexical Diversity (MTLD) | high type/token variety | compresses poorly |
| Readability | short common words, short sentences | compresses well (low `r`) |

`_compression_ratio` returns `len(zlib(level=1)) / len(raw)`. Shannon entropy of English is
~1.0–1.5 bits/char against 8 raw bits, so an ideal compressor reaches `r ≈ 0.15`; zlib level-1
on ~1–2 KB of coherent prose lands at **`r ≈ 0.42–0.46`**. The old target of `0.55` was only
reachable by raising actual per-character entropy (rarer, longer words) — which is the literal
input to Flesch-Kincaid / Gunning-Fog grade level. So pushing Information Density to full
**mechanically lowered Readability**. The all-max corner of the composite was infeasible for
coherent prose; even an EXCELLENT skill in the project's own benchmark topped out at 93–98,
never 100.

Same shape for Lexical Diversity: MTLD of rich technical/academic prose sits at ~80–110, and
the old target of `100` sat at the top of that natural range, so varied prose scored 4–5/6.

## Decision

- **Information Density:** density component scores full at `r ≥ DENSITY_FULL_RATIO (0.42)`,
  ramping from 0 at `r = 0.30`. The duplication component (`0.4 · (1 − dup5)`) is unchanged.
- **Lexical Diversity:** scores full at `MTLD ≥ LEXICAL_FULL_MTLD (80)`, ramping from 0 at
  `MTLD = 30`.

Both thresholds are calibrated empirically to where genuinely dense, non-repetitive,
human-readable skill prose lands (five real coaching skills measured at `r` 0.41–0.44, MTLD
82–107, dup5 0.01–0.06). The lower ramps are retained as a floor, so thin/repetitive content
(which compresses *below* 0.42 and has MTLD *below* 80) is still penalized.

## Why this is not just "making 100 easier"

The change was validated to be **gaming-resistant**. Appending content to a full-scoring
skill lowers its score under the new scorer, because the bands are one-sided plateaus (extra
verbosity cannot push past full) and added filler dilutes the other dimensions:

| feasibility-qa | Total | Info Density | Lexical Diversity |
|---|---|---|---|
| as-is (lean) | **96** | 15/15 | 6/6 |
| + 40× repeated sentence | 85 | 12/15 | 3/6 |
| + 300-word varied word-salad | 84 | 14/15 | 5/6 |

The lean original scores highest. The score maximum now coincides with lean, well-written
content — the opposite of the old incentive, which rewarded entropy-padding that costs the
agent input tokens on every invocation for zero behavioural benefit.

Re-scoring five real skills with **byte-for-byte identical content** (no tokens added):

| Skill | Before | After |
|---|---|---|
| feasibility-qa | 89 | 96 |
| scope-activation | 88 | 94 |
| presales-delivery-roadmap | 86 | 92 |
| impact-summary | 86 | 91 |
| build-map | 82 | 86 |

The recovered points were a ruler artifact, not a content deficit.

## Considered options

- **Two-sided bands (penalize very high `r`/MTLD too).** Rejected for now: very high `r` on a
  skill body means concise/code-like content, already covered by Code Maintainability and
  Readability; a second penalty would be double jeopardy. The one-sided plateau is the
  minimal principled fix.
- **Report a per-dimension profile instead of a 0–100 sum.** Deferred: a larger change to the
  report model. Bands make the existing composite's maximum feasible, which addresses the
  acute problem (100 being unreachable by construction) without restructuring output.
- **Leave as-is and document that ~95 is the real ceiling.** Rejected: the conflicting
  objectives actively incentivize token-costly padding, so the scorer was nudging authors the
  wrong way.

## Consequences

- 100 is now reachable for genuinely excellent, lean skills; the gap to 100 no longer requires
  degrading the artifact.
- Benchmark `HighQuality` arms are largely unchanged (short skills were never density-limited;
  their cap is Example Quality / Behavioral Configuration — a separate, legitimate signal).
- Calibration constants `DENSITY_FULL_RATIO` and `LEXICAL_FULL_MTLD` live at module scope in
  `scorers.py` for one-line re-tuning.

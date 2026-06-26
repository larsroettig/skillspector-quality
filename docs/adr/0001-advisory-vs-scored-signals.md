# Advisory notes carry zero score weight

Optional frontmatter that is genuinely nice-to-have but unrelated to agent token-ROI —
specifically `author` and `version` — is surfaced as an **advisory note** (guidance text on
the dimension's label) and removed from `dim_metadata`'s scored signals entirely, so its
absence neither rewards nor penalizes the score. `when_to_use` stays a **scored signal**
because the AGENTbench finding (Gloaguen et al., 2026) shows its specificity is the
highest-ROI content in a context file.

## Considered options

- Keep `author`/`version` as 0.5-when-absent signals (status quo) — rejected: "neutral
  0.5" still moves the number, since present scores 1.0. The user's requirement was *zero*
  effect.
- Make all optional fields advisory — rejected: would pull `when_to_use` out of the score,
  contradicting the AGENTbench rationale.

## Consequences

Establishes a reusable distinction (`Advisory note` vs `Scored signal` in `CONTEXT.md`)
applied elsewhere — e.g. the missing-TOC check in Progressive Disclosure (ADR-0002) is an
advisory note, while nesting depth is a scored penalty.

# Progressive Disclosure scores appropriate disclosure, not file presence

`dim_progressive_disclosure` is reframed from "are `reference.md` and `examples.md` present
and linked?" to "is content appropriately disclosed given its volume?". It recognizes ANY
supporting doc linked one level deep from SKILL.md (arbitrary filenames and `reference/`
folders), so the official Claude patterns (`pdf-processing` with `FORMS.md`, `bigquery-skill`
with a `reference/` folder) score well instead of being penalized for not using two
hard-coded names.

## Scoring

- **Trigger (line-count based):** body < 100 lines and no supporting docs → N/A (omitted).
  Body > 500 lines → full expectation of disclosure; 100–500 ramps linearly.
- **Scored signals:** body-leanness vs. volume (a 500+ line SKILL.md with no linked docs is
  penalized); depth-≤1 linkedness of supporting docs; a **scored penalty** for any doc
  reachable only at depth ≥2 ("keep references one level deep").
- **Advisory note (zero weight, per ADR-0001):** a supporting doc longer than 100 lines
  without a table of contents.
- **Weight:** raised 5 → 8, sourced from Lexical Diversity 9 → 6; registry total stays 100.

## Boundary with Structural Coherence

Structural Coherence keeps any-depth reachability + acyclicity + heading-tree sanity.
Progressive Disclosure owns depth-1 flatness + body-leanness. A depth-2 file is "reachable"
(Structural is satisfied) yet "nested" (Disclosure penalizes) — an intentional, coherent
split rather than double-counting.

## Why line-count over word-count

Line count matches Anthropic's informal "keep SKILL.md under ~500 lines" guidance and the
existing 100-line floor in the code; word-count was considered but the familiar line
heuristic won for explainability.

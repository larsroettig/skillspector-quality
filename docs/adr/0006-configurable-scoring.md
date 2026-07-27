# Scoring is configurable per dimension and sub-check, with a strict gate

`score_quality` accepts a `ScoringConfig` (`src/skillspector_quality/config.py`) that can
**disable** dimensions/sub-checks or mark them **strict**. Previously every dimension always ran
at a fixed weight with no way to opt out or to fail CI on a specific check.

## Model

- **Ids.** Dimensions are addressed by display name or slug ("Information Density" /
  `information-density`); link sub-checks by dotted id (`link.broken`, `link.platform`,
  `link.redundant`, `link.case-mismatch`). All ids are normalized (lowercase, punctuation → `-`)
  so either form works.
- **Disable.** A disabled dimension is omitted from scoring and its weight renormalizes away —
  identical to the existing N/A-omission path, so disabling never penalizes. A disabled
  sub-check drops its term from `link_valid`.
- **Strict = harder bar + gate.** Strict raises the relevant threshold (e.g. `link.broken`
  severity 0.34→0.50; Information Density `DENSITY_FULL_RATIO` 0.42→0.50; Lexical Diversity
  `LEXICAL_FULL_MTLD` 80→100) AND records a `gate_violation` when the check fails. The CLI exits
  1 on any gate violation, alongside the existing `--min-score` gate.
- **Precedence.** `[tool.skillspector-quality]` in `pyproject.toml` and `.skillspector.toml`
  set project defaults; `--disable` / `--strict` CLI flags union on top. Unknown ids are warned
  and ignored, never fatal.

## Considered options

- **CLI flags only / config file only** — rejected: file gives reproducible project defaults,
  flags give per-run overrides; both together is the least surprising.
- **Threshold-shift only (no gate) / gate only (no shift)** — rejected: authors wanted both a
  harder score signal *and* the ability to fail CI on a specific defect (a broken link).
- **Per-dimension only (no sub-checks)** — rejected: broken-link detection must be independently
  toggleable from redundant-link detection.

## Consequences

- `ScorerFn` signature is now `(doc, w, config)` (config optional, defaults to an empty config),
  so direct callers and tests passing `(doc, w)` keep working.
- `QualityReport` gains `gate_violations`; JSON/markdown/terminal renderers surface it.
- The config object is threaded CLI → graph `state["scoring_config"]` → `quality_scorer` node →
  `score_quality`, in-process (not serialized).

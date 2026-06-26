---
name: skillspector-quality
description: Scores the authoring quality of Claude Code skill bundles. Analyzes SKILL.md and supporting documentation across ten deterministic dimensions — metadata completeness, information density, lexical diversity, readability, topic coverage, structural coherence, code maintainability, example quality, progressive disclosure, and behavioral configuration — and returns a 0–100 score with per-dimension breakdowns.
when_to_use: Use when you need to evaluate or improve a Claude Code skill bundle before publishing. Invoke after writing a new skill to verify it meets quality thresholds, or in CI to gate merges on a minimum score. Do not use to validate skill correctness or functional behavior — this tool measures structure and completeness, not whether the skill produces correct outputs.
metadata:
  author: Lars Roettig
  version: 1.1.0
---

# SkillSpector Quality

Deterministic authoring quality scorer for Claude Code skills. Rates `SKILL.md` bundles from 0 to 100 across ten dimensions using information theory, readability metrics, TF-IDF topic modeling, link-graph analysis, and code maintainability metrics. No LLM calls required — every score is byte-identical across runs.

## Overview

SkillSpector Quality adds a quality assessment layer on top of SkillSpector's security scan. It reads the same file cache built by `resolve_input` and passes it through ten independent scoring dimensions. The final score is a weighted sum, normalized so that omitted dimensions (for example, code maintainability when no scripts are present) do not penalize the skill.

## Dimensions

Each dimension returns a list of `(earned, max, label)` tuples. Dimensions that do not apply return an empty list and are excluded from the weight denominator.

| Dimension | Weight | What it measures |
|---|---|---|
| Metadata & Discovery | 8 | Completeness and specificity of frontmatter fields |
| Information Density | 15 | Compression ratio and n-gram duplication |
| Lexical Diversity | 6 | MTLD score across all prose |
| Readability | 10 | Ensemble of five readability formulas |
| Topic Coverage | 15 | TF-IDF cosine alignment between description and body |
| Structural Coherence | 13 | Heading hierarchy correctness and link-graph reachability |
| Code Maintainability | 15 | Radon MI, cyclomatic complexity, docstring coverage |
| Example Quality | 10 | Input/output pairing richness and section depth |
| Progressive Disclosure | 8 | Supporting docs linked at depth 1 from SKILL.md |
| Behavioral Config | 10 | Validity of frontmatter behavioral/execution fields |

## Installation

```bash
pip install -e ../SkillRater   # install skillspector (not on PyPI)
pip install -e .               # install skillspector-quality
```

For development:

```bash
uv sync --extra dev
uv run pytest
```

## Usage

```bash
skillspector-quality scan ./my-skill --no-llm
skillspector-quality scan ./my-skill --format json
skillspector-quality scan ./my-skill --min-score 75
```

The `--min-score` flag exits with code 1 if the quality score falls below the threshold, suitable for CI gates.

## Scoring

The score is computed deterministically:

1. Each dimension scorer receives the parsed `SkillDoc` and its weight.
2. It returns `[(earned, max, label), ...]` or `[]` for N/A.
3. The engine sums `earned` and `max` across all applicable dimensions.
4. `score = round(100 * total_earned / total_max)`.

The score measures structural quality and completeness — not content correctness. A perfect score does not guarantee the skill behaves correctly against real-world inputs.

## Output Formats

| Format | Description |
|---|---|
| `terminal` | Rich terminal report combining security and quality sections |
| `json` | JSON object with `quality_assessment` alongside the security `risk_assessment` |
| `markdown` | Markdown section appended to the security report body |
| `sarif` | SARIF with quality metrics in `runs[0].properties.quality` |

## Architecture

See [reference](reference.md) for the full dimension specification and [examples](examples.md) for scored SKILL.md samples with annotated breakdowns.

The graph adds a `quality_scorer` node that runs in parallel with the upstream security analyzers after `build_context`. It terminates at `END` independently, so the security `report` node's predecessor count stays at one and is not triggered twice.

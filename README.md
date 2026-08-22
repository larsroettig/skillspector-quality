# skillspector-quality

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13383/badge)](https://www.bestpractices.dev/projects/13383)

<img width="1584" height="672" alt="Firefly_The image, watermarked_img_3618978183344880806 png, features a modern, futuristic cor 275505" src="https://github.com/user-attachments/assets/26dacee1-5400-4f15-9a10-e062002e8a84" />


> **Proposal.** This project is in active development and welcomes community input.
> PRs, new dimensions, weight-adjustment proposals, and CI recipes are all appreciated —
> see [CONTRIBUTING.md](CONTRIBUTING.md).

A **quality rating layer** for [SkillSpector](https://github.com/NVIDIA/skillspector).

SkillSpector answers *"is this skill safe?"* (a security **risk** score, 0 = safe, 100 = dangerous).  
This tool adds the complementary question *"is this skill well-crafted?"* — a deterministic **quality score** from 0–100 (higher = better), shown right next to the security report in a single unified output.

It is a **standalone package**: it imports `skillspector` read-only and never modifies it, so upstream syncs stay trivial.

**Goal:** help teams write skills that are simultaneously **secure** (low risk score from SkillSpector),
**cost-efficient** (minimal redundant prose that inflates agent token spend), and **well-documented**
(clear trigger conditions so agents invoke them correctly).
The scoring dimensions are grounded in peer-reviewed research; see [Research basis](#research-basis).

---

## Table of contents

- [How it works](#how-it-works)
- [What this measures — and what it does not](#what-this-measures--and-what-it-does-not)
- [Quick start](#quick-start)
- [CI/CD integration](#cicd-integration)
  - [GitHub Actions — fail PR if score is too low](#github-actions--fail-pr-if-score-is-too-low)
  - [GitHub Actions — comment score on every PR](#github-actions--comment-score-on-every-pr)
  - [GitLab CI](#gitlab-ci)
  - [Exit codes](#exit-codes)
- [Output formats](#output-formats)
- [Quality dimensions — math details](#quality-dimensions--math-details)
  - [Score formula](#score-formula)
  - [1. Metadata & Discovery](#1-metadata--discovery)
  - [2. Information Density](#2-information-density)
  - [3. Lexical Diversity](#3-lexical-diversity)
  - [4. Readability](#4-readability)
  - [5. Topic Coverage](#5-topic-coverage)?
  - [6. Structural Coherence](#6-structural-coherence)
  - [7. Code Maintainability](#7-code-maintainability)
  - [8. Example Quality](#8-example-quality)
  - [9. Progressive Disclosure](#9-progressive-disclosure)
  - [10. Instruction Clarity](#10-instruction-clarity)
  - [11. Behavioral Configuration](#11-behavioral-configuration)
- [Token cost — a separate axis](#token-cost--a-separate-axis)
- [Research basis](#research-basis)
- [Install](#install)
  - [Homebrew](#homebrew-recommended-for-users)
  - [Releasing](#releasing)
- [Docker](#docker)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## How it works

`skillspector_quality` rebuilds SkillSpector's LangGraph pipeline in its own graph, importing
the upstream nodes and analyzer registry, and inserts one extra `quality_scorer` node that
runs **in parallel** with the security analysis:

```
Input path
    │
    ├─── [SkillSpector security nodes] ──► risk_score / findings
    │
    └─── [quality_scorer node]        ──► quality_score / categories
    │
    └─── unified terminal report
```

**Key design properties:**

- **Deterministic.** The 0–100 score is a pure function of the skill's files — identical results
  with or without an LLM, across runs, across machines.
- **LLM is advisory only.** When an LLM is configured it adds short prose suggestions per
  category. With `--no-llm` or no API key the score is unchanged; notes are simply omitted.
- **Length-neutral.** Every content metric is a ratio or a length-invariant statistic.  
  The scorer penalizes *redundancy, low information density, poor structure, and incoherence* —
  never size. More genuinely useful content always helps.
- **N/A dimensions.** A dimension that does not apply (e.g. no scripts → Code Maintainability
  is N/A) is omitted from the denominator, so its weight renormalizes away automatically.

---

## What this measures — and what it does not

**This tool scores how well-*formed* a skill is, not whether it actually *works*.**

### The "high score illusion"

Deterministic grading is good at measuring what can be parsed: clear boundaries and
parameters, a defined persona/context, explicit constraints ("output JSON", "under 500
words"), and the absence of syntax errors or contradictory formatting. When those structural
elements are present, a skill scores high — even if it commands the model to do something
illogical, impossible, or conceptually flawed. A structurally perfect prompt can still be
logically broken, and that leads straight to confusion and hallucination.

The real danger is **false confidence**: a developer who sees `95/100` intuitively reads it as
"ready for production." If the tool isn't explicit about what the number means, that creates a
blind spot where structurally perfect but logically broken skills ship to users. Structural
scoring is **step one**; runtime testing and semantic validation against real inputs is
**step two** — the score never replaces it.

### Why, dimension by dimension

Every dimension is a measure of form, structure, or style — none of them can verify that the
skill's instructions are *correct*. Content-correctness cannot be measured deterministically,
so a skill can earn a high score and still be wrong in ways that lead an agent into confusion
or hallucination. Concretely:

- **Topic Coverage** checks that the description and body share vocabulary (TF-IDF cosine) —
  not that the description is *accurate* or the instructions are *right*.
- **Code Maintainability** measures how clean the code *looks* (radon MI / complexity /
  docstrings) — a tidy, well-documented function can still be silently buggy.
- **Information Density, Lexical Diversity, Readability** reward non-redundant, varied, readable
  prose — confident but *incorrect* instructions score just as well as correct ones.
- **Structural Coherence, Example Quality, Progressive Disclosure** check that content is
  linked, headed, and paired — not that the example outputs are what the code actually produces.

A high score means a skill is **clear, well-structured, and cheap for an agent to consume** —
a necessary but *not sufficient* condition for quality. Treat it as a linter for craft, not a
correctness oracle. Validating that a skill *does the right thing* still requires human review
and real-world testing. (The optional LLM commentary can surface some content concerns, but it
is advisory, off by default, non-deterministic, and never affects the score.)

---

## Quick start

```bash
python -m skillspector_quality scan ./my-skill/
python -m skillspector_quality scan ./my-skill/ --no-llm
python -m skillspector_quality scan ./my-skill/ --format json
python -m skillspector_quality scan ./my-skill/ --min-score 60    # exit 1 if score < 60
```

Sample terminal output:

```
╭──────────────────────────────────────────────────────────────────────╮
│ SkillSpector Report                                                  │
│ Skill:   pdf-processing                                              │
│ Source:  ./my-skill/                                                 │
│ Scanned: 2026-06-14 10:23:41 UTC                                     │
╰──────────────────────────────────────────────────────────────────────╯

 Overview
 ──────────────────────────────────────────────────────────────────────
 Dimension    Risk Score   Status
 ──────────────────────────────────────────────────────────────────────
 Security      5/100        LOW  NO_ACTION_NEEDED
 Quality       18/100       GOOD  REVIEW RECOMMENDED
 ──────────────────────────────────────────────────────────────────────
 Risk Score: 0 = best  ·  100 = worst

 Quality Dimensions
   +  8/8   Metadata & Discovery
              All fields complete
   ~ 10/15  Information Density
              Content is dense and non-repetitive
   + 10/10  Readability
              Reading level: 11th grade — good for technical documentation
   ~  9/15  Topic Coverage
              Description partially matches skill content — refine it to better reflect actual functionality
   + 13/13  Structural Coherence
              Heading structure is correct; all files are linked
   ~  7/10  Example Quality
              2 example(s) with clear before/after or input/output pairs
   +  5/5   Progressive Disclosure
              Full doc structure: examples.md and reference.md are linked
```

---

## CI/CD integration

The tool is designed to slot into any CI/CD pipeline as a quality gate on skill files.
It exits `0` when checks pass and `1` when a gate fails, making it composable with any
CI system that reads exit codes.

### GitHub Actions — fail PR if score is too low

Create `.github/workflows/skill-quality.yml`:

```yaml
name: Skill Quality Gate

on:
  pull_request:
    paths:
      - 'skills/**'          # adjust to your skill directory layout
      - '**SKILL.md'

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install skillspector-quality
        run: |
          # skillspector is not on PyPI — install from your internal registry
          # or a pinned wheel, then install this package on top.
          pip install skillspector==2.4.4          # adjust to your source
          pip install skillspector-quality

      - name: Find changed skill directories
        id: skills
        run: |
          # Collect every SKILL.md that changed in this PR
          SKILLS=$(git diff --name-only origin/${{ github.base_ref }}...HEAD \
            | grep 'SKILL\.md' \
            | xargs -I{} dirname {} \
            | sort -u \
            | tr '\n' ' ')
          echo "dirs=$SKILLS" >> $GITHUB_OUTPUT

      - name: Run quality scan
        if: steps.skills.outputs.dirs != ''
        run: |
          FAIL=0
          for skill_dir in ${{ steps.skills.outputs.dirs }}; do
            echo "Scanning $skill_dir"
            python -m skillspector_quality scan "$skill_dir" \
              --no-llm \
              --format terminal \
              --min-score 60 || FAIL=1
          done
          exit $FAIL

      - name: No skills changed
        if: steps.skills.outputs.dirs == ''
        run: echo "No SKILL.md files changed — skipping quality scan."
```

This workflow:
- triggers only when skill files change (saves CI minutes)
- scans every modified skill directory in the PR
- fails the check if any skill scores below 70
- runs without an LLM (`--no-llm`) for deterministic, zero-cost CI runs

### GitHub Actions — comment score on every PR

A richer workflow that posts the full quality report as a PR comment:

```yaml
name: Skill Quality Report

on:
  pull_request:
    paths:
      - 'skills/**'
      - '**SKILL.md'

permissions:
  pull-requests: write

jobs:
  quality-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install
        run: |
          pip install skillspector==2.4.4
          pip install skillspector-quality

      - name: Find changed skills
        id: skills
        run: |
          SKILLS=$(git diff --name-only origin/${{ github.base_ref }}...HEAD \
            | grep 'SKILL\.md' | xargs -I{} dirname {} | sort -u | tr '\n' ' ')
          echo "dirs=$SKILLS" >> $GITHUB_OUTPUT

      - name: Scan and collect reports
        id: scan
        if: steps.skills.outputs.dirs != ''
        run: |
          OVERALL=0
          COMMENT="## Skill Quality Report\n\n"
          for skill_dir in ${{ steps.skills.outputs.dirs }}; do
            # JSON output so we can extract the score
            REPORT=$(python -m skillspector_quality scan "$skill_dir" \
              --no-llm --format json 2>/dev/null || true)
            SCORE=$(echo "$REPORT" | python -c \
              "import sys,json; d=json.load(sys.stdin); print(d.get('quality_assessment',{}).get('score','?'))")
            RISK=$(echo "$REPORT" | python -c \
              "import sys,json; d=json.load(sys.stdin); print(d.get('risk_assessment',{}).get('risk_score','?'))")
            COMMENT+="### \`$skill_dir\`\n"
            COMMENT+="| | Score |\n|---|---|\n"
            COMMENT+="| Quality | **$SCORE / 100** |\n"
            COMMENT+="| Security Risk | **$RISK / 100** |\n\n"
            # Fail if quality < 70 or security risk > 50
            if [ "$SCORE" -lt 70 ] 2>/dev/null; then
              COMMENT+="⚠️ Quality is below the 70-point threshold.\n\n"
              OVERALL=1
            fi
            if [ "$RISK" -gt 50 ] 2>/dev/null; then
              COMMENT+="🚨 Security risk exceeds threshold.\n\n"
              OVERALL=1
            fi
          done
          # Write to file to avoid shell quoting issues
          printf "%b" "$COMMENT" > /tmp/pr_comment.md
          echo "exit_code=$OVERALL" >> $GITHUB_OUTPUT

      - name: Post PR comment
        if: steps.skills.outputs.dirs != ''
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('/tmp/pr_comment.md', 'utf8');
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body,
            });

      - name: Enforce gate
        if: steps.scan.outputs.exit_code == '1'
        run: exit 1
```

### GitLab CI

```yaml
skill-quality:
  stage: test
  image: python:3.13-slim
  rules:
    - changes:
        - skills/**
        - "**SKILL.md"
  script:
    - pip install skillspector==2.4.4 skillspector-quality
    - |
      FAIL=0
      for skill_dir in $(git diff --name-only origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD \
          | grep 'SKILL\.md' | xargs -I{} dirname {} | sort -u); do
        python -m skillspector_quality scan "$skill_dir" --no-llm --min-score 60 || FAIL=1
      done
      exit $FAIL
  artifacts:
    when: always
    paths:
      - skill-quality-*.json
```

For JSON artifacts per skill, add `--output skill-quality-${skill_dir//\//-}.json --format json`
to the scan command.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | All gates passed |
| `1` | Security risk score > 50 **or** quality score < `--min-score` |
| `2` | Scan error (file not found, parse failure, etc.) |

The security risk gate always takes priority — a dangerous skill exits `1` even when `--min-score`
is not set. The quality gate is **opt-in** via `--min-score`.

---

## Output formats

| Flag | Use case |
|------|---------|
| `--format terminal` (default) | Human-readable report with color |
| `--format json` | Machine-readable; parse `quality_assessment.score` |
| `--format markdown` | Append to security markdown report |
| `--format sarif` | SARIF 2.1 with quality in `runs[0].properties.quality` |

**JSON structure:**

```json
{
  "risk_assessment": {
    "risk_score": 5,
    "risk_severity": "LOW"
  },
  "quality_assessment": {
    "score": 82,
    "categories": [
      { "name": "Metadata & Discovery", "earned": 8,  "max": 8,  "label": "All fields complete" },
      { "name": "Information Density",  "earned": 10, "max": 15, "label": "Content is dense and non-repetitive" },
      { "name": "Lexical Diversity",    "earned": 7,  "max": 10, "label": "Vocabulary is rich and varied (412 words)" }
    ]
  }
}
```

---

## Quality dimensions — math details

### Score formula

Each dimension returns a list of `(earned, max, label)` triples. A dimension that does not apply
returns an empty list; its weight is excluded from both numerator and denominator:

```
final_score = round(100 × Σ earned_i / Σ max_i)   for all applicable dimensions i
```

This means N/A dimensions neither reward nor punish — they simply renormalize away. For example,
a skill with no scripts excludes Code Maintainability (weight 15) entirely; the remaining
dimensions divide up the full 100 points.

---

### Calibration and score tiers

**Every band edge below is anchored to a measured corpus, not chosen by hand.**
`benchmarks/calibrate.py` scores a directory tree of skills and reports aggregate statistics
only — percentiles, correlations, counts, never names or content — so a private corpus can be
measured without disclosing it:

```bash
python benchmarks/calibrate.py ~/.claude              # markdown report to stdout
python benchmarks/calibrate.py ./skills -o cal.md     # or to a file
```

Run against 207 real skills, the score distribution is **p10 = 61, p50 = 73, p90 = 82**
(min 48, max 89, σ 8.5). Tiers are anchored to that distribution, so a tier means a *population
position* rather than an arbitrary number:

| Tier | Score | Meaning |
|---|---|---|
| **EXCELLENT** | ≥ 82 | top decile (corpus p90) |
| **GOOD** | ≥ 73 | above the median skill (p50) |
| **FAIR** | ≥ 61 | above the bottom decile (p10) |
| **POOR** | ≥ 45 | below anything in the corpus (min = 48) |
| **CRITICAL** | < 45 | — |

For CI, `--min-score 60` is the recommended gate: it corresponds to roughly the corpus p10, so
it fails genuinely weak skills without failing half the population.

> **Upgrading from 1.x:** v1 and v2 scores are **not comparable**. The v1 thresholds were
> hand-picked and measurement showed several sat at the wrong end of the distribution — the
> scorer reported a near-constant instead of ranking. Expect existing scores to move by roughly
> 5–10 points, and re-check any `--min-score` gate: the old README recommended 70, which under
> v2 would fail about half of all real skills. Full analysis in
> [ADR-0007](docs/adr/0007-percentile-calibration.md); the measured distribution is committed at
> [docs/calibration-report.md](docs/calibration-report.md).

---

### 1. Metadata & Discovery

**Weight: 8** — Measures frontmatter completeness per the [official skill spec](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

Only `name` and `description` are **required** by the spec. `author` and `version` are
**advisory** ([ADR-0001](docs/adr/0001-advisory-vs-scored-signals.md)): surfaced as guidance,
never scored, so their absence cannot lower the score.

**Trigger specificity is scored on `when_to_use` when present, and on `description` otherwise.**
Across a 207-skill corpus, `when_to_use` appeared in **zero** skills while `description`
appeared in all 207 — authors write their triggers inside the description ("Use when the user
wants to…", "Do not use for…"). Scoring only the unused field made this dimension return exactly
0.875 for every skill: eight points that could not rank anything
([ADR-0007](docs/adr/0007-percentile-calibration.md)).

Research ([Gloaguen et al., 2026](#research-basis)) found that concrete trigger conditions and
explicit exclusions ("Do not use for X") are the highest-ROI content in agent context files.
Exclusions appear in just **2 %** of real skills, which is why they carry the heaviest weight
here — it is a deliberate incentive toward the cheapest, most valuable content available.

```
trigger = when_to_use if set else description

signals = [
  desc_score,      # 1.0 if 0 < len(description) ≤ 1024, else 0.0            (required)
  when_score,      # specificity(trigger):
                   #   0.00 if absent · 0.15 if shorter than 15 chars
                   #   +0.30 for a trigger verb (use/invoke/trigger/call/…)
                   #   +0.20 for situational framing (when/if/while/after/before)
                   #   +0.30 for an exclusion condition (do not/never/skip/avoid/…)
                   #   +0.20 × clamp((distinct trigger clauses − 1) / 3)
  name_score,      # 1.0 if name matches [a-z0-9]+(-[a-z0-9]+)*, else 0.0    (required)
]

s = mean(signals)
earned = round(8 × s)
```

**Length is a floor, never a bonus.** The previous version awarded +0.30 for `len ≥ 15` and
+0.10 for `len > 80`; those fired for 100 % and 99 % of real descriptions, contributing a
constant while creating an incentive to inflate the most token-sensitive text in the system —
descriptions load for *every* skill in *every* session.

---

### 2. Information Density

**Weight: 15** — Measures how much unique information the prose carries.

Weight raised from 12 to reflect the finding that redundant prose in agent context files
inflates token cost by 20–23 % with no improvement in task success ([Gloaguen et al., 2026](#research-basis)).

Two sub-metrics:

**Compression ratio (density)** — the ratio of the gzip-compressed size to the original, used
as a proxy for information entropy. Dense, varied prose compresses poorly (high ratio = good);
repetitive prose compresses well (low ratio = bad):

```
r = len(gzip(prose)) / len(prose)

density = clamp((r - 0.38) / (0.50 - 0.38), 0, 1)
```

The anchors are **measured, not chosen**: 0.38 and 0.50 are the p10 and p90 of the compression
ratio across a 207-skill corpus ([ADR-0007](docs/adr/0007-percentile-calibration.md),
[full report](docs/calibration-report.md)). The previous 0.42 full-marks threshold sat at the
corpus **p25** — 75 % of real skills scored full marks, so the dimension reported a near-constant.
Compression ratio is length-invariant, so this cannot be raised by writing more.

**5-gram duplication** — the fraction of 5-word n-grams that have appeared before in the same
document, detecting copy-paste repetition:

```
dup = |{g ∈ 5-grams(tokens) : seen_before(g)}| / max(1, |5-grams(tokens)|)
```

Combined score:

```
s = 0.6 × density + 0.4 × (1 - dup)
earned = round(15 × s)
```

---

### 3. Lexical Diversity

**Weight: 6** — Measures vocabulary richness in a way that does not inflate with document
length (unlike the naive Type-Token Ratio, which always decreases as documents grow longer).

**MTLD (Measure of Textual Lexical Diversity)** — iterates forward through the token stream,
tracking the running TTR. Every time TTR drops to the threshold 0.72, the segment is counted
and a new segment starts. MTLD = total tokens / segment count. Values above ≈ 100 indicate
genuinely diverse vocabulary; below ≈ 30 indicates heavy repetition:

```python
# Simplified MTLD forward pass
def _one_pass(tokens, threshold=0.72):
    types, count, segments = set(), 0, 0.0
    for tok in tokens:
        types.add(tok); count += 1
        if len(types) / count <= threshold:
            segments += 1; types = set(); count = 0
    if count > 0:
        # Partial segment: count fractionally
        segments += 1 - (len(types)/count - threshold) / (1 - threshold)
    return len(tokens) / max(1, segments)

mtld = mean(_one_pass(tokens), _one_pass(reversed(tokens)))
```

HD-D (hypergeometric distribution diversity) is also computed as a cross-check but the score
uses MTLD as the primary signal:

```
s = clamp((mtld - 53) / (136 - 53), 0, 1)
earned = round(6 × s)
```

The anchors are the corpus p10 and p90 ([ADR-0007](docs/adr/0007-percentile-calibration.md)).
The previous full-marks threshold of 80 sat at roughly p40, so over half of all real skills
scored full marks.

**N/A condition:** fewer than **200** prose tokens. Below ~200 tokens MTLD is not merely noisy
but *biased downward* (corpus mean 76.3 at 150–300 tokens vs 96.1 at 300–800), so scoring it
there would penalize a document for being short — a length-neutrality violation. Real skills sit
far above this floor: corpus p10 is 431 prose tokens.

---

### 4. Readability

**Weight: 10** — Measures whether the writing difficulty matches the intended audience. The
optimal range for technical documentation is **8–14th grade**: accessible enough for a broad
audience, substantive enough to convey technical content.

An ensemble of five formulas is computed and the **median** grade is used — this is more robust
than any single formula because each has different sensitivity to sentence length vs. syllable
count vs. word frequency:

| Formula | Key factors |
|---------|-------------|
| Flesch-Kincaid Grade Level | sentence length, syllables/word |
| Gunning Fog Index | sentence length, complex words (≥ 3 syllables) |
| SMOG Index | complex words in sample of 30 sentences |
| Automated Readability Index | characters/word, words/sentence |
| Coleman-Liau Index | characters/word (no syllable counting) |

Scoring against the sweet spot:

```
if 9 ≤ grade ≤ 14:    s = 1.0
elif grade < 9:        s = clamp((grade - 4) / 5, 0, 1)   # too simple
else:                  s = clamp((22 - grade) / 8, 0, 1)  # too complex

earned = round(10 × s)
```

Measurement note: real skills genuinely cluster inside this band (corpus p10 = 9.1, p75 = 13.3),
so Readability behaves as a **violation detector** rather than a discriminator — it catches the
tails without ranking the middle. The band was deliberately *not* narrowed further than the data
supports ([ADR-0007](docs/adr/0007-percentile-calibration.md)).

**N/A condition:** fewer than 30 words of prose after stripping code fences and front matter.

---

### 5. Topic Coverage

**Weight: 15** — Measures whether the description accurately reflects what the skill does, and
whether supporting documents are topically consistent with the skill body.

Uses **TF-IDF cosine similarity** with a small corpus built from the skill's own files
(description, body, each linked document). Building IDF from the skill bundle rather than an
external corpus ensures that terms that are distinctive *within this skill* (not globally rare)
get appropriate weight:

```
corpus = [body_terms] + [terms(doc) for doc in markdown_docs.values()]
idf(t) = log((1 + |corpus|) / (1 + df(t))) + 1      # smoothed, avoids zero

tfidf_vec(terms, idf) = {t: count(t) × idf(t) for t in terms}
cosine(u, v) = dot(u, v) / (|u| × |v|)
```

Coverage score (description ↔ body alignment):

```
coverage = cosine(tfidf(desc), tfidf(body))
cov_norm  = clamp((coverage - 0.23) / (0.57 - 0.23), 0, 1)
```

The anchors are the corpus p10 and p90 of description↔body cosine
([ADR-0007](docs/adr/0007-percentile-calibration.md)). Coverage and cohesion previously shared a
single hand-picked reference of 0.5; they are now anchored separately, because a terse
description shares less TF-IDF mass with the body (p90 = 0.57) than two full documents share
with each other (p90 = 0.51 for cohesion, over a lower baseline).

When supporting docs exist, cohesion (body ↔ each supporting doc) is blended in:

```
if supporting_docs:
    cohesion = mean(cosine(tfidf(body), tfidf(doc)) for doc in docs)
    s = 0.5 × cov_norm + 0.5 × clamp(cohesion / 0.5, 0, 1)
else:
    s = cov_norm

earned = round(15 × s)
```

---

### 6. Structural Coherence

**Weight: 13** — Two independent sub-checks: heading tree well-formedness and link-graph
reachability.

**Heading tree:** Extracts `#`-level markers from the body, counts *level skips* (transitions
where the next heading level increases by more than 1, e.g. H2 → H4), and checks for exactly
one H1 title:

```
skips       = count(b - a > 1 for consecutive levels a, b)
transitions = len(levels) - 1
s_head      = (1 - skips/transitions) × (0.5 if h1_count ≠ 1 else 1.0)
```

**Link graph:** Builds a directed graph where SKILL.md and each linked file are nodes, and
markdown links are edges. Computes reachability from SKILL.md (BFS) and checks acyclicity
(DFS with grey/white/black coloring):

```
reach  = |nodes reachable from SKILL.md| / |all nodes|
acyclic = 1.0 if no back-edges else 0.0
```

Combined:

```
s = 0.5 × s_head + 0.4 × reach + 0.1 × acyclic
earned = round(13 × s)
```

---

### 7. Code Maintainability

**Weight: 15** — Evaluated only when the skill bundle includes scripts. N/A otherwise.

For each Python script, three metrics are computed via [`radon`](https://radon.readthedocs.io/):

**Maintainability Index (MI)** — a composite score (0–100) derived from Halstead volume,
cyclomatic complexity, and lines of code, calibrated so that 100 = trivially maintainable,
0 = impossible to maintain. Radon classifies MI > 20 as maintainable:

```
MI = max(0, 100 × (
    171
    - 5.2 × ln(Halstead volume)
    - 0.23 × cyclomatic_complexity
    - 16.2 × ln(lines_of_code)
) / 171)
```

**Average cyclomatic complexity (CC)** — average McCabe complexity per function. Each
decision point (if, for, while, try, etc.) adds 1. Lower is better; CC > 10 per function is
considered high:

```
cc_penalty = clamp((avg_cc - 5) / 20, 0, 1)
```

**Docstring coverage** — fraction of functions/classes/modules with docstrings (via `ast`):

```
docstring_cov = |items with docstring| / max(1, |all items|)
```

Per-script score:

```
s_py = 0.5 × clamp(MI/100, 0, 1) + 0.3 × (1 - cc_penalty) + 0.2 × docstring_cov
```

For non-Python scripts (shell, JS, etc.) a heuristic based on file size, line length, and
comment density is used instead.

Final score:

```
s = mean(s_py for each script)
earned = round(15 × s)
```

---

### 8. Example Quality

**Weight: 10** — Checks that the skill concretely demonstrates itself, and how well.

**Detection.** A section counts as a demonstration when its heading *names* it one
(Example / Usage / Sample / Walkthrough / Scenario / Demo / Recipe / Quick start), **or** when it
carries a fenced code block with at least 5 words of explanatory prose around it. Both paths
matter: measured over 207 real skills, the previous `^#{2,3}\s+Example` regex matched **10 %**
while **96 %** demonstrated usage via code fences — so the dimension scored over 90 % of real
skills at zero and was measuring one heading word, not the presence of examples
([ADR-0007](docs/adr/0007-percentile-calibration.md)).

**Richness** is a gradient, not a boolean — a gate would simply re-saturate at the other end:

| Richness | Condition |
|---|---|
| **1.0** | two or more code blocks, or explicit `input`/`output` or `before`/`after` framing |
| **0.5** | a single code block with explanatory prose |
| **0.0** | a heading promising an example that shows nothing concrete |

```
demos     = heading-named sections ∪ fenced sections with prose
richness  = mean(richness(d) for d in demos)
depth     = clamp(median_token_count(demos) / 84, 0, 1)

s = 0.6 × richness + 0.4 × depth
earned = round(10 × s)
```

The depth anchor of 84 is the corpus **median**, not the p90 of 191. Depth is a raw word count —
anchoring it at p90 would reward padding examples, and padding costs runtime tokens on every
invocation. Length-shaped signals get median anchors; length-invariant ones get p90.

If no demonstration is found anywhere in the bundle:

- **N/A** when body < 100 words — minimal skills are not expected to have worked examples
- **0/10** when body ≥ 100 words — substantial skills should show at least one worked case

---

### 9. Progressive Disclosure

**Weight: 8** — Checks whether content is appropriately disclosed given its volume.

Weight lowered from 7: research shows that linking more files causes agents to load and process
additional content regardless of relevance, increasing token spend without proportional task gains.
Having `examples.md` and `reference.md` is still rewarded, but the signal is weighted less
heavily than information density and specificity.

The [official best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#progressive-disclosure-patterns)
recommend splitting content into `reference.md` and `examples.md` only when SKILL.md body
exceeds ~100 lines. This dimension reflects that:

- **N/A** when body < 100 lines and neither `reference.md` nor `examples.md` exists — a concise
  skill follows best practices by staying in a single file
- **Scored** when supporting files exist or the body is long enough to warrant them

For each supporting file:

```
val = 1.0 if (present in file cache AND linked from SKILL.md)
    = 0.5 if (present but not linked)
    = 0.0 if (absent and body ≥ 100 lines)

s = mean(val for each of reference.md, examples.md)
earned = round(5 × s)
```

---

### 10. Behavioral Configuration

### 10. Instruction Clarity

**Weight: 8** — Measures how directly the prose tells an agent what to do.

**Hedging density** — vague filler per 100 prose words. AGENTbench found this class of prose
is precisely what makes context files cost tokens without improving task success:

```
hedge_density = 100 × |hedge words| / |prose words|     # "appropriate", "as needed",
                                                        # "etc.", "various", "consider"
s_hedge = clamp(1 − hedge_density / 0.50, 0, 1)         # 0.50 is corpus p90
```

**Untagged code fences** — a fence with no language tag makes an agent guess whether a block is
shell, JSON, or expected output:

```
s_fence = clamp(1 − untagged_ratio / 0.89, 0, 1)        # 0.89 is corpus p90

earned = round(8 × mean(s_hedge, s_fence))
```

Both signals are "lower is better" and bottom out at a genuine zero, so they anchor
**full-marks-at-0 / zero-at-p90** rather than the usual p10/p90 ramp. Hedge density is a ratio,
so padding around the filler cannot dilute it.

**N/A condition:** fewer than 50 prose words *and* no code fences — nothing to judge.

---

### 11. Behavioral Configuration

**Weight: 10** — Evaluated only when any of the 13 behavioral frontmatter fields appear in
the skill. N/A for skills that use only the two required fields (`name`, `description`).

The 13 fields are validated in four groups:

| Group | Fields | Weight share |
|-------|--------|-------------|
| Agent discovery | `paths`, `user-invocable`, `arguments`, `argument-hint` | 30% |
| Tool restrictions | `allowed-tools`, `disallowed-tools`, `disable-model-invocation` | 40% |
| Execution settings | `context`, `agent`, `effort`, `shell`, `model` | 20% |
| Lifecycle hooks | `hooks` | 10% |

Within each group, absent optional fields score 0.5 (neutral). Invalid values (wrong type,
bad enum, etc.) score 0.0. Valid values score 1.0. Special coherence rules:

- `argument-hint` is **required** when `arguments` is set (0.0 if missing)
- `agent` is **recommended** when `context: fork` (0.0 if missing — forks should declare intent)
- `effort` must be one of `low | medium | high | xhigh | max`
- `shell` must be `bash | powershell`
- `context` must be `fork` (the only currently valid value)

---

## Token cost — a separate axis

The tool reports **three independent scores**: security risk, quality, and token cost.

Cost is not folded into the quality score because measurement says they are orthogonal —
across 207 real skills the two correlate at only **+0.14**. Blending them would collapse a
cheap sloppy skill and a polished bloated one onto the same number. It also keeps the
**length-neutral** promise intact on the quality axis, so *"excellent but expensive"* becomes
something the tool can actually say.

### Why tiers, not raw tokens

A token's lifetime cost depends on how often it is loaded, and the tiers differ by orders of
magnitude:

| Tier | What | Corpus p50 | Weight |
|------|------|-----------:|--------|
| **always-on** | `description` — loaded for **every** skill in **every** session | 76 tok | 1.0 |
| **on-invoke** | `SKILL.md` body — loaded when the skill fires | 1,502 tok | `RATE` |
| **on-demand** | supporting docs and scripts — only if the agent reads them | 3,960 tok | `RATE × READ` |

The weights are **derived from two stated assumptions** rather than hard-coded as a ratio, so
the premise is arguable instead of buried:

```python
ASSUMED_INVOCATION_RATE = 1 / 50   # a skill fires in ~1 session out of 50
ASSUMED_DOC_READ_RATE   = 0.4      # a doc is read in ~40% of invocations
```

Amortised per session, a 76-token description outweighs a 1,500-token body despite being 20×
smaller: `76 × 1.00 = 76` versus `1502 × 0.02 = 30`. **The single highest-leverage place to
cut cost is the description**, and no raw token count would tell you that.

These are assumptions, not measurements — nothing in the corpus can validate how often *your*
skills fire. Change the constants and the weights follow coherently.

### Score and tiers

The weighted total is percentile-anchored like every quality band (p10 = 75 tokens → 100,
p90 = 331 → 0). **Higher is cheaper.**

| Tier | Cost score | Meaning |
|------|-----------:|---------|
| **LEAN** | ≥ 88 | cheap to keep installed |
| **MODERATE** | ≥ 58 | typical footprint |
| **HEAVY** | ≥ 35 | trim the always-on tier |
| **BLOATED** | < 35 | costs more than it likely returns |

Observed distribution: p10 = 0, p50 = 58, p90 = 100, σ = 32.1 — by a wide margin the
best-discriminating axis in the tool, because real skills differ far more in cost than in craft.

Duplicated prose is reported as **recoverable** spend, naming which files overlap — removing
one copy recovers those tokens. Full reasoning in
[ADR-0009](docs/adr/0009-cost-axis-and-instruction-clarity.md).

> Token counts use a chars/4 approximation, not a model tokenizer. A real tokenizer would add
> a model-specific dependency to a deterministic tool, and the score is a percentile rank where
> a consistent constant factor cancels out.

---

## Research basis

The scoring dimensions are informed by empirical research on agent context files and their
effect on task success rate and inference cost.

**Primary reference**

> Gloaguen, A., Mündler, N., Müller, M., Raychev, V., & Vechev, M. (2026).
> *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?*
> arXiv:2602.11988. <https://arxiv.org/abs/2602.11988>

**Key findings applied in this project**

| Finding | Dimension affected |
|---------|-------------------|
| LLM-generated context files cost +20–23 % more tokens with no/negative task-success benefit | Information Density weight raised from 12 → 15 |
| Redundant prose that duplicates README content accounts for most of the cost increase | Information Density — compression ratio and n-gram deduplication signals |
| Specific trigger conditions ("Use when X") and exclusion conditions ("Do not use for Y") are the highest-ROI content — +4 % task success with human-written minimal files | Metadata — `when_to_use` now scored for specificity, not just presence |
| Linking more supporting files causes agents to load and reason over them regardless of relevance | Progressive Disclosure weight lowered from 7 → 5 |

If you find other published work that should inform the scoring, please open an issue or PR.

---

## Benchmark results

Ran 3 arms × 8 scenarios × N=10 repeats (240 LLM calls per model) at temperature 0.3.
Each call uses a unique nonce to prevent provider-side caching from skewing results.

Arms: **Baseline** (generic "extract JSON" prompt, no SKILL.md), **LowQuality**
(conversational SKILL.md, no schema, no example), **HighQuality** (SKILL.md improved
by this library's recommendations).

### Cross-model comparison (Anthropic, N=10)

| Model | Baseline | LowQuality | HighQuality | LowQuality tok waste |
|-------|:--------:|:----------:|:-----------:|:--------------------:|
| claude-haiku-4-5 | 4 % (3/80) | **0 %** (0/80) | **100 %** (80/80) | 7.6× (359 vs 47) |
| claude-sonnet-4-6 | 25 % (20/80) | **0 %** (0/80) | **100 %** (80/80) | 10.4× (428 vs 41) |
| claude-opus-4-8 | 25 % (20/80) | **0 %** (0/80) | **100 %** (80/80) | 12.0× (778 vs 63) |

### Per-scenario breakdown (claude-sonnet-4-6, N=10)

| Scenario | Baseline | LowQuality | HighQuality |
|----------|:--------:|:----------:|:-----------:|
| Customer Order Extraction | 10/10 ✓ | 0/10 | 10/10 ✓ |
| Meeting Notes Summary | 10/10 ✓ | 0/10 | 10/10 ✓ |
| Bug Report Triage | 0/10 | 0/10 | 10/10 ✓ |
| Product Review Analysis | 0/10 | 0/10 | 10/10 ✓ |
| Incident Report Parser | 0/10 | 0/10 | 10/10 ✓ |
| Support Email Classification | 0/10 | 0/10 | 10/10 ✓ |
| Job Posting Parser | 0/10 | 0/10 | 10/10 ✓ |
| Ambiguous Ticket Routing ¹ | 0/10 | 0/10 | 10/10 ✓ |

¹ Scenario 8 is a deliberately ambiguous billing/technical ticket where both
category values are defensible. Correctness only requires a valid JSON structure
with a valid enum value — not a specific category. HighQuality produced 10/10
correct responses with ≤ 1 output-token variance (46–47 tokens), showing that
the "choose dominant issue" guidance keeps the model consistent under genuine
semantic ambiguity.

### What the numbers mean

**HighQuality is model-agnostic:**
100 % correctness on Haiku, Sonnet, and Opus. A SKILL.md with a strict schema and
a worked example produces reliable structured output regardless of which model tier
you deploy on.

**More capable models make bad SKILL.md more expensive:**
LowQuality token waste grows with model capability — Haiku wastes 7.6×, Sonnet 10.4×,
Opus **12.0×** (778 tokens of prose for 0 % correctness). More capable models follow
chain-of-thought instructions more faithfully, so a poorly written SKILL.md costs
progressively more as you upgrade. The token savings from HighQuality are largest at
the top of the capability range.

**Baseline passes 2/8 scenarios — the failure is schema alignment, not capability:**
The model correctly extracts all the right data in every Baseline run. It just names
fields its own way (`caller_name` instead of `name`, `tasks` instead of `action_items`,
`status: "Resolved"` instead of `resolved: true`). This is a contract failure, not a
reasoning failure — exactly what a strict schema in your SKILL.md prevents. Haiku
guesses correct key names only 4 % of the time; Sonnet and Opus reach 25 % because
they tend toward more conventional field naming.

**HighQuality is near-deterministic:**
7 of 8 scenarios produced zero output-token variance across all 10 Sonnet runs. A
well-designed SKILL.md with an explicit schema and a worked example guides the model
into a single, predictable output path — which is what production automation needs.

### Running the benchmark yourself

```bash
# Dry-run (quality scoring only, no LLM calls)
python benchmarks/run_benchmark.py --dry-run

# Single model
export SKILLSPECTOR_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python benchmarks/run_benchmark.py -n 10

# Two specific models (comparison table printed at end)
python benchmarks/run_benchmark.py --models claude-haiku-4-5-20251001,claude-sonnet-4-6

# All Anthropic models
python benchmarks/run_benchmark.py --anthropic-all
```

Full documentation: [`benchmarks/README.md`](benchmarks/README.md).

---

## Install

### Homebrew (recommended for users)

```bash
brew tap larsroettig/tap
brew install skillspector-quality

skillspector-quality scan ./my-skill --no-llm
```

The formula installs a self-contained binary — **no Python, no `skillspector` checkout, and no
Rust toolchain required**. Supported: macOS arm64, macOS x86_64, Linux x86_64.

Why a binary rather than a normal Homebrew Python formula: `skillspector` is not on PyPI and
upstream publishes no tags, the runtime tree is 48 packages, and six of those are Rust/C
extensions that Homebrew would have to compile from source. The reasoning and the trade-offs
are in [ADR-0008](docs/adr/0008-homebrew-distribution.md).

> Use `--no-llm` with the binary. The optional LLM commentary needs provider credentials; the
> deterministic score — the actual product — needs nothing.

### Development (from source)

`skillspector` is not on PyPI, so it must be installed editable from a local checkout first.
The install script handles everything — picking a compatible Python (`>=3.12,<3.14`),
creating the venv, and installing both packages:

```bash
scripts/install.sh                          # looks for ../SkillRater by default
scripts/install.sh /path/to/skillspector   # or point at a specific checkout
```

Manual equivalent with [uv](https://docs.astral.sh/uv/):

```bash
uv venv .venv --python 3.13 && source .venv/bin/activate
uv pip install -e ../SkillRater       # the skillspector checkout (pinned to ==2.4.4)
uv pip install -e '.[dev]'
```

### Releasing

One-time setup — create the tap repository (it must be named `homebrew-tap` for
`brew tap larsroettig/tap` to resolve):

```bash
gh repo create larsroettig/homebrew-tap --public \
  --description "Homebrew formulae for larsroettig's tools"
git clone https://github.com/larsroettig/homebrew-tap && mkdir -p homebrew-tap/Formula
```

Per release:

```bash
git tag -s v2.0.0 -m "v2.0.0" && git push origin v2.0.0  # triggers .github/workflows/release.yml
gh run watch                                  # builds 3 platforms, publishes the release

# once the release exists, regenerate the formula from its published checksums
packaging/homebrew/update-formula.sh v2.0.0 \
  ../homebrew-tap/Formula/skillspector-quality.rb

cd ../homebrew-tap && git commit -am "skillspector-quality 2.0.0" && git push
```

Verify before announcing:

```bash
brew uninstall skillspector-quality 2>/dev/null
brew untap larsroettig/tap 2>/dev/null
brew tap larsroettig/tap && brew install skillspector-quality
brew test skillspector-quality      # runs a real scan against a generated skill
```

The release workflow refuses to publish a binary built against the CI stub, and asserts the
frozen build reproduces a known score before packaging — see
[ADR-0008](docs/adr/0008-homebrew-distribution.md).

### In CI (with a pre-built wheel)

If your organization packages skillspector as an internal wheel or mirrors it:

```bash
pip install skillspector==2.4.4 --index-url https://your.private.pypi/simple
pip install skillspector-quality
```

---

## Docker

`make docker-build` builds a self-contained image. Because skillspector is not on PyPI, the
Makefile first stages the local checkout (`SKILLSPECTOR_SRC`, default `../SkillRater`) into the
build context, then runs a multi-stage build:

```bash
make docker-build                              # uses ../SkillRater
make docker-build SKILLSPECTOR_SRC=/path/to/skillspector
```

Scan a skill by mounting it into the container:

```bash
docker run --rm -v "$PWD/my-skill:/work/skill:ro" \
  skillspector-quality scan /work/skill --no-llm

# or, for the bundled fixture:
make docker-run
```

In CI, pull and run the image directly:

```yaml
- name: Quality scan (Docker)
  run: |
    docker run --rm \
      -v "${{ github.workspace }}/skills:/work/skills:ro" \
      your-registry/skillspector-quality:latest \
      scan /work/skills/my-skill --no-llm --min-score 60
```

---

## Contributing

Contributions are welcome — new dimensions, weight proposals backed by research, bug fixes,
and CI recipes. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, the
DCO sign-off requirement, and what kinds of changes are in scope.

---

## Security

To report a security vulnerability, **do not open a public issue**. See [SECURITY.md](SECURITY.md)
for the private reporting address and our disclosure policy.

---

## License

MIT — see [LICENSE](LICENSE). This project depends on
[skillspector](https://github.com/NVIDIA/skillspector) (Apache-2.0) as a separate library; no
skillspector source is included here.

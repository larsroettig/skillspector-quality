# Context — skillspector-quality

Glossary of the ubiquitous language for the skill-quality scorer. Glossary only — no
implementation details, no decisions (those live in `docs/adr/`).

## Terms

### Scored signal
A check whose result moves the numeric quality score. Each dimension is a weighted bag of
scored signals in `[0,1]`. Example: `when_to_use` specificity.

### Advisory note
Guidance surfaced to the author that carries **zero score weight** — it explains why
something is good practice without rewarding or penalizing the number. Example: presence of
`author`/`version` frontmatter. Distinct from a [[Scored signal]]: an absent advisory item
never lowers the score.

### Required field
Frontmatter the official skill spec mandates: `name`, `description`. Their absence is a
[[Scored signal]] failure. Everything else (`when_to_use`, `author`, `version`, behavioral
fields) is optional.

### Supporting doc
A markdown file in the skill bundle other than `SKILL.md` that holds detail progressively
disclosed from the entry point (e.g. `reference.md`, `FORMS.md`, `reference/sales.md`).

### Progressive disclosure
Keeping `SKILL.md` lean and moving depth into [[Supporting doc]]s that are linked, so an
agent loads detail only when needed.

### Disclosure trigger
The point at which a skill "owes" [[Progressive disclosure]]: SKILL.md body below 100 lines
owes nothing (N/A); above 500 lines owes full disclosure; in between, expectation ramps.

### Nesting depth
Distance of a [[Supporting doc]] from `SKILL.md` in the link graph. Depth 1 = linked
directly. Depth ≥2 = nested behind another doc — a scored penalty, since agents partial-read
nested files and miss content.

### Benchmark arm
One structural variant of the same skill in the folder-structure benchmark. The three arms:
**Monolith** (all content in SKILL.md, no files), **Flat** (lean SKILL.md + one
`reference.md`), **Folder** (lean SKILL.md + a `reference/` directory split by domain).

### Planted fact
A unique, unguessable fact placed in exactly one domain's [[Supporting doc]] in the
benchmark. A domain-targeted question is correct only if the agent retrieves its planted
fact — forcing it to load the right file and making correctness deterministic.

### Context cost
Cumulative input tokens the API reports across a tool-use loop. The benchmark's efficiency
metric — what [[Progressive disclosure]] is meant to reduce. Distinct from output tokens,
which the existing extraction benchmark measures.

### Broken link
A relative link whose target has a text suffix (`.md/.py/.txt/.json/.yaml/.yml/.toml`) but is
absent from the scanned `file_cache`. The agent would be told to read a file that isn't there —
wasted tokens. A `[[Scored signal]]` inside [[Link validity]]. Links to binary assets
(`.pptx/.png/.pdf`) are **not** flagged: the loader never reads them, so their absence is
unverifiable.

### Platform-coupled link
A link target that resolves only on one machine or OS: a POSIX absolute path (`/Users/...`),
home-relative (`~/`), a Windows path (`C:\...` or backslashes), or a `file://` URL. Breaks for
any other user or in CI. A `[[Scored signal]]` inside [[Link validity]].

### Case-mismatched link
A link that resolves only case-insensitively — e.g. `reference/Catalog.md` pointing at
`reference/catalog.md`. Works on macOS/Windows, breaks on case-sensitive Linux/CI. Scored at
[[Broken link]] severity within [[Link validity]].

### Redundant link
The same target reached by 2+ `[text](target)` **markdown** links in a skill — repeats add
tokens but no disclosure value. Bare/backtick prose paths are exempt (repeating "read this file
at this step" is legitimate guidance). A light `[[Scored signal]]` inside [[Link validity]].

### Link validity
The sub-signal inside Structural Coherence that scores link hygiene:
`1 - (0.34·broken + 0.34·platform + 0.10·redundant)`, where broken includes
[[Case-mismatched link]]s. Aggregates [[Broken link]], [[Platform-coupled link]], and
[[Redundant link]] checks.

### Scoring config
Project + CLI controls (`[tool.skillspector-quality]` in `pyproject.toml`, plus `--disable` /
`--strict` flags, unioned) that switch individual dimensions or sub-checks off, or make them
strict. See [[Disabled dimension]], [[Strict check]], [[Quality gate]].

### Disabled dimension
A dimension or sub-check turned off via [[Scoring config]]. It is omitted from scoring and its
weight renormalizes away — identical to an N/A dimension, so its absence never penalizes.

### Strict check
A dimension or sub-check marked strict via [[Scoring config]]: its threshold is raised (a harder
bar) AND, when violated, it produces a [[Quality gate]] failure.

### Quality gate
A pass/fail condition that makes the CLI exit non-zero. Two sources: the score falling below
`--min-score`, and any [[Strict check]] that failed.

### Calibration corpus
The population of real skills a [[Band edge]] is measured against. Percentiles describe *that*
corpus, not all skills everywhere — a corpus from one ecosystem yields narrower bands than the
wild. Never committed; only its [[Aggregate report]] is.

### Aggregate report
The publishable output of a calibration run: percentiles, correlations, and counts, with no
skill name, path, or text. What makes measuring a private corpus safe.

### Band edge
The pair of values mapping a raw statistic onto `[0,1]` for a [[Scored signal]] — the value
scoring zero and the value scoring full. Anchored to [[Calibration corpus]] percentiles.

### Quality-shaped signal
A [[Scored signal]] that is a ratio or length-invariant statistic, so an author cannot raise it
by writing more (compression ratio, MTLD, TF-IDF cosine). Its [[Band edge]] is anchored zero-at-p10,
full-at-p90 to use the whole range.

### Length-shaped signal
A [[Scored signal]] that is a raw count of words (example depth, description length). Its
[[Band edge]] is anchored at the corpus **median**, never p90 — anchoring high would reward
padding, and padding costs runtime tokens on every invocation. Distinct from a
[[Quality-shaped signal]] purely in how it can be gamed.

### Saturated dimension
A dimension whose earned fraction is near-constant across the [[Calibration corpus]] (σ≈0). It
adds a fixed amount to every score and therefore cannot rank anything, even though it looks
like it is contributing. The failure mode calibration exists to detect.

### Cost axis
The second score, reported beside quality and security: what a skill costs an agent in tokens.
Separate because the two are orthogonal (r=+0.14 over the [[Calibration corpus]]) — folding
them together would collapse a cheap sloppy skill and a polished bloated one onto one number.

### Loading tier
When a piece of a skill is paid for. **Always-on** = `description`, loaded for every skill in
every session. **On-invoke** = `SKILL.md` body, loaded when the skill fires. **On-demand** =
supporting docs and scripts, loaded only if the agent reads them. A [[Length-shaped signal]]
in each tier costs a different amount, which is why raw token totals mislead.

### Stated assumption
A named constant encoding a premise the [[Calibration corpus]] cannot validate — invocation
rate, doc-read rate. The [[Loading tier]] weights are *derived* from these rather than
hard-coded, so the premise is arguable instead of buried in a ratio. Distinct from a
[[Band edge]], which is measured.

### Recoverable cost
Tokens paid more than once — duplicated prose across files. Reported on the [[Cost axis]] and
as an [[Advisory note]] naming which files overlap, never as a [[Scored signal]]: the existing
duplication metric already prices it (r=+0.951), so scoring it again would double-count.

### Violation detector
A [[Saturated dimension]] that is saturated *legitimately*, because real skills genuinely almost
all pass it (Readability, platform-coupled links). It earns its weight by catching the rare
offender, not by discriminating — so it should not be forced to spread.

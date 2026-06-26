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

# Roadmap

Where skillspector-quality is going over the next year, and why. Covering **2026 H2 through
2027 H2**.

This is the maintainer's current intent, not a commitment or a delivery date. The project's
whole premise is that scoring decisions should follow evidence, so an item here can be dropped
or reversed when measurement says it should be — that has already happened once (see
*Completed*). Dated items are reviewed at each minor release; the whole document is reviewed at
each major.

Discussion of any item belongs in a [GitHub issue](https://github.com/larsroettig/skillspector-quality/issues).

## Now — 2026 H2

**Ship 2.0.0.** The cost axis, percentile-calibrated band edges, link hygiene, configurable
scoring, and binary distribution are complete and awaiting release. Scores are deliberately not
comparable with 1.x; [CHANGELOG.md](CHANGELOG.md) records why.

**Close the OpenSSF Silver gaps.** Passing is at 100%. Silver needs governance, roadmap, and
assurance-case documents (this file is part of that), signed releases, and a second maintainer.
Tracked as its own effort because several items are organisational rather than technical.

**Signed releases end to end.** Release artifacts are signed with Sigstore keyless signing;
next is making verification a documented, one-command step for consumers and signing version
tags in git. See [RELEASING.md](RELEASING.md).

## Next — 2027 H1

**Broaden the calibration corpus.** This is the most important item on the list. The band edges
in [`docs/adr/0007-percentile-calibration.md`](docs/adr/0007-percentile-calibration.md) are
anchored to percentiles of a corpus drawn from a single ecosystem that shares authors in places
— [`docs/calibration-report.md`](docs/calibration-report.md) says so explicitly. Anchors derived
from a narrow corpus produce narrower bands than the wild. Re-running against a broader,
independently-sourced corpus would either confirm the anchors or move them, and moving them is
a breaking change.

**Retire or repair saturated dimensions.** Calibration identified dimensions whose earned
fraction is near-constant across the corpus: they add a fixed amount to every score and rank
nothing. Some are legitimate violation detectors and should stay; the rest should be re-banded
or removed. Distinguishing the two requires the broader corpus above, so this follows it.

**Second maintainer.** The project's bus factor is 1 — see
[GOVERNANCE.md](GOVERNANCE.md#continuity-of-access). Recruiting and onboarding a second
maintainer with admin access is the single highest-value change to project resilience, and it
is a prerequisite for the Silver `bus_factor` criterion.

## Later — 2027 H2

**Validate the cost model's stated assumptions.** The loading-tier weights on the cost axis are
derived from named assumptions — invocation rate and doc-read rate — that the calibration corpus
cannot confirm (see
[`docs/adr/0009-cost-axis-and-instruction-clarity.md`](docs/adr/0009-cost-axis-and-instruction-clarity.md)).
Measuring real invocation and read rates from agent traces would replace an argued premise with
a measured one.

**Scoring stability across versions.** Users tracking a score over time need to know when a
change is theirs and when it is ours. A documented way to re-score history under a pinned
scorer version, or a stability guarantee per minor release, would make the number trustworthy
as a trend rather than only as a snapshot.

**Wider ecosystem coverage.** Scoring currently assumes the Claude Code skill layout. Supporting
other agent-skill formats is worth doing only if the underlying signals generalise — an open
question, not a decided direction.

## Not planned

Stated so nobody invests effort in a direction that will be declined — these mirror the
constraints in [CONTRIBUTING.md](CONTRIBUTING.md#what-we-are-looking-for):

- **LLM calls in the deterministic scoring path.** The score must stay reproducible without
  network access or an API key. LLM commentary stays strictly advisory and never moves a number.
- **Weakening the determinism guarantee** in any form.
- **Hard dependencies on proprietary services.**
- **Scoring that rewards writing more.** Length-shaped signals anchor at the corpus median
  precisely so padding does not pay; runtime tokens are a real cost to users.

## Completed

- **2.0.0 (pending release)** — cost axis; percentile-calibrated bands; link hygiene;
  configurable scoring via `pyproject.toml`, `--disable`, `--strict`; PyInstaller binaries and
  Homebrew formula; OpenSSF passing badge at 100%.
- **1.1.0** — extraction and structure benchmarks; 10-dimension deterministic scorer; cache
  observability; ADRs 0001–0003.
- **1.0.0** — initial public release.

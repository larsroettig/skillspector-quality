# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Each released version below is tagged in git as `vX.Y.Z` and published as a GitHub
release. The section for a version is the source of that release's notes.

## [Unreleased]

### Added

- `GOVERNANCE.md` — governance model, roles and responsibilities, and a continuity-of-access
  plan, including a plainly-stated bus factor of 1.
- `ROADMAP.md` — direction through 2027 H2, with an explicit "not planned" section.
- `RELEASING.md` — how a release is cut and how anyone verifies it.
- `docs/assurance-case.md` — trust boundaries, threat model, security claims with evidence, and
  accepted risks.

### Changed

- Release artifacts are now signed with Sigstore keyless signing (cosign + GitHub OIDC) and
  published with `.sigstore.json` bundles alongside `SHA256SUMS`. There is no private signing
  key to lose or leak; verification checks that the artifact came from this repository's release
  workflow.

## [2.0.0] — 2026-08-22

Major bump: quality scores are not comparable with 1.x. Band edges were re-anchored to
measured corpus percentiles, so the same skill will generally score differently than it
did under 1.1.0.

### Added

- **Cost axis** — token cost is now reported as a third score alongside quality and
  security. Priced by loading tier: `description` is always-on (paid in every session),
  the `SKILL.md` body is on-invoke, supporting docs are on-demand. Tier weights derive
  from named, stated assumptions rather than hard-coded ratios. See
  `docs/adr/0009-cost-axis-and-instruction-clarity.md`.
- **Link hygiene** scoring inside Structural Coherence: broken, platform-coupled,
  case-mismatched, and redundant links. Binary assets are deliberately not flagged. See
  `docs/adr/0005-link-hygiene.md`.
- **Configurable scoring** via `[tool.skillspector-quality]` in `pyproject.toml`, unioned
  with the new `--disable` and `--strict` flags. Disabled dimensions renormalize away;
  strict checks raise the bar and cause a non-zero exit. See
  `docs/adr/0006-configurable-scoring.md`.
- **`--version` flag** on the CLI.
- **Standalone binaries** for macOS (arm64, x86_64) and Linux x86_64, published on tag,
  plus a Homebrew formula updater. See `docs/adr/0008-homebrew-distribution.md`.
- `benchmarks/calibrate.py`, which emits an aggregate-only report — percentiles,
  correlations, counts, with no skill name, path, or text — so a private corpus can be
  measured without republishing it.

### Changed

- Band edges are anchored to measured corpus percentiles. Quality-shaped signals span
  p10→p90; length-shaped signals anchor at the median rather than p90, so padding a skill
  body is not rewarded. See `docs/adr/0007-percentile-calibration.md` and
  `docs/calibration-report.md`.
- Density bands reworked around the disclosure trigger. See
  `docs/adr/0004-density-bands.md`.
- `__version__` is now read from installed package metadata instead of a hand-maintained
  literal, which had drifted to `0.1.0` across both prior releases.

### Fixed

- `scorers.py` used PEP 701 f-string syntax (Python 3.12+). The fuzzing base image parses
  with Python 3.11, where PyInstaller silently omitted the unparseable module and produced
  a fuzz target that failed at import. The build now runs `compileall` first so such a
  syntax error surfaces immediately with a file and line.

### Security

- No publicly known run-time vulnerabilities were fixed in this release; no CVEs were
  assigned to this project at the time of release.
- Supply-chain hardening: GitHub Actions are pinned by commit SHA, the fuzzing base image
  is pinned by digest, and fuzzing dependencies install under `pip --require-hashes`.
- `actions/checkout` bumped to v7.0.0 and `github/codeql-action` to v4.36.3.

## [1.1.0] — 2026-06-26

### Added

- Extraction benchmark framework with Anthropic and OpenAI provider support.
- Structure benchmark comparing Monolith, Flat, and Folder layouts. See
  `docs/adr/0003`.
- 10-dimension deterministic quality scorer, requiring no LLM.
- Cache observability: `cache_creation_tokens` and `cache_read_tokens` tracked per run,
  with a warning when the system prompt falls below Anthropic's 2048-token caching
  minimum.
- ADRs 0001–0003, unit tests, and benchmark results.

### Changed

- Structure benchmark reduced from 16 domains × 10 repeats to 6 × 4 (144 calls instead of
  960), keeping three distractor pairs: finance/billing, product/platform,
  security/compliance.

### Security

- No publicly known run-time vulnerabilities were fixed in this release.

## [1.0.0] — 2026-06-26

Initial public release. Published without release notes at the time; this entry was
reconstructed afterward from the repository history.

### Added

- Quality rating layer over SkillSpector, scoring `SKILL.md` bundles 0–100 and merging the
  result with the upstream security report.

### Security

- No publicly known run-time vulnerabilities were fixed in this release.

[Unreleased]: https://github.com/larsroettig/skillspector-quality/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/larsroettig/skillspector-quality/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/larsroettig/skillspector-quality/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/larsroettig/skillspector-quality/releases/tag/v1.0.0

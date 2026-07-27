# Governance

This document describes how skillspector-quality is run: who decides what, how decisions are
made, and what happens if a key person becomes unavailable. It describes the project as it
actually is today — a small, single-maintainer project — rather than a structure it has not
grown into yet.

## Governance model

**Benevolent dictator (BDFL), with public decision records.**

Lars Roettig ([@larsroettig](https://github.com/larsroettig)) is the maintainer and has final
say on what is merged and released. This is the honest description of a project with one
maintainer; it is not aspirational.

Two things keep that from being opaque:

1. **Decisions of consequence are written down as ADRs** in [`docs/adr/`](docs/adr/) before or
   alongside the change that implements them. An ADR states the decision, the alternatives
   considered, and the reasoning. A reader who disagrees can argue with the reasoning rather
   than guess at it.
2. **All changes land through public pull requests** against `main`, so the discussion and the
   diff are archived and searchable.

## Roles and responsibilities

| Role | Holder | Responsibilities |
|------|--------|------------------|
| **Maintainer** | [@larsroettig](https://github.com/larsroettig) | Final decision on scope, design, and releases. Reviews and merges pull requests. Cuts releases and tags. Responds to vulnerability reports. Administers the repository and its secrets. |
| **Reviewer** | [@larsroettig](https://github.com/larsroettig) (via [CODEOWNERS](.github/CODEOWNERS)) | Reviews every pull request. `CODEOWNERS` requires owner review on all paths. |
| **Security contact** | [@larsroettig](https://github.com/larsroettig) | Receives private reports via GitHub Security Advisories; see [SECURITY.md](SECURITY.md). Committed response time is 7 days. |
| **Contributor** | Anyone | Opens issues and pull requests under [CONTRIBUTING.md](CONTRIBUTING.md). No special access required. |

> **Known limitation — bus factor.** Every role above is held by one person, so the project's
> bus factor is 1. This is a real risk, stated plainly rather than papered over. The mitigations
> in *Continuity of access* below reduce the damage, but they do not substitute for a second
> maintainer. Adding one is an open goal — see [ROADMAP.md](ROADMAP.md).

## How decisions are made

- **Routine changes** (bug fixes, documentation, dependency bumps, test coverage) — a pull
  request reviewed and merged by the maintainer.
- **Changes to scoring behaviour** (a new dimension, a weight, a band edge) — require an ADR in
  `docs/adr/` explaining the evidence, because these change every user's score. A change that
  makes scores incomparable with the previous line requires a major version bump, recorded in
  [CHANGELOG.md](CHANGELOG.md).
- **Disagreement** — raise it in the issue or pull request. The maintainer decides, and records
  the reasoning in the thread or an ADR. Anyone who disagrees with the outcome retains the
  option of forking: the project is MIT licensed.

## Contributing and becoming a maintainer

Anyone may contribute under [CONTRIBUTING.md](CONTRIBUTING.md). There is no CLA; contributions
are accepted under a [DCO](CONTRIBUTING.md#commit-sign-off-dco) sign-off.

A contributor may be invited to become a maintainer after a sustained record of accepted,
substantive contributions and review participation — in practice, several merged pull requests
touching scoring logic, plus demonstrated judgement in review. Invitation is at the maintainer's
discretion. A new maintainer receives the access listed below.

## Continuity of access

The point of this section is that the project survives the maintainer becoming unavailable.

**What the project depends on**

| Asset | Where it lives | Needed to |
|-------|----------------|-----------|
| Source, history, issues, PRs | GitHub, public | Everything. Fully mirrored by any clone or fork. |
| Release binaries | GitHub Releases, built by CI from a tag | Distribute builds |
| `CODECOV_TOKEN` | Repository secret | Upload coverage (non-blocking; CI passes without it) |
| `SCORECARD_TOKEN` | Repository secret | Publish Scorecard results |
| `GITHUB_TOKEN` | Issued per-run by GitHub | Publish releases |
| Homebrew tap | Separate repository | `brew install` distribution |

**Why the project can be continued by someone else**

- The repository is **public and MIT licensed**, so anyone may fork and continue it without
  permission. History, issues, and pull request discussion come along with a clone.
- **No release step depends on a personal credential.** The release workflow runs on a tag and
  authenticates with the automatically-issued `GITHUB_TOKEN`; artifacts are signed keylessly via
  Sigstore using the workflow's OIDC identity. There is no private signing key that can be lost
  with a person. See [RELEASING.md](RELEASING.md).
- **No dependency on unpublished infrastructure.** There is no bespoke build server, no private
  package index, and no self-hosted runner. Everything runs on GitHub-hosted runners from
  configuration committed in this repository.
- The two repository secrets above are **convenience only**. Losing them degrades coverage
  reporting and Scorecard publishing; neither blocks building, testing, or releasing.

**Standing arrangement**

- The repository is owned by an individual GitHub account. To reduce single-account risk, the
  maintainer grants **admin access to at least one trusted second party** where possible, so
  repository administration does not depend on one account remaining accessible.

  > **Status: not yet in place.** This is the project's main continuity gap, and it is recorded
  > here rather than hidden. Until a second admin exists, the practical fallback is the fork
  > path above: the licence and the public history make continuation possible without any
  > handover, though the canonical URL and the badge would not transfer.

- If the maintainer is unreachable for **90 days** with open security reports outstanding,
  reporters should treat the issue as unhandled and may disclose publicly, per the timeline in
  [SECURITY.md](SECURITY.md).

## Changing this document

Governance changes are made by pull request against this file, so the change is public and
reviewable like any other. Substantive changes to the decision-making model should also be
recorded as an ADR.

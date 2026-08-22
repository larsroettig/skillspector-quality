# Homebrew ships a frozen binary from a custom tap, not a Python formula

`brew install skillspector-quality` should work without the user having a Python toolchain, a
`skillspector` checkout, or a Rust compiler. The idiomatic Homebrew approach for a Python CLI —
`virtualenv_install_with_resources` — cannot deliver that here, so the tap installs a
PyInstaller binary built in CI instead.

## Why the idiomatic path does not work

- **The core dependency is not distributable.** `skillspector==2.1.4` is not on PyPI, and
  upstream (`NVIDIA/skillspector`) publishes **no tags and no releases**. There is nothing for
  a `resource` block to point at by version, and nothing for
  `brew update-python-resources` to resolve against. The repo's own install path assumes a
  local sibling checkout (`../SkillRater`), which a Homebrew build machine does not have.
- **The tree is 48 packages.** A resource-based formula would need ~47 hand-maintained
  `resource` blocks, regenerated on every dependency bump — by hand, since neither this
  package nor `skillspector` is on PyPI.
- **Six dependencies are compiled extensions.** `pydantic-core`, `orjson`, `ormsgpack`,
  `xxhash`, `zstandard` and `uuid-utils` are Rust or C. Homebrew builds Python dependencies
  from sdist, so the formula would need a Rust toolchain as a build dependency, with build
  times and failure modes to match.
- **homebrew-core is not available.** Its notability bar is roughly 75 stars / 30 forks /
  30 watchers; this repo has 10 / 0 / 1. A custom tap is required regardless of packaging
  style.

## Decision

CI freezes one self-contained executable per platform and attaches it to a GitHub Release. The
formula downloads a tarball and installs a single file — no dependency resolution at install
time, and no regeneration when a dependency bumps.

- **Targets:** `darwin-arm64`, `darwin-x86_64`, `linux-x86_64`. PyInstaller cannot
  cross-compile, so each needs a native interpreter. GitHub retired hosted Intel macOS
  runners, so `darwin-x86_64` builds on the same `macos-14` (arm64) host as `darwin-arm64`,
  forced onto its x86_64 slice via Rosetta 2 (`arch -x86_64 python -m PyInstaller ...`); pip
  then resolves `macosx_x86_64` wheels and PyInstaller freezes an Intel binary.
- **Upstream pin:** `NVIDIA/skillspector@fd25398d7aa99353d86237b9c260759351f0e644` — the newest
  commit where upstream `pyproject.toml` declares version `2.4.4`, currently upstream HEAD. A
  commit SHA is the only pin available in the absence of tags.

  Compatibility was verified at that commit before pinning, not assumed: all nine imported
  symbols (`resolve_input`, `build_context`, `meta_analyzer`, `report`, `ANALYZER_NODES`,
  `ANALYZER_NODE_IDS`, `SkillspectorState`, `chat_completion`, `is_llm_available`) exist; the
  four node signatures still take `SkillspectorState` and return a dict; `ANALYZER_NODE_IDS`
  is still a `list[str]` and `ANALYZER_NODES` a dict keyed by it; and every `SkillspectorState`
  key this layer reads or writes (`input_path`, `file_cache`, `output_format`, `report_body`,
  `risk_score`, `sarif_report`, `temp_dir_for_cleanup`, `use_llm`, `yara_rules_dir`,
  `model_config`) is still declared.
- **Formula generation:** `packaging/homebrew/update-formula.sh <tag>` reads the release's
  published `SHA256SUMS` and emits the formula, so the digests always match what CI built
  rather than what someone hashed locally.

## Two build-time guards

**Refuse to ship the CI stub.** `ci-stubs/skillspector` exists so `uv sync` can resolve the
pin without the real package, and `[tool.uv.sources]` redirects to it. A release binary built
against the stub would start, score, and report — while the entire security half of the tool
did nothing. The release job therefore installs with `pip` (which ignores `[tool.uv.sources]`)
and asserts the installed package has `nodes/analyzers/__init__.py`, the package layout only
real upstream has; the stub ships `nodes/analyzers.py` as a flat module.

**Assert a known score.** A frozen bundle that has lost a dynamically imported dependency
often still launches and fails later. The release job scans `tests/fixtures/calib-strong` and
requires exactly `82`, the score the source build produces.

## Consequences

The binary is ~25 MB — it embeds a Python runtime and all 48 packages. That is the cost of
removing the toolchain requirement, and it is downloaded once.

**Upstream drift is now a deliberate act.** The pin means the shipped binary keeps working
even as upstream moves. Bumping it requires re-verifying the nine imported symbols, the four
node signatures, and the state keys, because this layer imports upstream internals rather than
a published API. That was always true; the pin makes it visible and reviewable.

macOS binaries carry only an **ad-hoc signature**, not a Developer ID. Homebrew installs are
not quarantined (the download is not made by a browser), so this works — but the binaries are
not notarized, and a user who downloads a tarball manually from the Releases page will hit
Gatekeeper. Notarization needs a paid Apple Developer account and is deliberately out of scope.

`--no-llm` is the intended mode for the binary. The LLM commentary path is advisory and needs
provider credentials; the deterministic score, which is the product, needs nothing.

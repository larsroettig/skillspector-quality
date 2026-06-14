# Contributing to skillspector-quality

Thank you for your interest in improving skillspector-quality.  
This project is a **proposal** and community input is actively welcome — whether that is
a new quality dimension, a weight adjustment backed by research, a bug fix, or a CI recipe.

---

## Quick start for contributors

```bash
# 1. Fork and clone
git clone https://github.com/<you>/skillspector-quality
cd skillspector-quality

# 2. Set up the dev environment (requires skillspector checked out at ../SkillRater)
scripts/install.sh

# 3. Run the test suite
python -m pytest tests/

# 4. Run linters
ruff check src/ tests/
mypy src/
```

The install script picks a compatible Python (≥ 3.12, < 3.14), creates `.venv`, and installs
both `skillspector` and this package in editable mode.  If skillspector lives elsewhere:

```bash
scripts/install.sh /path/to/skillspector
```

---

## What we are looking for

| Area | Examples |
|------|---------|
| **New quality dimensions** | Dimensions grounded in peer-reviewed NLP or software-quality research; include a reference |
| **Weight adjustments** | Changes backed by empirical evidence or a published benchmark |
| **Bug fixes** | Wrong scores, unexpected N/A results, edge-case crashes |
| **CI recipes** | Integration examples for new CI systems or cloud providers |
| **Documentation** | Clarifications, typo fixes, better math explanations |
| **Tests** | Coverage gaps in `tests/test_scorers.py` |

**We do not accept** changes that add LLM calls to the deterministic scoring path, reduce the
determinism guarantee, or introduce hard dependencies on proprietary services.

---

## Making a change

1. Open an issue first for non-trivial changes — it avoids duplicate work.
2. Create a feature branch from `main`.
3. Add or update tests. The scorer must stay deterministic: same inputs must always produce
   the same score regardless of environment or LLM availability.
4. Update the relevant section of `README.md` if you change a dimension weight or formula.
5. Run `python -m pytest tests/` and confirm all tests pass.
6. Open a pull request. The PR description should include:
   - What changed and why
   - If a scoring formula changed: the research or rationale behind it
   - Before/after score examples on a real or synthetic skill

---

## Commit sign-off (DCO)

All commits must carry a Developer Certificate of Origin sign-off.  Add `-s` to your commit:

```bash
git commit -s -m "feat: add when_to_use specificity scorer"
```

This adds:

```
Signed-off-by: Your Name <you@example.com>
```

By signing off you certify that you wrote or have the right to contribute the code under the
project's MIT license, per the [Developer Certificate of Origin v1.1](https://developercertificate.org/).

---

## Code style

- **Python ≥ 3.12**, type-annotated, `ruff` + `mypy` clean.
- No new runtime dependencies without discussion — the scorer must stay installable in
  minimal CI environments.
- New scoring helpers go in `src/skillspector_quality/quality/scorers.py`; keep them pure
  (no I/O, no global state).
- Default to **no comments** — well-named functions and variables are preferred. Add a comment
  only for non-obvious invariants or research-derived constants (include the citation).

---

## Reporting bugs

Open a [GitHub issue](../../issues) with:
- The skill directory or a minimal reproducer
- The command you ran
- The output you got vs. what you expected

For security vulnerabilities, see [SECURITY.md](SECURITY.md).

---

## Code of conduct

All participation is governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

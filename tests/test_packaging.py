"""Tests for the Homebrew distribution path (ADR-0008).

Packaging breaks silently: a typo in the formula generator or a drift between the pinned
upstream SHA and the documentation is only discovered when a release fails. These run in the
normal suite so that never happens.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
GENERATOR = REPO_ROOT / "packaging" / "homebrew" / "update-formula.sh"
SPEC = REPO_ROOT / "packaging" / "pyinstaller" / "skillspector-quality.spec"
RELEASE_WF = REPO_ROOT / ".github" / "workflows" / "release.yml"

# Fake but well-formed digests, so the generator can be exercised without a published release.
_FIXTURE_SUMS = "\n".join(
    f"{c * 64}  skillspector-quality-2.0.0-{target}.tar.gz"
    for c, target in (("1", "darwin-arm64"), ("2", "darwin-x86_64"), ("3", "linux-x86_64"))
)


@pytest.fixture
def formula(tmp_path: Path) -> str:
    sums = tmp_path / "SHA256SUMS"
    sums.write_text(_FIXTURE_SUMS + "\n", encoding="utf-8")
    result = subprocess.run(
        ["bash", str(GENERATOR), "v2.0.0"],
        capture_output=True,
        text=True,
        check=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "SHA256SUMS_FILE": str(sums)},
    )
    return result.stdout


def test_formula_carries_a_digest_for_every_platform(formula: str) -> None:
    """A missing digest means `brew install` fails on that platform only — easy to miss."""
    for char in ("1", "2", "3"):
        assert f'sha256 "{char * 64}"' in formula


def test_formula_urls_match_the_release_asset_names(formula: str) -> None:
    """The URLs must match exactly what release.yml uploads, or install 404s."""
    for target in ("darwin-arm64", "darwin-x86_64", "linux-x86_64"):
        expected = (
            "https://github.com/larsroettig/skillspector-quality/releases/download/"
            f"v2.0.0/skillspector-quality-2.0.0-{target}.tar.gz"
        )
        assert f'url "{expected}"' in formula


def test_formula_installs_the_binary_and_tests_a_real_scan(formula: str) -> None:
    assert 'bin.install "skillspector-quality"' in formula
    # A --help-only test would pass even if the frozen bundle lost a dependency at import time.
    assert "--no-llm --format json" in formula


@pytest.mark.skipif(shutil.which("ruby") is None, reason="ruby not available")
def test_formula_is_syntactically_valid_ruby(formula: str, tmp_path: Path) -> None:
    path = tmp_path / "skillspector-quality.rb"
    path.write_text(formula, encoding="utf-8")
    result = subprocess.run(["ruby", "-c", str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_generator_fails_loudly_on_a_missing_checksum(tmp_path: Path) -> None:
    """Silently emitting an empty sha256 would produce a formula that installs anything."""
    sums = tmp_path / "SHA256SUMS"
    sums.write_text("1" * 64 + "  skillspector-quality-2.0.0-darwin-arm64.tar.gz\n")
    result = subprocess.run(
        ["bash", str(GENERATOR), "v2.0.0"],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "SHA256SUMS_FILE": str(sums)},
    )
    assert result.returncode != 0
    assert "no checksum" in result.stderr


def test_release_workflow_pins_skillspector_by_full_sha() -> None:
    """A branch or tag ref would let the binary's contents change without a commit here.

    Upstream publishes no tags or releases, so a 40-character commit SHA is the only pin
    available (ADR-0008).
    """
    workflow = yaml.safe_load(RELEASE_WF.read_text(encoding="utf-8"))
    sha = workflow["env"]["SKILLSPECTOR_SHA"]
    assert re.fullmatch(r"[0-9a-f]{40}", sha), f"not a full commit SHA: {sha!r}"


def test_release_workflow_refuses_to_ship_the_ci_stub() -> None:
    """The CI stub satisfies imports but scores nothing real — shipping it would be silent."""
    text = RELEASE_WF.read_text(encoding="utf-8")
    assert "stub skillspector detected" in text
    assert "nodes" in text and "analyzers" in text


def test_release_workflow_smoke_tests_against_a_known_score() -> None:
    """Guards the frozen bundle against losing a dynamically imported dependency."""
    text = RELEASE_WF.read_text(encoding="utf-8")
    assert "calib-strong" in text
    assert "expected 82" in text


def test_pyinstaller_spec_collects_the_dynamic_import_packages() -> None:
    """langchain/langgraph resolve nodes dynamically; static analysis alone misses them."""
    text = SPEC.read_text(encoding="utf-8")
    for pkg in ("langchain_core", "langgraph", "skillspector", "skillspector_quality"):
        assert f'"{pkg}"' in text
    assert "copy_metadata" in text
    # UPX corrupts codesigned macOS binaries; the arm64 build will not launch if it is on.
    assert "upx=False" in text

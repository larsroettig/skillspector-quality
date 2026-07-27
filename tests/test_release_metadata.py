"""Guards on the change-control criteria from the OpenSSF Best Practices badge.

Two of those criteria are easy to satisfy once and then lose silently:

* ``version_unique`` — one identifier per release. ``__version__`` had already drifted to
  ``0.1.0`` while ``pyproject.toml`` said ``2.0.0`` and the newest tag said ``v1.1.0``.
* ``release_notes`` — a human-readable summary per release. The release workflow reads it
  from ``CHANGELOG.md``, so a tag cut without a matching section fails the release. These
  tests move that failure from release time to commit time.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from skillspector_quality import __version__

REPO_ROOT = Path(__file__).parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Mirrors the extraction in .github/workflows/release.yml; keep the two in step.
_SECTION = r"^## \[{version}\].*?$\n(.*?)(?=^## |\Z)"


def _declared_version() -> str:
    with PYPROJECT.open("rb") as fh:
        version: str = tomllib.load(fh)["project"]["version"]
    return version


def _changelog_section(version: str) -> str | None:
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        _SECTION.format(version=re.escape(version)), text, re.MULTILINE | re.DOTALL
    )
    return match.group(1).strip() if match else None


def test_runtime_version_matches_pyproject() -> None:
    """OpenSSF version_unique: one version identifier, not three."""
    assert __version__ == _declared_version()


def test_changelog_has_section_for_current_version() -> None:
    """OpenSSF release_notes: the release workflow fails without this section."""
    version = _declared_version()
    assert _changelog_section(version) is not None, (
        f"CHANGELOG.md has no '## [{version}]' section — `gh release create` would have "
        f"no notes to publish. Add one before tagging v{version}."
    )


def test_changelog_section_is_not_empty() -> None:
    section = _changelog_section(_declared_version())
    assert section, "the changelog section for the current version has no content"


def test_changelog_documents_vulnerability_status() -> None:
    """OpenSSF release_notes_vulns: every release states what was fixed, even if nothing."""
    section = _changelog_section(_declared_version())
    assert section is not None
    assert "### Security" in section, (
        "each release section needs a '### Security' heading naming every publicly known "
        "run-time vulnerability fixed, or stating that there were none"
    )


@pytest.mark.parametrize("version", ["1.0.0", "1.1.0"])
def test_released_versions_remain_documented(version: str) -> None:
    """Past releases keep their notes; the badge is assessed against release history."""
    assert _changelog_section(version), f"CHANGELOG.md lost the section for {version}"


# --------------------------------------------------------------------------- #
# Project-oversight documents
#
# These back OpenSSF Silver criteria (governance, roles_responsibilities,
# access_continuity, documentation_roadmap, assurance_case). A published badge asserts
# they exist; deleting or renaming one should fail here rather than quietly turn the
# public claim into a false one.
# --------------------------------------------------------------------------- #

RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


@pytest.mark.parametrize(
    ("filename", "criterion"),
    [
        ("GOVERNANCE.md", "governance / roles_responsibilities / access_continuity"),
        ("ROADMAP.md", "documentation_roadmap"),
        ("RELEASING.md", "signed_releases (verification instructions)"),
        ("docs/assurance-case.md", "assurance_case"),
        ("CODE_OF_CONDUCT.md", "code_of_conduct"),
        ("CONTRIBUTING.md", "contribution_requirements"),
        ("SECURITY.md", "vulnerability_report_process"),
    ],
)
def test_oversight_document_exists(filename: str, criterion: str) -> None:
    path = REPO_ROOT / filename
    assert path.is_file(), f"{filename} is missing — OpenSSF {criterion} depends on it"
    assert path.read_text(encoding="utf-8").strip(), f"{filename} is empty"


def test_governance_names_the_continuity_fallback() -> None:
    """access_continuity is only real if the fallback is written down."""
    text = (REPO_ROOT / "GOVERNANCE.md").read_text(encoding="utf-8")
    assert "Continuity of access" in text
    assert "bus factor" in text.lower(), "the bus-factor limitation must stay stated, not hidden"


def test_assurance_case_states_accepted_risks() -> None:
    """An assurance case that lists only mitigations is marketing, not an argument."""
    text = (REPO_ROOT / "docs" / "assurance-case.md").read_text(encoding="utf-8")
    assert "Accepted risks" in text
    assert "Trust boundaries" in text


def test_release_workflow_signs_artifacts() -> None:
    """signed_releases: keyless signing must stay wired up, with the OIDC permission."""
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    assert "id-token: write" in text, "Sigstore keyless signing needs the OIDC token permission"
    assert "cosign sign-blob" in text, "release artifacts are no longer signed"
    assert "sigstore/cosign-installer@" in text
    assert ".sigstore.json" in text, "signature bundles must be uploaded with the release"

"""skillspector-quality: a quality rating layer on top of SkillSpector."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    # Read from installed package metadata rather than restating the number here: a
    # hand-maintained literal drifts from pyproject.toml (it sat at 0.1.0 through two
    # releases), and OpenSSF `version_unique` wants one identifier per release, not three.
    __version__ = version("skillspector-quality")
except PackageNotFoundError:  # pragma: no cover - only when running from a source tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]

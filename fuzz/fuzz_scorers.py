"""Fuzz the SKILL.md parser and quality scorer pipeline.

Targets the two main untrusted-input surfaces:
  - _parse_frontmatter: YAML frontmatter from arbitrary user files
  - score_quality: full scorer pipeline over a file_cache dict
"""

import sys

import atheris

with atheris.instrument_imports():
    from skillspector_quality.quality import score_quality
    from skillspector_quality.quality.scorers import _parse_frontmatter


@atheris.instrument_func
def TestOneInput(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(len(data))

    # Fuzz the YAML frontmatter parser
    try:
        _parse_frontmatter(text)
    except Exception:
        pass

    # Fuzz the full scorer pipeline with a synthetic single-file doc
    try:
        score_quality({"SKILL.md": text})
    except Exception:
        pass


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

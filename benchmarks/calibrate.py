"""Measure the distribution of every raw quality statistic over a corpus of real skills.

Motivation: every band edge in ``scorers.py`` used to be a hand-picked constant defended by
prose. This harness replaces that with a measurement — point it at a directory tree of
skills and it reports where real skills actually sit on each statistic, so thresholds can be
anchored to percentiles instead of intuition. See ``docs/adr/0007-percentile-calibration.md``.

**Privacy.** Output is aggregate-only: percentiles, correlations, and counts. No skill name,
path, or text is ever emitted, so the report of a private corpus is safe to publish.

Usage::

    python benchmarks/calibrate.py                        # defaults to ~/.claude
    python benchmarks/calibrate.py ~/.claude ./my-skills  # several roots
    python benchmarks/calibrate.py --format json -o calibration.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from skillspector_quality.quality import score_quality
from skillspector_quality.quality.cost import score_cost
from skillspector_quality.quality.scorers import (
    SkillDoc,
    _build_idf,
    _compression_ratio,
    _cosine,
    _link_hygiene,
    _median,
    _mtld,
    _ngram_dup,
    _prose_for_readability,
    _readability_grades,
    _strip_fences_text,
    _terms,
    _tfidf_vec,
    _word_tokens,
)

# Suffixes worth loading into a bundle's file_cache (mirrors the scanner's own view).
TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".markdown",
        ".py",
        ".sh",
        ".bash",
        ".zsh",
        ".js",
        ".ts",
        ".yaml",
        ".yml",
        ".txt",
        ".json",
        ".toml",
    }
)

# Skip pathologically large files: they are generated data, not authored prose.
MAX_FILE_BYTES = 400_000

# Percentiles reported for every metric.
QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)

# Raw statistics, in report order. Each maps to a band edge (or pair) in scorers.py.
METRIC_ORDER = (
    "compression",
    "ngram_dup",
    "mtld",
    "readability",
    "cosine_desc",
    "cosine_cohesion",
    "example_depth",
    "hedge_density",
    "untagged_fences",
    "cost_weighted",
    "cost_always_on",
    "cost_on_invoke",
    "cost_on_demand",
    "body_lines",
    "n_docs",
)


def load_bundle(skill_md: Path) -> dict[str, str]:
    """Read a skill bundle into a ``file_cache`` keyed by path relative to the skill root."""
    root = skill_md.parent
    cache: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            cache[str(path.relative_to(root))] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return cache


def raw_metrics(doc: SkillDoc) -> dict[str, float]:
    """Compute every raw statistic for one skill. Keys absent when not measurable."""
    out: dict[str, float] = {}
    prose = doc.all_prose
    if not prose.strip():
        return out

    tokens = _word_tokens(prose)
    out["compression"] = _compression_ratio(prose)
    out["ngram_dup"] = _ngram_dup(tokens, n=5)
    if len(tokens) >= 50:
        out["mtld"] = _mtld(tokens)

    grades, _words = _readability_grades(_prose_for_readability(doc))
    if grades:
        out["readability"] = _median(grades)

    body_terms = _terms(doc.body)
    description = str(doc.data.get("description") or "")
    if body_terms and description:
        idf = _build_idf([body_terms] + [_terms(c) for c in doc.markdown_docs.values()])
        body_vec = _tfidf_vec(body_terms, idf)
        out["cosine_desc"] = _cosine(_tfidf_vec(_terms(description), idf), body_vec)
        if doc.markdown_docs:
            cohesions = [
                _cosine(body_vec, _tfidf_vec(_terms(c), idf)) for c in doc.markdown_docs.values()
            ]
            out["cosine_cohesion"] = sum(cohesions) / len(cohesions)

    # Median demonstration length — the depth signal inside Example Quality.
    from skillspector_quality.quality.scorers import _demonstrations

    demos = _demonstrations(doc)
    if demos:
        lengths = sorted(len(_word_tokens(d)) for d in demos)
        out["example_depth"] = float(lengths[len(lengths) // 2])

    # Instruction Clarity inputs. Both are "lower is better" and bottom out at a real zero.
    from skillspector_quality.quality.scorers import _fence_tags, _hedge_density

    body_prose = _strip_fences_text(doc.body)
    if len(_word_tokens(body_prose)) >= 50:
        out["hedge_density"] = _hedge_density(body_prose)
    tags = _fence_tags(doc.body)
    for content in doc.markdown_docs.values():
        tags.extend(_fence_tags(content))
    if tags:
        out["untagged_fences"] = sum(1 for t in tags if not t) / len(tags)

    # Cost axis: the weighted total is what the cost score is anchored to, and the per-tier
    # raw counts show why the always-on tier dominates despite being the smallest.
    cost = score_cost(doc)
    out["cost_weighted"] = cost.weighted_total
    for tier in cost.tiers:
        out[f"cost_{tier.name.replace('-', '_')}"] = float(tier.raw_tokens)

    out["body_lines"] = float(len(doc.body_lines))
    out["n_docs"] = float(len(doc.markdown_docs))
    return out


@dataclass
class Corpus:
    """Accumulated aggregate observations. Holds no skill-identifying data."""

    metrics: list[dict[str, float]] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    cost_scores: list[float] = field(default_factory=list)
    dimension_fractions: dict[str, list[float]] = field(default_factory=dict)
    link_offenders: dict[str, int] = field(
        default_factory=lambda: {"broken": 0, "case_mismatch": 0, "platform": 0, "redundant": 0}
    )
    skipped: int = 0

    @property
    def n(self) -> int:
        return len(self.scores)

    def observe(self, file_cache: dict[str, str]) -> None:
        doc = SkillDoc.from_file_cache(file_cache)
        metrics = raw_metrics(doc)
        if not metrics:
            self.skipped += 1
            return
        self.metrics.append(metrics)

        hygiene = _link_hygiene(doc)
        self.link_offenders["broken"] += len(hygiene.broken)
        self.link_offenders["case_mismatch"] += len(hygiene.case_mismatch)
        self.link_offenders["platform"] += len(hygiene.platform)
        self.link_offenders["redundant"] += sum(count - 1 for _, count in hygiene.redundant)

        report = score_quality(file_cache)
        self.scores.append(float(report.score))
        self.cost_scores.append(float(score_cost(doc).score))
        for category in report.categories:
            fraction = category.earned / category.max if category.max else 0.0
            self.dimension_fractions.setdefault(category.name, []).append(fraction)


def percentile(values: list[float], q: float) -> float:
    """Nearest-rank percentile. Simple and stable for the corpus sizes involved."""
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = int(round(q * (len(ordered) - 1)))
    return ordered[min(len(ordered) - 1, max(0, index))]


def _spread(values: list[float]) -> dict[str, float]:
    return {
        "n": float(len(values)),
        **{f"p{int(q * 100)}": percentile(values, q) for q in QUANTILES},
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "sd": statistics.pstdev(values),
    }


def summarize(corpus: Corpus) -> dict[str, Any]:
    """Build the aggregate report. Every value is a statistic, never content."""
    metrics: dict[str, dict[str, float]] = {}
    for key in METRIC_ORDER:
        values = [m[key] for m in corpus.metrics if key in m]
        if values:
            metrics[key] = _spread(values)

    dimensions = {
        name: _spread(values) for name, values in sorted(corpus.dimension_fractions.items())
    }

    # Correlate only dimensions observed for every skill; N/A dimensions have ragged
    # vectors that cannot be paired without inventing values.
    complete = [n for n, v in corpus.dimension_fractions.items() if len(v) == corpus.n]
    correlations: list[dict[str, Any]] = []
    for i, a in enumerate(sorted(complete)):
        for b in sorted(complete)[i + 1 :]:
            try:
                r = statistics.correlation(
                    corpus.dimension_fractions[a], corpus.dimension_fractions[b]
                )
            except statistics.StatisticsError:
                continue  # zero-variance dimension: correlation undefined
            correlations.append({"a": a, "b": b, "r": round(r, 3)})
    correlations.sort(key=lambda c: -abs(float(c["r"])))

    return {
        "n_skills": corpus.n,
        "n_skipped": corpus.skipped,
        "total_score": _spread(corpus.scores) if corpus.scores else {},
        "cost_score": _spread(corpus.cost_scores) if corpus.cost_scores else {},
        "metrics": metrics,
        "dimensions": dimensions,
        "correlations": correlations,
        "link_offenders": dict(corpus.link_offenders),
    }


def _table(header: str, rows: dict[str, dict[str, float]], cols: tuple[str, ...]) -> list[str]:
    out = [
        f"### {header}",
        "",
        "| " + " | ".join(("metric", *cols)) + " |",
        "|" + "|".join(["---"] * (len(cols) + 1)) + "|",
    ]
    for name, spread in rows.items():
        cells = [f"{spread[c]:.3f}" if c != "n" else f"{int(spread[c])}" for c in cols]
        out.append("| " + " | ".join((name, *cells)) + " |")
    out.append("")
    return out


def render_markdown(summary: dict[str, Any]) -> str:
    """Aggregate report as markdown. Safe to commit — contains no corpus content."""
    cols = ("n", "p10", "p25", "p50", "p75", "p90", "min", "max")
    lines = [
        "# Quality-scorer calibration report",
        "",
        (
            f"Corpus: **{summary['n_skills']} skills** "
            f"({summary['n_skipped']} skipped as unparseable or empty)."
        ),
        "",
        (
            "Generated by `python benchmarks/calibrate.py <skills-dir>`. Aggregate statistics "
            "only — no skill name, path, or text appears in this file, so the report of a "
            "private corpus is safe to publish."
        ),
        "",
        (
            "These percentiles describe **the corpus that was measured**, which is drawn from a "
            "single ecosystem and shares authors in places. Re-run against a broader corpus to "
            "challenge the anchors in `docs/adr/0007-percentile-calibration.md`."
        ),
        "",
    ]
    total = summary["total_score"]
    if total:
        lines += [
            "## Total score",
            "",
            (
                f"p10 **{total['p10']:.0f}** · p50 **{total['p50']:.0f}** "
                f"· p90 **{total['p90']:.0f}** · min {total['min']:.0f} "
                f"· max {total['max']:.0f} · sd {total['sd']:.1f}"
            ),
            "",
            (
                "A narrow p10–p90 band means the scorer is reporting a near-constant rather "
                "than discriminating between skills."
            ),
            "",
        ]
    lines += [
        "## Raw statistics",
        "",
        "Band edges in `scorers.py` are anchored to these percentiles.",
        "",
    ]
    lines += _table("Distribution", summary["metrics"], cols)
    lines += [
        "## Per-dimension earned fraction",
        "",
        (
            "`sd` near zero means the dimension adds a constant to every score and cannot "
            "rank anything."
        ),
        "",
    ]
    lines += _table("Dimensions", summary["dimensions"], cols)

    lines += [
        "## Dimension correlations",
        "",
        "Computed only over dimensions present for every skill.",
        "",
    ]
    strong = [c for c in summary["correlations"] if abs(float(c["r"])) >= 0.3]
    if strong:
        lines += ["| a | b | r |", "|---|---|---|"]
        lines += [f"| {c['a']} | {c['b']} | {float(c['r']):+.2f} |" for c in strong]
    else:
        lines.append("_No pair reaches |r| >= 0.3._")
    lines.append("")

    offenders = summary["link_offenders"]
    lines += [
        "## Link offenders",
        "",
        f"Across {summary['n_skills']} skills: "
        + ", ".join(f"**{v}** {k.replace('_', '-')}" for k, v in offenders.items()),
        "",
        "A category at zero never fires on this corpus — it is insurance, not a discriminator.",
        "",
    ]
    return "\n".join(lines)


def collect(roots: list[Path]) -> Corpus:
    corpus = Corpus()
    seen: set[Path] = set()
    for root in roots:
        for skill_md in sorted(root.rglob("SKILL.md")):
            resolved = skill_md.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            cache = load_bundle(skill_md)
            if "SKILL.md" not in cache:
                corpus.skipped += 1
                continue
            try:
                corpus.observe(cache)
            except Exception as exc:  # noqa: BLE001 — one bad skill must not abort the sweep
                corpus.skipped += 1
                print(f"skipped a skill ({type(exc).__name__})", file=sys.stderr)
    return corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "roots",
        nargs="*",
        type=Path,
        default=None,
        help="Directory trees to scan for SKILL.md (default: ~/.claude).",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument(
        "-o", "--out", type=Path, default=None, help="Write the report to a file instead of stdout."
    )
    args = parser.parse_args(argv)

    roots: list[Path] = args.roots or [Path.home() / ".claude"]
    missing = [r for r in roots if not r.is_dir()]
    if missing:
        print(f"error: not a directory: {', '.join(str(m) for m in missing)}", file=sys.stderr)
        return 2

    corpus = collect(roots)
    if corpus.n == 0:
        print("error: no scorable skills found", file=sys.stderr)
        return 1

    summary = summarize(corpus)
    text = json.dumps(summary, indent=2) if args.format == "json" else render_markdown(summary)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"Calibration report written to {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Render the quality report for each output format.

Kept separate from the upstream report node so SkillSpector's own formatters stay
untouched; the CLI stitches these in.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO
from typing import Any

import skillspector
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from skillspector_quality.quality.models import QualityReport

_SKILLSPECTOR_VERSION = getattr(skillspector, "__version__", "")

# Scope disclaimer that travels with every report. Guards against the "high score illusion":
# a structurally perfect skill can still be logically broken. Content-correctness cannot be
# measured deterministically, so the score never implies the skill actually works.
QUALITY_CAVEAT = (
    "Note: This score evaluates the structural quality and completeness of your instructions "
    "(syntax, constraints, formatting). It does not guarantee content correctness, factual "
    "accuracy, or prevent model hallucinations. Always functionally test your skill against "
    "real-world inputs."
)

_SEV_COLOR: dict[str, str] = {
    "CRITICAL": "red",
    "HIGH": "red",
    "FAIR": "yellow",
    "GOOD": "green",
    "EXCELLENT": "green",
    "MEDIUM": "yellow",
    "LOW": "green",
}

# Quality score thresholds → (severity label, recommendation).
# Mirrors SkillSpector's risk_severity / risk_recommendation pattern.
_QUALITY_LEVELS: list[tuple[int, str, str]] = [
    (85, "EXCELLENT", "READY TO PUBLISH"),
    (70, "GOOD", "REVIEW RECOMMENDED"),
    (55, "FAIR", "IMPROVE BEFORE PUBLISHING"),
    (40, "POOR", "SIGNIFICANT WORK NEEDED"),
    (0, "CRITICAL", "NOT READY"),
]


def _quality_status(score: int) -> tuple[str, str]:
    """Return (severity, recommendation) for a 0-100 quality score."""
    for threshold, severity, recommendation in _QUALITY_LEVELS:
        if score >= threshold:
            return severity, recommendation
    return "CRITICAL", "NOT READY"


def _score_color(score: int) -> str:
    if score >= 70:
        return "green"
    if score >= 40:
        return "yellow"
    return "red"


# --------------------------------------------------------------------------- #
# Unified terminal renderer (security + quality in one report)                #
# --------------------------------------------------------------------------- #


def unified_terminal_text(result: dict[str, Any], report: QualityReport) -> str:
    """Single cohesive terminal report combining security and quality sections.

    Builds from raw graph state (manifest, component_metadata, filtered_findings,
    risk_score / risk_severity / risk_recommendation) so both halves share one
    header, one component table, and a side-by-side overview.
    """
    console = Console(record=True, force_terminal=True, width=88, file=StringIO())

    manifest: dict[str, Any] = result.get("manifest") or {}
    skill_name: str = manifest.get("name") or "unknown"
    skill_path: str = result.get("skill_path") or result.get("input_path") or ""
    scanned: str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    risk_score: int = result.get("risk_score") or 0
    risk_severity: str = (result.get("risk_severity") or "UNKNOWN").upper()
    risk_rec: str = result.get("risk_recommendation") or ""
    findings: list[Any] = result.get("filtered_findings") or []
    components: list[Any] = result.get("component_metadata") or []

    version_sub = f"v{_SKILLSPECTOR_VERSION}" if _SKILLSPECTOR_VERSION else ""

    # ── Header ──────────────────────────────────────────────────────────────
    console.print(
        Panel(
            f"[bold]Skill:[/bold] {skill_name}\n"
            f"[bold]Source:[/bold] {skill_path}\n"
            f"[bold]Scanned:[/bold] {scanned}",
            title="SkillSpector Report",
            subtitle=version_sub,
        )
    )

    # ── Overview: security + quality side by side ────────────────────────────
    # Both columns are risk scores: 0 = best, 100 = worst.
    # Quality risk = 100 - quality score so the direction matches security.
    sev_color = _SEV_COLOR.get(risk_severity, "white")
    quality_risk = 100 - report.score
    qual_color = _score_color(report.score)
    qual_severity, qual_rec = _quality_status(report.score)

    overview = Table(
        show_header=True,
        box=box.SIMPLE_HEAD,
        title="Overview",
        caption="Risk Score: 0 = best  ·  100 = worst",
    )
    overview.add_column("Dimension", style="bold")
    overview.add_column("Risk Score", justify="right")
    overview.add_column("Status")
    overview.add_row(
        "Security",
        f"[{sev_color}]{risk_score}/100[/{sev_color}]",
        f"[{sev_color}]{risk_severity}  {risk_rec}[/{sev_color}]",
    )
    overview.add_row(
        "Quality",
        f"[{qual_color}]{quality_risk}/100[/{qual_color}]",
        f"[{qual_color}]{qual_severity}  {qual_rec}[/{qual_color}]",
    )
    console.print(overview)

    # ── Components ───────────────────────────────────────────────────────────
    if components:
        ct = Table(
            title=f"Components ({len(components)})",
            show_header=True,
            box=box.SIMPLE_HEAD,
        )
        ct.add_column("File")
        ct.add_column("Type")
        ct.add_column("Lines", justify="right")
        ct.add_column("Executable")
        for comp in components:
            ct.add_row(
                comp.get("path", ""),
                comp.get("type", ""),
                str(comp.get("lines", "")),
                "[yellow]Yes[/yellow]" if comp.get("executable") else "No",
            )
        console.print(ct)

    # ── Security Issues ──────────────────────────────────────────────────────
    console.print(f"\n[bold]Security Issues ({len(findings)})[/bold]")
    if not findings:
        console.print("  [green]No security issues detected.[/green]\n")
    else:
        for f in findings:
            sev = (getattr(f, "severity", "") or "").upper()
            fc = _SEV_COLOR.get(sev, "white")
            loc = f"{getattr(f, 'file', '')}:{getattr(f, 'start_line', '')}"
            pct = int((getattr(f, "confidence", 0) or 0) * 100)
            console.print(
                f"\n  [{fc}]{sev}[/{fc}] [{getattr(f, 'rule_id', '')}]  "
                f"{getattr(f, 'message', '')}",
                highlight=False,
            )
            console.print(f"    [dim]Location: {loc}  |  Confidence: {pct}%[/dim]")
            rem = getattr(f, "remediation", "") or ""
            if rem:
                console.print(f"    [dim]Remediation: {rem.strip()[:120]}[/dim]")

    # ── Quality Dimensions ───────────────────────────────────────────────────
    console.print("\n[bold]Quality Dimensions[/bold]")
    for c in report.categories:
        mark = (
            "[green]+[/green]"
            if c.earned == c.max
            else ("[yellow]~[/yellow]" if c.earned > 0 else "[red]x[/red]")
        )
        kind_tag = r"[dim]\[F][/dim]" if c.kind == "frontmatter" else r"[dim]\[B][/dim]"
        console.print(f"  {mark} {c.earned:>2}/{c.max:<2}  {kind_tag}  {c.name}")
        for _, _, label in c.items:
            console.print(f"      [dim]{label}[/dim]")
        if c.notes:
            console.print(f"      [cyan]tip:[/cyan] {c.notes}")
    console.print(
        "\n  [dim][F] frontmatter — raises score; "
        "no effect on token spend  "
        "[B] prompt body — raises score AND reduces token spend[/dim]"
    )
    console.print(f"\n  [dim]{QUALITY_CAVEAT}[/dim]")

    return console.export_text()


# --------------------------------------------------------------------------- #
# Non-terminal formats (unchanged structure)                                  #
# --------------------------------------------------------------------------- #


def quality_markdown_section(report: QualityReport) -> str:
    """Markdown '## Quality Assessment' section appended to the security report."""
    lines: list[str] = []
    lines.append("\n## Quality Assessment\n")
    lines.append(f"**Score:** {report.score}/100  ")
    lines.append("")
    lines.append("| Category | Kind | Score |")
    lines.append("|----------|------|-------|")
    for c in report.categories:
        kind_label = "frontmatter" if c.kind == "frontmatter" else "body"
        lines.append(f"| {c.name} | {kind_label} | {c.earned}/{c.max} |")
    lines.append("")
    notes = [(c.name, c.notes) for c in report.categories if c.notes]
    if notes:
        lines.append("### Suggestions\n")
        for name, note in notes:
            lines.append(f"- **{name}:** {note}")
        lines.append("")
    lines.append(f"> {QUALITY_CAVEAT}")
    lines.append("")
    return "\n".join(lines)


def quality_json_dict(report: QualityReport) -> dict[str, object]:
    """JSON 'quality_assessment' object (sibling of risk_assessment)."""
    data = report.to_dict()
    data["caveat"] = QUALITY_CAVEAT
    return data


def quality_sarif_properties(report: QualityReport) -> dict[str, object]:
    """Compact summary for SARIF runs[0].properties.quality (not a result)."""
    return {
        "score": report.score,
        "categories": {c.name: {"earned": c.earned, "max": c.max} for c in report.categories},
    }

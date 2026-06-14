"""CLI for skillspector-quality.

Thin wrapper: build initial state, invoke the quality-augmented graph, merge the upstream
security report with the quality block, map to exit code. Mirrors ``skillspector scan``
flags and adds ``--min-score``.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import typer
from langchain_core.runnables import RunnableConfig
from rich.console import Console

from skillspector_quality.graph import graph
from skillspector_quality.quality.models import QualityReport
from skillspector_quality.quality.render import (
    quality_json_dict,
    quality_markdown_section,
    quality_sarif_properties,
    unified_terminal_text,
)

app = typer.Typer(
    name="skillspector-quality",
    help="Quality rating layer for SkillSpector. Adds a 0-100 quality score alongside the security report.",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


class FormatChoice(StrEnum):
    terminal = "terminal"
    json = "json"
    markdown = "markdown"
    sarif = "sarif"


def _merge_output(result: dict[str, Any], fmt: FormatChoice, report: QualityReport) -> str:
    """Combine the upstream security report_body with the quality block."""
    report_body = result.get("report_body") or ""

    if fmt == FormatChoice.terminal:
        return unified_terminal_text(result, report)

    if fmt == FormatChoice.markdown:
        return report_body + "\n" + quality_markdown_section(report)

    if fmt == FormatChoice.json:
        try:
            data = json.loads(report_body) if report_body else {}
        except json.JSONDecodeError:
            data = {}
        data["quality_assessment"] = quality_json_dict(report)
        return json.dumps(data, indent=2)

    # sarif
    sarif = result.get("sarif_report")
    if not isinstance(sarif, dict):
        try:
            sarif = json.loads(report_body)
        except json.JSONDecodeError:
            sarif = {"runs": [{}]}
    runs = sarif.get("runs") or [{}]
    props = runs[0].get("properties") or {}
    props["quality"] = quality_sarif_properties(report)
    runs[0]["properties"] = props
    sarif["runs"] = runs
    return json.dumps(sarif, indent=2)


def _write(text: str, output: Path | None, fmt: FormatChoice) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
        console.print(f"Report saved to: {output}")
    elif fmt == FormatChoice.terminal:
        console.print(text)
    else:
        print(text)


@app.command()
def scan(
    input_path: Annotated[
        str,
        typer.Argument(help="Path or URL to scan (directory, .md, .zip, Git URL, file URL)."),
    ],
    format: Annotated[
        FormatChoice, typer.Option("--format", "-f", help="Output format.", case_sensitive=False)
    ] = FormatChoice.terminal,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write report to file instead of stdout.")
    ] = None,
    no_llm: Annotated[
        bool,
        typer.Option("--no-llm", help="Skip LLM analysis (security + quality stay deterministic)."),
    ] = False,
    yara_rules_dir: Annotated[
        Path | None, typer.Option("--yara-rules-dir", help="Extra YARA rules directory.")
    ] = None,
    min_score: Annotated[
        int | None,
        typer.Option(
            "--min-score",
            help="Fail (exit 1) if the quality score is below this threshold (0-100). Off by default.",
            min=0,
            max=100,
        ),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging.")] = False,
) -> None:
    """Scan a skill for security vulnerabilities AND rate its authoring quality."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")
    result = None
    try:
        state: dict[str, object] = {
            "input_path": input_path,
            "output_format": format.value,
            "use_llm": not no_llm,
        }
        if yara_rules_dir is not None:
            state["yara_rules_dir"] = str(yara_rules_dir.resolve())

        trace_config: RunnableConfig = {"run_name": "skillspector-quality-scan"}
        result = graph.invoke(state, config=trace_config)

        report = QualityReport.from_dict(result.get("quality_report") or {"score": 0})
        _write(_merge_output(result, format, report), output, format)

        # Exit codes: preserve the upstream security risk gate first.
        if (result.get("risk_score") or 0) > 50:
            raise typer.Exit(code=1)
        # Optional quality gate.
        if min_score is not None and report.score < min_score:
            console.print(
                f"[red]Quality gate:[/red] score {report.score} is below --min-score {min_score}"
            )
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2) from e
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=2) from e
    finally:
        if result is not None:
            temp_dir = result.get("temp_dir_for_cleanup")
            if (
                temp_dir
                and isinstance(temp_dir, str)
                and os.path.isdir(temp_dir)
                and os.path.abspath(temp_dir).startswith(tempfile.gettempdir())
            ):
                shutil.rmtree(temp_dir, ignore_errors=True)


@app.callback()
def main() -> None:
    """skillspector-quality — quality rating on top of SkillSpector."""


if __name__ == "__main__":
    app()

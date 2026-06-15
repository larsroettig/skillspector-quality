"""3-arm benchmark: Baseline vs LowQuality vs HighQuality SKILL.md.

Proves skillspector-quality adds measurable value over both "nothing" (Baseline)
and "any SKILL.md" (LowQuality):
  - Baseline     → no SKILL.md; generic extraction instruction only
  - LowQuality   → bad SKILL.md body (conversational, no schema, no example)
  - HighQuality  → SKILL.md improved by skillspector-quality recommendations

Two separated metrics per cell (mirrors ponytail benchmark pattern):
  - output_tokens  : always measured — how verbose is the LLM?
  - schema_correct : pass/fail gate — did the LLM return the right structure?

Provider selection via environment variables:

    # OpenAI (default)
    export SKILLSPECTOR_PROVIDER=openai
    export OPENAI_API_KEY=sk-...

    # Anthropic
    export SKILLSPECTOR_PROVIDER=anthropic
    export ANTHROPIC_API_KEY=sk-ant-...

    # NVIDIA build.nvidia.com
    export SKILLSPECTOR_PROVIDER=nv_build
    export NVIDIA_INFERENCE_KEY=nvapi-...

    # Local Ollama or any OpenAI-compatible endpoint
    export SKILLSPECTOR_PROVIDER=openai
    export OPENAI_API_KEY=ollama
    export OPENAI_BASE_URL=http://localhost:11434/v1
    export SKILLSPECTOR_MODEL=llama3.1:8b

Usage:
    python benchmarks/run_benchmark.py                   # N=5 repeats, all scenarios
    python benchmarks/run_benchmark.py --dry-run         # quality scores only, no LLM calls
    python benchmarks/run_benchmark.py --repeats 3       # fewer repeats
    python benchmarks/run_benchmark.py --ollama-all      # every pulled Ollama model (N=3)
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import statistics
import sys
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from skillspector_quality.quality import score_quality  # noqa: E402

from benchmarks.scenarios import SCENARIOS, Arm, Scenario  # noqa: E402
from benchmarks.validators import validate  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

N_REPEATS = 10
N_REPEATS_OLLAMA_ALL = 5
N_REPEATS_ANTHROPIC_ALL = 10

_ANTHROPIC_MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-8",
]
DEFAULT_TEMPERATURE = 0.3

_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "nv_build": "meta/llama-3.1-8b-instruct",
}
_NV_BUILD_BASE_URL = "https://integrate.api.nvidia.com/v1"
_OLLAMA_DEFAULT_URL = "http://localhost:11434/v1"
_VALID_PROVIDERS = frozenset(_DEFAULT_MODELS)

_RESULTS_DIR = _REPO_ROOT / "benchmarks" / "results"

# t-distribution 95% CI critical values (two-tailed, df = n-1)
_T_CRIT: dict[int, float] = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447,  7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
}

_BASELINE_PROMPT = (
    "Extract the relevant information from the text below and return ONLY valid JSON.\n"
    "Do not include any explanation, markdown formatting, or code fences — "
    "output only the raw JSON object.\n\n"
    "Text: {input}"
)


# ─────────────────────────────────────────────────────────────────────────────
# Per-run result dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class RunResult:
    scenario: str
    arm: str
    run: int
    output_tokens: int
    total_tokens: int
    latency: float
    correct: bool
    reason: str
    prompt: str = ""
    output: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Provider helpers
# ─────────────────────────────────────────────────────────────────────────────


def _resolve_provider() -> tuple[str, str]:
    provider = os.environ.get("SKILLSPECTOR_PROVIDER", "openai").lower()
    if provider not in _VALID_PROVIDERS:
        print(
            f"❌  Unknown SKILLSPECTOR_PROVIDER={provider!r}. "
            f"Choose from: {', '.join(sorted(_VALID_PROVIDERS))}"
        )
        sys.exit(1)
    model = os.environ.get("SKILLSPECTOR_MODEL") or _DEFAULT_MODELS[provider]
    return provider, model


def _make_client(provider: str, *, base_url: str | None = None, api_key: str | None = None) -> Any:
    if provider == "anthropic":
        try:
            from anthropic import Anthropic  # noqa: PLC0415
        except ImportError:
            print("❌  anthropic package not installed.  Run: pip install anthropic")
            sys.exit(1)
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None
        return Anthropic(api_key=key)

    try:
        from openai import OpenAI  # noqa: PLC0415
    except ImportError:
        print("❌  openai package not installed.  Run: pip install openai")
        sys.exit(1)

    if provider == "nv_build":
        key = api_key or os.environ.get("NVIDIA_INFERENCE_KEY")
        if not key:
            return None
        return OpenAI(api_key=key, base_url=_NV_BUILD_BASE_URL)

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    url = base_url or os.environ.get("OPENAI_BASE_URL")
    return OpenAI(api_key=key, base_url=url) if url else OpenAI(api_key=key)


def _provider_display(provider: str, base_url: str | None = None) -> str:
    labels = {"openai": "OpenAI", "anthropic": "Anthropic", "nv_build": "NVIDIA build.nvidia.com"}
    label = labels.get(provider, provider)
    url = base_url or os.environ.get("OPENAI_BASE_URL")
    if provider == "openai" and url:
        label = f"OpenAI-compatible ({url})"
    return label


# ─────────────────────────────────────────────────────────────────────────────
# Core helpers
# ─────────────────────────────────────────────────────────────────────────────


def _extract_body(skill_md: str) -> str:
    if not skill_md.startswith("---"):
        return skill_md
    end = skill_md.find("\n---", 3)
    return skill_md[end + 4 :].lstrip("\n") if end != -1 else skill_md


def _build_prompt(arm: Arm, scenario: Scenario) -> str:
    """Build the LLM prompt for an arm × scenario cell.

    A unique nonce is appended so that every API call has a distinct prompt.
    This prevents two classes of caching that would corrupt the benchmark:
      1. Exact-match output caching (local proxies, some hosted endpoints) —
         identical prompts return a stored completion instead of a fresh one.
      2. Anthropic / OpenAI KV prompt-cache hits — warm cache reduces TTFT for
         runs 2-N, making latency measurements for repeat calls artificially fast.
    The nonce is an HTML comment placed after all task content; the model ignores it.
    """
    if arm.skill_md is None:
        base = _BASELINE_PROMPT.replace("{input}", scenario.test_input)
    else:
        body = _extract_body(arm.skill_md)
        base = body.replace("{input}", scenario.test_input)
    nonce = uuid.uuid4().hex[:12]
    return f"{base}\n\n<!-- {nonce} -->"


def _body_score(report: Any) -> int:
    """Quality score for body-only dimensions (kind == 'body'), 0-100."""
    earned = sum(c.earned for c in report.categories if c.kind == "body")
    max_ = sum(c.max for c in report.categories if c.kind == "body")
    return round(earned / max_ * 100) if max_ else 0


def _tier(score: int) -> str:
    if score >= 85:
        return "EXCELLENT"
    if score >= 70:
        return "GOOD"
    if score >= 55:
        return "FAIR"
    if score >= 40:
        return "POOR"
    return "CRITICAL"


def _model_slug(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", model)


def _run_stats(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "ci95": 0.0, "n": 0}
    mean = statistics.mean(values)
    if n < 2:
        return {"mean": round(mean, 4), "std": 0.0, "ci95": 0.0, "n": n}
    std = statistics.stdev(values)
    t = _T_CRIT.get(n - 1, 1.96)
    ci95 = t * std / (n ** 0.5)
    return {"mean": round(mean, 4), "std": round(std, 4), "ci95": round(ci95, 4), "n": n}


# ─────────────────────────────────────────────────────────────────────────────
# Error handling + LLM call
# ─────────────────────────────────────────────────────────────────────────────


def _explain_llm_error(exc: Exception, provider: str, model: str, base_url: str = "") -> None:
    is_local = "localhost" in base_url or "127.0.0.1" in base_url

    _openai_not_found: tuple[type, ...] = ()
    _openai_conn_err: tuple[type, ...] = ()
    _openai_auth_err: tuple[type, ...] = ()
    _anthropic_not_found: tuple[type, ...] = ()
    _anthropic_conn_err: tuple[type, ...] = ()

    try:
        import openai as _oai  # noqa: PLC0415
        _openai_not_found = (_oai.NotFoundError,)
        _openai_conn_err = (_oai.APIConnectionError,)
        _openai_auth_err = (_oai.AuthenticationError,)
    except ImportError:
        pass
    try:
        import anthropic as _ant  # noqa: PLC0415
        _anthropic_not_found = (_ant.NotFoundError,)
        _anthropic_conn_err = (_ant.APIConnectionError,)
    except ImportError:
        pass

    if _openai_not_found and isinstance(exc, _openai_not_found):
        if is_local:
            print(f"\n❌  Model '{model}' not found in Ollama.")
            print(f"    Pull it first:        ollama pull {model}")
            print(f"    List pulled models:   ollama list")
        else:
            print(f"\n❌  Model '{model}' not found at {base_url or 'the endpoint'}.")
            print("    Check SKILLSPECTOR_MODEL or the provider's model catalogue.")
        return
    if _openai_conn_err and isinstance(exc, _openai_conn_err):
        if is_local:
            print(f"\n❌  Could not connect to {base_url}.")
            print("    Start Ollama first:   ollama serve")
        else:
            print(f"\n❌  Could not connect to {base_url or 'the API'}.")
        return
    if _openai_auth_err and isinstance(exc, _openai_auth_err):
        key_var = {"openai": "OPENAI_API_KEY", "nv_build": "NVIDIA_INFERENCE_KEY"}.get(provider, "API key")
        print(f"\n❌  Authentication failed. Check {key_var}.")
        return
    if _anthropic_not_found and isinstance(exc, _anthropic_not_found):
        print(f"\n❌  Model '{model}' not found at Anthropic. Check SKILLSPECTOR_MODEL.")
        return
    if _anthropic_conn_err and isinstance(exc, _anthropic_conn_err):
        print("\n❌  Could not connect to Anthropic. Check ANTHROPIC_API_KEY.")
        return
    print(f"\n❌  LLM call failed: {exc}")


def _call_llm(
    client: Any,
    prompt: str,
    label: str,
    provider: str,
    model: str,
    *,
    base_url: str = "",
    temperature: float = DEFAULT_TEMPERATURE,
) -> dict[str, Any]:
    t0 = time.time()
    try:
        if provider == "anthropic":
            kwargs: dict[str, Any] = dict(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            try:
                response = client.messages.create(**kwargs)
            except Exception as exc:
                if "temperature" in str(exc) and "deprecated" in str(exc):
                    del kwargs["temperature"]
                    response = client.messages.create(**kwargs)
                else:
                    raise
            content = response.content[0].text if response.content else ""
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
    except Exception as exc:
        _explain_llm_error(exc, provider, model, base_url)
        sys.exit(1)

    return {
        "label": label,
        "latency": time.time() - t0,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "prompt": prompt,
        "output": content,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Ollama discovery
# ─────────────────────────────────────────────────────────────────────────────


def _list_ollama_models(base_url: str) -> list[str]:
    try:
        from openai import OpenAI, APIConnectionError  # noqa: PLC0415
    except ImportError:
        print("❌  openai package not installed.  Run: pip install openai")
        sys.exit(1)
    try:
        client = OpenAI(api_key="ollama", base_url=base_url)
        return [m.id for m in client.models.list().data]
    except APIConnectionError:
        print(f"❌  Could not connect to Ollama at {base_url}.")
        print("    Start Ollama first:  ollama serve")
        sys.exit(1)
    except Exception as exc:
        print(f"❌  Failed to list Ollama models: {exc}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Quality scoring helpers
# ─────────────────────────────────────────────────────────────────────────────


def _score_arm(arm: Arm) -> tuple[int, int]:
    """Return (overall_score, body_score) for an arm, or (0, 0) for Baseline."""
    if arm.skill_md is None:
        return 0, 0
    report = score_quality({"SKILL.md": arm.skill_md})
    return report.score, _body_score(report)


# ─────────────────────────────────────────────────────────────────────────────
# Results formatting
# ─────────────────────────────────────────────────────────────────────────────


def _median_or_zero(vals: list[int]) -> float:
    return statistics.median(vals) if vals else 0.0


def _format_table(
    all_results: list[RunResult],
    scenarios: list[Scenario],
    arm_scores: dict[tuple[str, str], tuple[int, int]],
    n_repeats: int,
) -> list[str]:
    """Build the summary comparison table as a list of text lines."""
    lines: list[str] = []
    arm_names = ["Baseline", "LowQuality", "HighQuality"]
    w = 74

    lines.append("═" * w)
    lines.append(f"  {'Scenario':<28} {'Arm':<14} {'Body':>5}  {'Out-tok(med)':>12}  {'Correct':>9}")
    lines.append(f"  {'─' * (w - 2)}")

    # Per-scenario rows
    for scenario in scenarios:
        for arm_name in arm_names:
            cell = [r for r in all_results if r.scenario == scenario.name and r.arm == arm_name]
            overall, body = arm_scores.get((scenario.name, arm_name), (0, 0))
            out_toks = [r.output_tokens for r in cell]
            correct_n = sum(1 for r in cell if r.correct)
            n = len(cell)
            med = f"{_median_or_zero(out_toks):.0f}" if out_toks else "—"
            correct_str = f"{correct_n}/{n}" if n else "—"
            star = " ✓" if correct_n == n and n > 0 else ""
            body_str = str(body) if arm_name != "Baseline" else "—"
            lines.append(
                f"  {scenario.name:<28} {arm_name:<14} {body_str:>5}  {med:>12}  {correct_str:>7}{star}"
            )
        lines.append(f"  {'·' * (w - 2)}")

    # Aggregate rows
    lines.append(f"  {'─' * (w - 2)}")
    for arm_name in arm_names:
        arm_results = [r for r in all_results if r.arm == arm_name]
        out_toks = [r.output_tokens for r in arm_results]
        correct_n = sum(1 for r in arm_results if r.correct)
        n = len(arm_results)
        med = f"{_median_or_zero(out_toks):.0f}" if out_toks else "—"
        correct_str = f"{correct_n}/{n}" if n else "—"
        pct = f" ({100 * correct_n // n}%)" if n else ""
        # Average body score across scenarios (excluding Baseline)
        if arm_name != "Baseline":
            body_vals = [arm_scores.get((s.name, arm_name), (0, 0))[1] for s in scenarios]
            avg_body = f"~{round(sum(body_vals) / len(body_vals))}" if body_vals else "—"
        else:
            avg_body = "—"
        lines.append(
            f"  {'AGGREGATE':<28} {arm_name:<14} {avg_body:>5}  {med:>12}  {correct_str:>7}{pct}"
        )
    lines.append("═" * w)
    return lines


def _markdown_report(
    all_results: list[RunResult],
    scenarios: list[Scenario],
    arm_scores: dict[tuple[str, str], tuple[int, int]],
    provider: str,
    model: str,
    n_repeats: int,
    temperature: float,
    base_url: str,
) -> str:
    """Build the markdown result file content."""
    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    arm_names = ["Baseline", "LowQuality", "HighQuality"]

    lines: list[str] = []
    lines.append(f"# Benchmark Results — {date_str}")
    lines.append("")
    lines.append(f"**Provider:** {_provider_display(provider, base_url)}  ")
    lines.append(f"**Model:** `{model}`  ")
    lines.append(f"**Repeats:** {n_repeats} per cell  ")
    lines.append(f"**Temperature:** {temperature}  ")
    lines.append(f"**Scenarios:** {len(scenarios)}  ")
    lines.append(f"**Arms:** Baseline · LowQuality · HighQuality  ")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "- **Baseline** — generic extraction prompt, no SKILL.md  \n"
        "- **LowQuality** — SKILL.md with conversational body, no schema, no example  \n"
        "- **HighQuality** — SKILL.md improved by skillspector-quality recommendations  \n"
    )
    lines.append(
        "Two metrics per cell: `output_tokens` (measurement) + `schema_correct` (gate).  \n"
        "Reported values: median output tokens across N repeats, correct count out of N."
    )
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(f"| Scenario | Arm | Body score | Output tok (med) | Correct/{n_repeats} |")
    lines.append("|----------|-----|:----------:|:----------------:|:-------:|")

    for scenario in scenarios:
        for arm_name in arm_names:
            cell = [r for r in all_results if r.scenario == scenario.name and r.arm == arm_name]
            _, body = arm_scores.get((scenario.name, arm_name), (0, 0))
            out_toks = [r.output_tokens for r in cell]
            correct_n = sum(1 for r in cell if r.correct)
            n = len(cell)
            med = f"{_median_or_zero(out_toks):.0f}" if out_toks else "—"
            correct_str = f"{correct_n}/{n}"
            body_str = str(body) if arm_name != "Baseline" else "—"
            mark = " ✓" if correct_n == n and n > 0 else ""
            lines.append(f"| {scenario.name} | {arm_name} | {body_str} | {med} | {correct_str}{mark} |")

    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"| Arm | Avg body score | Output tok (med) | Correct rate |")
    lines.append("|-----|:--------------:|:----------------:|:------------:|")
    for arm_name in arm_names:
        arm_results = [r for r in all_results if r.arm == arm_name]
        out_toks = [r.output_tokens for r in arm_results]
        correct_n = sum(1 for r in arm_results if r.correct)
        n = len(arm_results)
        med = f"{_median_or_zero(out_toks):.0f}" if out_toks else "—"
        pct = f"{100 * correct_n // n}%" if n else "—"
        if arm_name != "Baseline":
            body_vals = [arm_scores.get((s.name, arm_name), (0, 0))[1] for s in scenarios]
            avg_body = f"~{round(sum(body_vals) / len(body_vals))}" if body_vals else "—"
        else:
            avg_body = "—"
        lines.append(f"| {arm_name} | {avg_body} | {med} | {pct} |")

    lines.append("")
    lines.append("## Per-run detail")
    lines.append("")
    lines.append("| Scenario | Arm | Run | Output tok | Correct | Reason |")
    lines.append("|----------|-----|:---:|:----------:|:-------:|--------|")
    for r in all_results:
        mark = "✓" if r.correct else "✗"
        reason = r.reason if not r.correct else ""
        lines.append(f"| {r.scenario} | {r.arm} | {r.run} | {r.output_tokens} | {mark} | {reason} |")

    lines.append("")
    lines.append(
        f"*Generated by [skillspector-quality](https://github.com) "
        f"benchmark runner on {date_str}.*"
    )
    return "\n".join(lines) + "\n"


def _save_markdown(
    all_results: list[RunResult],
    scenarios: list[Scenario],
    arm_scores: dict[tuple[str, str], tuple[int, int]],
    provider: str,
    model: str,
    n_repeats: int,
    temperature: float,
    base_url: str,
) -> Path:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    slug = _model_slug(model)
    provider_slug = provider.replace("_", "-")
    path = _RESULTS_DIR / f"{date_str}-{provider_slug}-{slug}.md"
    content = _markdown_report(
        all_results, scenarios, arm_scores, provider, model, n_repeats, temperature, base_url
    )
    path.write_text(content, encoding="utf-8")
    return path


def _save_json(
    all_results: list[RunResult],
    provider: str,
    model: str,
    n_repeats: int,
    temperature: float,
) -> Path:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    slug = _model_slug(model)
    provider_slug = provider.replace("_", "-")
    path = _RESULTS_DIR / f"{date_str}-{provider_slug}-{slug}.json"
    payload = {
        "provider": provider,
        "model": model,
        "n_repeats": n_repeats,
        "temperature": temperature,
        "date": date_str,
        "runs": [
            {
                "scenario": r.scenario,
                "arm": r.arm,
                "run": r.run,
                "output_tokens": r.output_tokens,
                "total_tokens": r.total_tokens,
                "latency": round(r.latency, 3),
                "correct": r.correct,
                "reason": r.reason,
                "prompt": r.prompt,
                "output": r.output,
            }
            for r in all_results
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Single-model runner
# ─────────────────────────────────────────────────────────────────────────────


def _run_benchmark(
    client: Any,
    provider: str,
    model: str,
    base_url: str,
    n_repeats: int,
    temperature: float,
    *,
    dry_run: bool = False,
) -> tuple[list[RunResult], dict[tuple[str, str], tuple[int, int]]]:
    """Run all scenarios × all arms × n_repeats and return (results, arm_scores)."""
    all_results: list[RunResult] = []

    # Pre-compute quality scores (deterministic, no LLM)
    arm_scores: dict[tuple[str, str], tuple[int, int]] = {}
    for scenario in SCENARIOS:
        for arm in scenario.arms:
            arm_scores[(scenario.name, arm.name)] = _score_arm(arm)

    if dry_run:
        return all_results, arm_scores

    arm_names = ["Baseline", "LowQuality", "HighQuality"]
    n_scenarios = len(SCENARIOS)
    n_arms = len(arm_names)
    total = n_scenarios * n_arms * n_repeats

    print(f"  {n_scenarios} scenarios · {n_arms} arms · {n_repeats} repeats = {total} LLM calls")
    print()

    for scenario in SCENARIOS:
        print(f"  ── {scenario.name}")
        for arm in scenario.arms:
            prompt = _build_prompt(arm, scenario)
            overall, body = arm_scores[(scenario.name, arm.name)]
            body_str = f"body={body}" if arm.name != "Baseline" else "baseline"
            for run_idx in range(1, n_repeats + 1):
                result = _call_llm(
                    client, prompt,
                    label=f"{scenario.name}/{arm.name}/{run_idx}",
                    provider=provider, model=model,
                    base_url=base_url, temperature=temperature,
                )
                correct, reason = validate(
                    result["output"],
                    scenario.required_keys,
                    scenario.expected,
                    scenario.enum_fields,
                )
                mark = "✓" if correct else "✗"
                print(
                    f"     {arm.name:<14} run {run_idx}/{n_repeats}  "
                    f"{result['completion_tokens']:>4} out-tok  "
                    f"{result['latency']:.1f}s  {mark}  {body_str}"
                )
                all_results.append(RunResult(
                    scenario=scenario.name,
                    arm=arm.name,
                    run=run_idx,
                    output_tokens=result["completion_tokens"],
                    total_tokens=result["total_tokens"],
                    latency=result["latency"],
                    correct=correct,
                    reason=reason,
                    prompt=result["prompt"],
                    output=result["output"],
                ))
        print()

    return all_results, arm_scores


# ─────────────────────────────────────────────────────────────────────────────
# Single-model entry point
# ─────────────────────────────────────────────────────────────────────────────


def main(dry_run: bool = False, n_repeats: int = N_REPEATS) -> None:
    provider, model = _resolve_provider()
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    temperature = float(os.environ.get("SKILLSPECTOR_TEMPERATURE", DEFAULT_TEMPERATURE))

    client = None
    if not dry_run:
        client = _make_client(provider, base_url=base_url or None)
        if client is None:
            key_var = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "nv_build": "NVIDIA_INFERENCE_KEY",
            }.get(provider, "API_KEY")
            print(f"⚠️  {key_var} not set — switching to dry-run (quality scoring only).\n")
            dry_run = True

    sep = "═" * 74
    print(f"\n{sep}")
    print(f"  skillspector-quality Benchmark")
    if dry_run:
        print(f"  (dry-run: quality scoring only, no LLM calls)")
    else:
        print(
            f"  provider={_provider_display(provider, base_url)}  "
            f"model={model}  N={n_repeats}  temp={temperature}"
        )
    print(sep)

    # ── Quality scores (always shown, even in dry-run) ────────────────────────
    print(f"\n  Quality scores per arm (body = dimensions that reach the LLM):\n")
    arm_header_done = False
    for scenario in SCENARIOS:
        if not arm_header_done:
            print(f"  {'Scenario':<28} {'Arm':<14} {'Overall':>8}  {'Body':>5}  {'Tier'}")
            print(f"  {'─' * 60}")
            arm_header_done = True
        for arm in scenario.arms:
            overall, body = _score_arm(arm)
            if arm.name == "Baseline":
                print(f"  {scenario.name:<28} {arm.name:<14} {'—':>8}  {'—':>5}  generic prompt")
            else:
                print(
                    f"  {scenario.name:<28} {arm.name:<14} {overall:>8}  {body:>5}  "
                    f"{_tier(overall)}"
                )
    print()

    if dry_run:
        return

    # ── Run benchmark ─────────────────────────────────────────────────────────
    all_results, arm_scores = _run_benchmark(
        client, provider, model, base_url, n_repeats, temperature
    )

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  RESULTS  model={model}  N={n_repeats}  temp={temperature}")
    print(sep)
    table_lines = _format_table(all_results, SCENARIOS, arm_scores, n_repeats)
    for line in table_lines:
        print(line)

    # ── Save results ──────────────────────────────────────────────────────────
    saved = _save_markdown(all_results, SCENARIOS, arm_scores, provider, model, n_repeats, temperature, base_url)
    saved_json = _save_json(all_results, provider, model, n_repeats, temperature)
    print(f"\n  Results saved to: {saved.relative_to(_REPO_ROOT)}")
    print(f"  Raw I/O saved to: {saved_json.relative_to(_REPO_ROOT)}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# --ollama-all entry point
# ─────────────────────────────────────────────────────────────────────────────


def main_ollama_all(n_repeats: int = N_REPEATS_OLLAMA_ALL) -> None:
    base_url = os.environ.get("OPENAI_BASE_URL", _OLLAMA_DEFAULT_URL)
    temperature = float(os.environ.get("SKILLSPECTOR_TEMPERATURE", DEFAULT_TEMPERATURE))
    benchmark_model = os.environ.get("SKILLSPECTOR_BENCHMARK_MODEL", "").strip()

    print(f"\n🔍  Discovering models at {base_url}...")
    discovered = _list_ollama_models(base_url)

    if not discovered:
        print("❌  No models found in Ollama. Pull at least one:")
        print("    ollama pull llama3.1:8b")
        sys.exit(1)

    if benchmark_model and benchmark_model not in discovered:
        print(f"⚠️  SKILLSPECTOR_BENCHMARK_MODEL='{benchmark_model}' is not pulled — ignoring.")
        benchmark_model = ""
    if not benchmark_model:
        benchmark_model = discovered[0]

    ordered = [benchmark_model] + sorted(m for m in discovered if m != benchmark_model)

    print(f"    Found {len(discovered)} model(s):  {', '.join(ordered)}")
    print(f"    Benchmark (reference) model: ★ {benchmark_model}")
    print(f"    Repeats per cell: {n_repeats}")
    print(f"    Results directory:  {_RESULTS_DIR.relative_to(_REPO_ROOT)}/\n")

    client = _make_client("openai", base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY", "ollama"))
    summary_rows: list[dict[str, Any]] = []

    for model in ordered:
        is_bench = model == benchmark_model
        marker = " ★ benchmark" if is_bench else ""
        sep = "═" * 70
        print(f"\n{sep}")
        print(f"  {model}{marker}")
        print(sep)

        all_results, arm_scores = _run_benchmark(
            client, "openai", model, base_url, n_repeats, temperature
        )

        saved = _save_markdown(all_results, SCENARIOS, arm_scores, "openai", model, n_repeats, temperature, base_url)
        _save_json(all_results, "openai", model, n_repeats, temperature)

        # Aggregate stats for comparison table
        for arm_name in ["Baseline", "LowQuality", "HighQuality"]:
            arm_results = [r for r in all_results if r.arm == arm_name]
            out_toks = [r.output_tokens for r in arm_results]
            correct_n = sum(1 for r in arm_results if r.correct)
            n = len(arm_results)
            summary_rows.append({
                "model": model,
                "is_bench": is_bench,
                "arm": arm_name,
                "med_out_tok": _median_or_zero(out_toks),
                "correct_pct": 100 * correct_n // n if n else 0,
                "n": n,
            })

        print(f"\n  ✅  Results saved to: {saved.name}\n")

    # ── Cross-model comparison table ─────────────────────────────────────────
    width = 76
    print(f"\n{'═' * width}")
    print(f"  CROSS-MODEL COMPARISON  (★ = benchmark reference)")
    print(f"{'═' * width}")
    print(
        f"  {'Model':<30} {'Arm':<14} {'Out-tok(med)':>12}  {'Correct':>8}"
    )
    print(f"  {'─' * (width - 2)}")

    current_model = ""
    for row in summary_rows:
        star = "★ " if row["is_bench"] and row["arm"] == "Baseline" else "  "
        model_str = row["model"] if row["model"] != current_model else ""
        current_model = row["model"]
        print(
            f"  {star}{model_str:<28} {row['arm']:<14} "
            f"{row['med_out_tok']:>12.0f}  {row['correct_pct']:>7}%"
        )

    print(f"\n  Results saved to: {_RESULTS_DIR.relative_to(_REPO_ROOT)}/")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# --anthropic-all entry point
# ─────────────────────────────────────────────────────────────────────────────


def main_anthropic_all(n_repeats: int = N_REPEATS_ANTHROPIC_ALL) -> None:
    """Run the benchmark against all three Anthropic models and print a comparison table."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY not set.")
        print("    export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    temperature = float(os.environ.get("SKILLSPECTOR_TEMPERATURE", DEFAULT_TEMPERATURE))
    models = _ANTHROPIC_MODELS

    print(f"\n{'═' * 70}")
    print(f"  skillspector-quality  ·  Anthropic  ·  {len(models)} models")
    print(f"  Repeats per cell: {n_repeats}  ·  Temperature: {temperature}")
    print(f"{'═' * 70}\n")

    client = _make_client("anthropic", api_key=api_key)
    summary_rows: list[dict[str, Any]] = []

    for model in models:
        sep = "═" * 70
        print(f"\n{sep}")
        print(f"  {model}")
        print(sep)

        all_results, arm_scores = _run_benchmark(
            client, "anthropic", model, "", n_repeats, temperature
        )

        saved = _save_markdown(all_results, SCENARIOS, arm_scores, "anthropic", model, n_repeats, temperature, "")
        _save_json(all_results, "anthropic", model, n_repeats, temperature)

        for arm_name in ["Baseline", "LowQuality", "HighQuality"]:
            arm_results = [r for r in all_results if r.arm == arm_name]
            out_toks = [r.output_tokens for r in arm_results]
            correct_n = sum(1 for r in arm_results if r.correct)
            n = len(arm_results)
            summary_rows.append({
                "model": model,
                "arm": arm_name,
                "med_out_tok": _median_or_zero(out_toks),
                "correct_pct": 100 * correct_n // n if n else 0,
                "n": n,
            })

        print(f"\n  ✅  Saved: {saved.name}\n")

    # ── Cross-model comparison ────────────────────────────────────────────────
    width = 76
    print(f"\n{'═' * width}")
    print(f"  CROSS-MODEL COMPARISON  (Anthropic)")
    print(f"{'═' * width}")
    print(f"  {'Model':<32} {'Arm':<14} {'Out-tok(med)':>12}  {'Correct':>8}")
    print(f"  {'─' * (width - 2)}")

    current_model = ""
    for row in summary_rows:
        model_str = row["model"] if row["model"] != current_model else ""
        current_model = row["model"]
        print(
            f"  {model_str:<32} {row['arm']:<14} "
            f"{row['med_out_tok']:>12.0f}  {row['correct_pct']:>7}%"
        )

    print(f"\n  Results saved to: {_RESULTS_DIR.relative_to(_REPO_ROOT)}/")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# Multi-model entry point
# ─────────────────────────────────────────────────────────────────────────────


def main_multi_model(models: list[str], n_repeats: int = N_REPEATS) -> None:
    """Run the benchmark against a user-specified list of models on the current provider."""
    provider, _ = _resolve_provider()
    base_url = os.environ.get("OPENAI_BASE_URL", "")
    temperature = float(os.environ.get("SKILLSPECTOR_TEMPERATURE", DEFAULT_TEMPERATURE))

    key_var = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "nv_build": "NVIDIA_INFERENCE_KEY",
    }.get(provider, "API_KEY")
    api_key = os.environ.get(key_var)
    client = _make_client(provider, base_url=base_url or None, api_key=api_key)
    if client is None:
        print(f"❌  {key_var} not set.")
        sys.exit(1)

    width = 76
    print(f"\n{'═' * width}")
    print(
        f"  skillspector-quality  ·  {_provider_display(provider, base_url)}"
        f"  ·  {len(models)} model(s)"
    )
    print(f"  Repeats per cell: {n_repeats}  ·  Temperature: {temperature}")
    print(f"{'═' * width}\n")

    summary_rows: list[dict[str, Any]] = []

    for model in models:
        sep = "═" * width
        print(f"\n{sep}")
        print(f"  {model}")
        print(sep)

        all_results, arm_scores = _run_benchmark(
            client, provider, model, base_url, n_repeats, temperature
        )
        saved = _save_markdown(
            all_results, SCENARIOS, arm_scores, provider, model, n_repeats, temperature, base_url
        )
        _save_json(all_results, provider, model, n_repeats, temperature)

        for arm_name in ["Baseline", "LowQuality", "HighQuality"]:
            arm_results = [r for r in all_results if r.arm == arm_name]
            out_toks = [r.output_tokens for r in arm_results]
            correct_n = sum(1 for r in arm_results if r.correct)
            n = len(arm_results)
            summary_rows.append({
                "model": model,
                "arm": arm_name,
                "med_out_tok": _median_or_zero(out_toks),
                "correct_pct": 100 * correct_n // n if n else 0,
                "n": n,
            })

        print(f"\n  ✅  Saved: {saved.name}\n")

    # Cross-model comparison table
    print(f"\n{'═' * width}")
    print(f"  CROSS-MODEL COMPARISON  ({_provider_display(provider, base_url)})")
    print(f"{'═' * width}")
    print(f"  {'Model':<32} {'Arm':<14} {'Out-tok(med)':>12}  {'Correct':>8}")
    print(f"  {'─' * (width - 2)}")

    current_model = ""
    for row in summary_rows:
        model_str = row["model"] if row["model"] != current_model else ""
        current_model = row["model"]
        print(
            f"  {model_str:<32} {row['arm']:<14} "
            f"{row['med_out_tok']:>12.0f}  {row['correct_pct']:>7}%"
        )

    print(f"\n  Results saved to: {_RESULTS_DIR.relative_to(_REPO_ROOT)}/")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python benchmarks/run_benchmark.py",
        description="skillspector-quality 3-arm benchmark (Baseline · LowQuality · HighQuality)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""\
            Provider is selected via SKILLSPECTOR_PROVIDER (openai|anthropic|nv_build).
            Model is selected via SKILLSPECTOR_MODEL (falls back to provider default).
            Temperature via SKILLSPECTOR_TEMPERATURE (default {DEFAULT_TEMPERATURE}).

            Examples:
              # Single model, N=10
              python benchmarks/run_benchmark.py

              # Override repeats
              python benchmarks/run_benchmark.py -n 3

              # Two specific Anthropic models
              export SKILLSPECTOR_PROVIDER=anthropic
              python benchmarks/run_benchmark.py --models claude-haiku-4-5-20251001,claude-sonnet-4-6

              # All Anthropic models
              python benchmarks/run_benchmark.py --anthropic-all

              # All pulled Ollama models
              python benchmarks/run_benchmark.py --ollama-all

              # Quality scoring only, no LLM calls
              python benchmarks/run_benchmark.py --dry-run
        """),
    )
    p.add_argument(
        "-n", "--repeats",
        type=int,
        default=None,
        metavar="N",
        help=(
            "repeats per cell "
            f"(default: {N_REPEATS} for single/--models, "
            f"{N_REPEATS_ANTHROPIC_ALL} for --anthropic-all, "
            f"{N_REPEATS_OLLAMA_ALL} for --ollama-all)"
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print quality scores only — no LLM calls",
    )
    p.add_argument(
        "--models",
        metavar="MODEL[,MODEL,...]",
        help=(
            "comma-separated list of models to run against the current provider "
            "(SKILLSPECTOR_PROVIDER); prints a cross-model comparison table when done"
        ),
    )
    p.add_argument(
        "--anthropic-all",
        action="store_true",
        help=f"run all Anthropic models: {', '.join(_ANTHROPIC_MODELS)}",
    )
    p.add_argument(
        "--ollama-all",
        action="store_true",
        help="discover and benchmark every pulled Ollama model",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.ollama_all:
        main_ollama_all(n_repeats=args.repeats or N_REPEATS_OLLAMA_ALL)
    elif args.anthropic_all:
        main_anthropic_all(n_repeats=args.repeats or N_REPEATS_ANTHROPIC_ALL)
    elif args.models:
        model_list = [m.strip() for m in args.models.split(",") if m.strip()]
        main_multi_model(models=model_list, n_repeats=args.repeats or N_REPEATS)
    else:
        main(dry_run=args.dry_run, n_repeats=args.repeats or N_REPEATS)

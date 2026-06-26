"""Folder-structure benchmark — how selectively does an agent retrieve, and what does it cost?
(ADR-0003; hardened per the evaluation-methodology review.)

The extraction benchmark (run_benchmark.py) sends a whole SKILL.md inline and measures OUTPUT
tokens. That cannot study progressive disclosure, which is about an agent choosing WHICH files
to load. This benchmark lays the SAME skill on disk (benchmarks/skills/) in three layouts,
gives a real LLM a `read_file` tool, and asks domain-targeted questions across 6 domains
arranged as 3 near-duplicate distractor pairs (finance/billing, product/platform,
security/compliance) so selective retrieval can genuinely go wrong.

Three arms (same knowledge, different layout):
  Monolith — everything in SKILL.md, no other files. Answer is already in the always-loaded prompt.
  Flat     — lean SKILL.md + one reference.md holding all domains. One read pulls everything.
  Folder   — lean SKILL.md + reference/<domain>.md split by domain. One read pulls one domain.

What this IS and ISN'T: the token ordering (Monolith ≥ Flat ≥ Folder cache-cold) is partly
mechanical — file sizes we chose — so this is a DEMONSTRATION of the cost mechanics, not proof
that disclosure "wins". The empirical content is the agent's RETRIEVAL behaviour and the
cache-aware cost:

  * correctness  — planted-code substring match; a FLOOR GATE only (expect ~100%), kept to
                   discard broken runs. Not the headline.
  * exact-retrieval — read precisely the relevant file and nothing else (Monolith: read nothing).
  * over-read       — read a distractor/irrelevant file.
  * cost            — cache-COLD (worst case, per-call nonce defeats caching) AND cache-WARM
                      (uncached tokens with provider prompt caching). Under caching the Monolith
                      penalty largely closes — so disclosure's token win holds mainly for
                      cache-cold or frequently-changing skills.

Tokens are reported as median [IQR]; rates as % [95% Wilson CI]. The cache-warm pass doubles
API calls; skip it with --cache-cold-only. Requires a tool-capable provider (Anthropic or
OpenAI tool calling); selection mirrors run_benchmark.py:

    export SKILLSPECTOR_PROVIDER=anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
    python benchmarks/structure_bench.py                  # N=10, cold + warm
    python benchmarks/structure_bench.py -n 2 --cache-cold-only   # quick dev run

    export SKILLSPECTOR_PROVIDER=openai
    export OPENAI_API_KEY=sk-...
    python benchmarks/structure_bench.py -n 5
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import statistics
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# Real skill folders on disk, one per arm (ADR-0003): monolith/ flat/ folder/.
_SKILLS_DIR = _REPO_ROOT / "benchmarks" / "skills"

# Reuse the extraction benchmark's provider plumbing (ADR-0003: shared plumbing).
from benchmarks.run_benchmark import (  # noqa: E402
    _RESULTS_DIR,
    DEFAULT_TEMPERATURE,
    _make_client,
    _median_or_zero,
    _model_slug,
    _provider_display,
)

N_REPEATS = 4
MAX_TOOL_TURNS = 6  # safety cap on the read_file loop
_TOOL_PROVIDERS = frozenset({"anthropic", "openai"})

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic multi-domain skill content + planted facts
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Domain:
    """Answer key + question source for one domain. Skill CONTENT lives on disk; only the
    grading metadata (which code answers which question) stays in Python."""

    key: str          # e.g. "finance" — matches reference/<key>.md in the folder arm
    title: str        # e.g. "Finance"
    code_name: str    # what the question asks for, e.g. "finance reconciliation"
    planted_code: str # the unguessable answer planted in the on-disk files


# 6 domains arranged as 3 near-duplicate distractor pairs (finance/billing, product/platform,
# security/compliance) so selective retrieval can genuinely go wrong.  6 domains × 4 repeats
# = 24 runs per arm; Wilson 95% CI for p=1.0 → [0.86, 1.0] — sufficient to conclude
# near-certain exact retrieval.  Order matches benchmarks/skills/ generation.
DOMAINS: list[Domain] = [
    Domain("finance", "Finance", "finance revenue-recognition", "RX-FIN-0372"),
    Domain("billing", "Billing", "billing dunning", "RX-BIL-1180"),
    Domain("product", "Product", "product analytics-event", "PRD-EVTH-9"),
    Domain("platform", "Platform", "platform rate-limit", "PLT-RL-66"),
    Domain("security", "Security", "security service-auth", "SEC-MTLS-3"),
    Domain("compliance", "Compliance", "compliance audit-evidence", "CMP-SOC2-9"),
]


def _question(domain: Domain) -> str:
    return (
        f"What is the internal {domain.code_name} configuration code? "
        "Answer with the exact code and nothing else. Use the read_file tool if you need to."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Arm construction: (skill_md_system_prompt, readable_file_map)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Arm:
    name: str
    skill_md: str            # goes in the system prompt (always loaded)
    files: dict[str, str]    # path -> content, served ON DEMAND via the read_file tool


# (display name, folder name under benchmarks/skills/)
_ARM_DIRS: list[tuple[str, str]] = [
    ("Monolith", "monolith"),
    ("Flat", "flat"),
    ("Folder", "folder"),
]


def _load_arm(name: str, dirname: str) -> Arm:
    """Load a real skill folder from disk into an Arm.

    SKILL.md becomes the always-loaded system prompt. Every other file is registered (by its
    subdir-prefixed relative path, e.g. ``reference/finance.md``) for the read_file tool but
    is NOT placed in the prompt — the agent loads only what it asks for, so the Folder arm
    can read a single domain file and pay for nothing else. Mirrors the ``_cache_of`` rglob
    pattern in tests/test_scorers.py.
    """
    base = _SKILLS_DIR / dirname
    if not (base / "SKILL.md").is_file():
        sys.exit(f"❌  Missing skill folder: {base / 'SKILL.md'} not found.")
    skill_md = (base / "SKILL.md").read_text(encoding="utf-8")
    files = {
        p.relative_to(base).as_posix(): p.read_text(encoding="utf-8")
        for p in base.rglob("*")
        if p.is_file() and p.relative_to(base).as_posix() != "SKILL.md"
    }
    return Arm(name=name, skill_md=skill_md, files=files)


def _build_arms() -> list[Arm]:
    return [_load_arm(name, dirname) for name, dirname in _ARM_DIRS]


def _verify_arms(arms: list[Arm]) -> None:
    """Fail fast if a committed skill folder drifted from the Python answer key — every
    planted code must be retrievable somewhere in each arm (SKILL.md or a readable file)."""
    for arm in arms:
        blob = arm.skill_md + "\n" + "\n".join(arm.files.values())
        missing = [d.planted_code for d in DOMAINS if d.planted_code not in blob]
        if missing:
            sys.exit(
                f"❌  {arm.name} skill folder is missing planted codes {missing}. "
                f"Re-check benchmarks/skills/{arm.name.lower()}/."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Statistics (dispersion, not bare point estimates)
# ─────────────────────────────────────────────────────────────────────────────


def _med_iqr(values: list[float]) -> tuple[float, float, float]:
    """Return (median, q1, q3). Robust summary for skewed token counts."""
    if not values:
        return 0.0, 0.0, 0.0
    med = statistics.median(values)
    if len(values) < 2:
        return med, med, med
    q1, _q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return med, q1, q3


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion k/n, returned as (low, high) in [0, 1]."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _fmt_med_iqr(values: list[float]) -> str:
    if not values:
        return "—"
    med, q1, q3 = _med_iqr(values)
    return f"{med:.0f} [{q1:.0f}–{q3:.0f}]"


def _fmt_pct_ci(k: int, n: int) -> str:
    if n == 0:
        return "—"
    lo, hi = _wilson_ci(k, n)
    return f"{100 * k / n:.0f}% [{100 * lo:.0f}–{100 * hi:.0f}]"


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval behaviour (the primary empirical signal — see ADR-0003 review)
# ─────────────────────────────────────────────────────────────────────────────


def _relevant_file(arm_name: str, domain: Domain) -> str | None:
    """The file an ideal agent would read to answer this domain's question, per arm.
    Monolith has no files (answer is already in the always-loaded SKILL.md)."""
    if arm_name == "Monolith":
        return None
    if arm_name == "Flat":
        return "reference.md"
    return f"reference/{domain.key}.md"


def _retrieval_flags(arm: Arm, domain: Domain, files_read: list[str]) -> tuple[bool, bool]:
    """Return (exact_retrieval, over_read) for one run.

    exact_retrieval — the agent read precisely the relevant file and nothing else
                      (Monolith: read nothing, answering from the system prompt).
    over_read       — the agent read at least one file that was NOT the relevant one
                      (a distractor sibling, or any file at all in the Monolith arm).
    """
    relevant = _relevant_file(arm.name, domain)
    valid = {p for p in files_read if p in arm.files}
    if relevant is None:  # Monolith
        return (len(files_read) == 0, len(valid) > 0)
    exact = valid == {relevant}
    over = any(p != relevant for p in valid)
    return exact, over


# ─────────────────────────────────────────────────────────────────────────────
# Tool-use loop (Anthropic + OpenAI)
# ─────────────────────────────────────────────────────────────────────────────

_TOOL_DESC = "Read a file from the skill bundle by its relative path (e.g. 'reference/finance.md')."
_SYSTEM_SUFFIX = (
    "\n\nYou are answering questions using the skill above. When the answer is in a "
    "supporting file, call read_file with its path. Read only the files you need."
)


def _read_file(files: dict[str, str], path: str) -> str:
    if path in files:
        return files[path]
    avail = ", ".join(sorted(files)) or "(none)"
    return f"ERROR: no file at {path!r}. Available files: {avail}"


def _cold_system(skill_md: str) -> str:
    # Cache-COLD: a unique nonce in the PREFIX gives every call a distinct system prompt, so
    # neither Anthropic (no cache_control) nor OpenAI (prefix auto-cache) can reuse a cache.
    return f"<!-- {uuid.uuid4().hex[:12]} -->\n" + skill_md + _SYSTEM_SUFFIX


@dataclass
class _AnthropicUsage:
    fresh_tokens: int          # input_tokens: not involved in caching at all
    cache_creation_tokens: int # cache_creation_input_tokens: written to cache (paid at 1.25×)
    cache_read_tokens: int     # cache_read_input_tokens: read from cache (paid at 0.1×)


def _run_loop_anthropic(
    client: Any, model: str, arm: Arm, question: str, temperature: float, cache_warm: bool
) -> tuple[str, _AnthropicUsage, list[str]]:
    tools = [{
        "name": "read_file",
        "description": _TOOL_DESC,
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    }]
    if cache_warm:
        # Cache-WARM: stable system prefix marked cacheable.  When the system prompt meets
        # Anthropic's minimum cacheable size (≥2048 tokens for Haiku), subsequent calls with
        # the same prefix pay only for uncached tokens; usage.input_tokens reports fresh tokens
        # only.  If the prompt is below the minimum the cache_control marker is silently ignored
        # and all tokens land in input_tokens — indistinguishable from cold without inspecting
        # cache_creation_input_tokens / cache_read_input_tokens.
        system: Any = [{
            "type": "text", "text": arm.skill_md + _SYSTEM_SUFFIX,
            "cache_control": {"type": "ephemeral"},
        }]
    else:
        system = _cold_system(arm.skill_md)
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    fresh_tokens = 0
    cache_creation_tokens = 0
    cache_read_tokens = 0
    files_read: list[str] = []
    answer = ""
    for _ in range(MAX_TOOL_TURNS):
        resp = client.messages.create(
            model=model, max_tokens=512, system=system, tools=tools,
            messages=messages, temperature=temperature,
        )
        fresh_tokens += resp.usage.input_tokens
        cache_creation_tokens += getattr(resp.usage, "cache_creation_input_tokens", 0) or 0
        cache_read_tokens += getattr(resp.usage, "cache_read_input_tokens", 0) or 0
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use" and block.name == "read_file":
                    path = str(block.input.get("path", ""))
                    files_read.append(path)
                    content = _read_file(arm.files, path)
                    results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": content}
                    )
            messages.append({"role": "user", "content": results})
            continue
        answer = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        break
    return answer, _AnthropicUsage(fresh_tokens, cache_creation_tokens, cache_read_tokens), files_read


def _openai_fresh_tokens(usage: Any) -> int:
    """Prompt tokens that were NOT served from OpenAI's automatic prefix cache."""
    cached = 0
    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", 0) or 0
    return usage.prompt_tokens - cached


def _run_loop_openai(
    client: Any, model: str, arm: Arm, question: str, temperature: float, cache_warm: bool
) -> tuple[str, _AnthropicUsage, list[str]]:
    tools = [{
        "type": "function",
        "function": {
            "name": "read_file",
            "description": _TOOL_DESC,
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    }]
    # OpenAI auto-caches stable prefixes (>=1024 tok); warm keeps the prefix clean, cold makes
    # it unique. Either way we count only freshly-processed prompt tokens.
    system_content = (arm.skill_md + _SYSTEM_SUFFIX) if cache_warm else _cold_system(arm.skill_md)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": question},
    ]
    fresh_tokens = 0
    cache_read_tokens = 0
    files_read: list[str] = []
    answer = ""
    for _ in range(MAX_TOOL_TURNS):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools, temperature=temperature,
        )
        details = getattr(resp.usage, "prompt_tokens_details", None)
        cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
        fresh_tokens += resp.usage.prompt_tokens - cached
        cache_read_tokens += cached
        msg = resp.choices[0].message
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                path = str(args.get("path", ""))
                files_read.append(path)
                content = _read_file(arm.files, path)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": content})
            continue
        answer = msg.content or ""
        break
    return answer, _AnthropicUsage(fresh_tokens, 0, cache_read_tokens), files_read


def _run_loop(
    client: Any, provider: str, model: str, arm: Arm, question: str, temperature: float,
    cache_warm: bool = False,
) -> tuple[str, _AnthropicUsage, list[str]]:
    if provider == "anthropic":
        return _run_loop_anthropic(client, model, arm, question, temperature, cache_warm)
    return _run_loop_openai(client, model, arm, question, temperature, cache_warm)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class StructRun:
    domain: str
    arm: str
    run: int
    input_tokens: int                            # cache-COLD: all freshly processed tokens
    correct: bool                                # floor gate only — expect ~100%
    cache_warm_input_tokens: int | None = None   # cache-WARM: fresh (non-cached) tokens
    cache_creation_tokens: int | None = None     # tokens written to cache (cache-warm only)
    cache_read_tokens: int | None = None         # tokens read from cache (cache-warm only)
    exact_retrieval: bool = False                # read precisely the relevant file (or 0 for Monolith)
    over_read: bool = False                      # read at least one irrelevant/distractor file
    files_read: list[str] = field(default_factory=list)
    answer: str = ""


# Anthropic minimum cacheable prompt size by model family.  Below this threshold the
# cache_control marker is silently ignored and all tokens land in input_tokens, making
# warm ≈ cold (the only difference is the UUID nonce prepended in the cold path).
_ANTHROPIC_CACHE_MIN = 2048  # tokens; applies to Haiku 3/3.5/4.5 and similar


def _warn_cache_eligibility(arms: list[Arm], cache_cold_only: bool) -> None:
    """Print a warning for any arm whose system prompt is likely below the caching minimum."""
    if cache_cold_only:
        return
    ineligible = []
    for arm in arms:
        # Rough estimate: 4 chars per token is a reasonable lower bound for mixed text/code.
        est_tokens = len(arm.skill_md + _SYSTEM_SUFFIX) / 4
        if est_tokens < _ANTHROPIC_CACHE_MIN:
            ineligible.append(f"{arm.name} (~{est_tokens:.0f} tok)")
    if ineligible:
        print(
            f"  ⚠️  Cache-warm pass enabled but the following arm(s) have system prompts\n"
            f"     below the ~{_ANTHROPIC_CACHE_MIN}-token Anthropic caching minimum — "
            f"cache_control will be silently ignored\n"
            f"     and warm ≈ cold (difference is only the cold nonce):\n"
            f"       {', '.join(ineligible)}\n"
            f"     To observe real cache savings, expand those SKILL.md files so the system\n"
            f"     prompt exceeds {_ANTHROPIC_CACHE_MIN} tokens, or run --cache-cold-only.\n"
        )


def _run(
    client: Any, provider: str, model: str, n_repeats: int, temperature: float,
    *, cache_cold_only: bool = False,
) -> list[StructRun]:
    arms = _build_arms()
    _verify_arms(arms)
    if provider == "anthropic":
        _warn_cache_eligibility(arms, cache_cold_only)
    results: list[StructRun] = []
    total = len(DOMAINS) * len(arms) * n_repeats
    modes = 1 if cache_cold_only else 2
    print(
        f"  {len(DOMAINS)} domains · {len(arms)} arms · {n_repeats} repeats × {modes} cache "
        f"mode(s) = {total * modes} calls\n"
    )
    for domain in DOMAINS:
        print(f"  ── {domain.title}")
        question = _question(domain)
        for arm in arms:
            for run_idx in range(1, n_repeats + 1):
                answer, cold_usage, files_read = _run_loop(
                    client, provider, model, arm, question, temperature, cache_warm=False
                )
                warm_tok: int | None = None
                warm_creation: int | None = None
                warm_read: int | None = None
                if not cache_cold_only:
                    _a, warm_usage, _f = _run_loop(
                        client, provider, model, arm, question, temperature, cache_warm=True
                    )
                    warm_tok = warm_usage.fresh_tokens
                    warm_creation = warm_usage.cache_creation_tokens
                    warm_read = warm_usage.cache_read_tokens
                correct = domain.planted_code.lower() in answer.lower()
                exact, over = _retrieval_flags(arm, domain, files_read)
                mark = "✓" if correct else "✗"
                cold_tok = cold_usage.fresh_tokens
                if warm_tok is None:
                    warm_str = ""
                else:
                    # Show cache breakdown: fresh/creation/read so cache behaviour is visible.
                    # When caching is below the provider minimum, creation=0 and read=0 —
                    # warm ≈ cold (minus the nonce).  When it works: creation>0 on first call,
                    # read>0 on subsequent calls, and fresh_tokens is dramatically smaller.
                    cache_detail = f"  +{warm_creation}cr +{warm_read}rd" if (warm_creation or warm_read) else "  [no cache]"
                    warm_str = f" / {warm_tok:>5} warm{cache_detail}"
                reads = ",".join(files_read) or "—"
                print(
                    f"     {arm.name:<9} run {run_idx}/{n_repeats}  {cold_tok:>6} cold{warm_str}  "
                    f"{len(files_read)} read [{reads}]  {mark}"
                )
                results.append(StructRun(
                    domain=domain.key, arm=arm.name, run=run_idx,
                    input_tokens=cold_tok, correct=correct,
                    cache_warm_input_tokens=warm_tok,
                    cache_creation_tokens=warm_creation,
                    cache_read_tokens=warm_read,
                    exact_retrieval=exact, over_read=over,
                    files_read=files_read, answer=answer.strip()[:200],
                ))
        print()
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

_ARM_NAMES = ["Monolith", "Flat", "Folder"]


def _print_summary(results: list[StructRun], n_repeats: int) -> None:
    print("═" * 92)
    print(
        f"  {'Arm':<9} {'cold tok med[IQR]':>20} {'warm med':>9} {'reads':>6} "
        f"{'exact-retr%':>13} {'over-read%':>11} {'correct':>8}"
    )
    print(f"  {'─' * 88}")
    for arm in _ARM_NAMES:
        cell = [r for r in results if r.arm == arm]
        n = len(cell)
        cold = [float(r.input_tokens) for r in cell]
        warm = [float(r.cache_warm_input_tokens) for r in cell if r.cache_warm_input_tokens is not None]
        reads = [float(len(r.files_read)) for r in cell]
        exact_n = sum(1 for r in cell if r.exact_retrieval)
        over_n = sum(1 for r in cell if r.over_read)
        correct_n = sum(1 for r in cell if r.correct)
        warm_str = f"{_median_or_zero([int(x) for x in warm]):.0f}" if warm else "—"
        print(
            f"  {arm:<9} {_fmt_med_iqr(cold):>20} {warm_str:>9} "
            f"{_median_or_zero([int(x) for x in reads]):>6.0f} "
            f"{_fmt_pct_ci(exact_n, n):>13} {_fmt_pct_ci(over_n, n):>11} {correct_n}/{n:<4}"
        )
    print("═" * 92)
    print("  cold = cache-cold (worst case); warm = cache-warm (uncached tokens).")
    print("  Caveat: under prompt caching the Monolith cost gap largely closes (see warm).")


def _markdown(results: list[StructRun], provider: str, model: str, n_repeats: int, temperature: float) -> str:
    date_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    out = [
        f"# Structure Benchmark — {date_str}",
        "",
        f"**Provider:** {_provider_display(provider)}  ",
        f"**Model:** `{model}`  ",
        f"**Repeats:** {n_repeats} per cell  ",
        f"**Temperature:** {temperature}  ",
        "",
        "Same skill, three layouts (real folders under `benchmarks/skills/`). This **demonstrates "
        "the mechanics** of how layout maps to context cost and **measures the agent's retrieval "
        "behaviour** — it does not by itself prove disclosure 'wins' (the token ordering is "
        "partly mechanical). The empirical signals are retrieval precision and the cache-warm cost.",
        "",
        "**Metrics.** Correctness (planted-code substring) is only a floor gate (expect ~100%). "
        "The real signals: **exact-retrieval** = read precisely the relevant file (Monolith = read "
        "nothing, answering from the always-loaded SKILL.md); **over-read** = read a distractor "
        "file. Cost is reported **cache-cold** (worst case, per-call nonce) and **cache-warm** "
        "(uncached tokens with provider prompt caching). Tokens: median [IQR]; rates: % [95% Wilson CI].",
        "",
        "**Caveat.** Under prompt caching a stable Monolith system prompt is largely cache-read, so "
        "the cold-vs-warm gap shows disclosure's token win holds mainly for cache-cold or "
        "frequently-changing skills.",
        "",
        "## Aggregate",
        "",
        "| Arm | Cold tok (med[IQR]) | Warm tok (med) | Reads (med) | Exact-retrieval | Over-read | Correct |",
        "|-----|:-------------------:|:--------------:|:-----------:|:---------------:|:---------:|:-------:|",
    ]
    for arm in _ARM_NAMES:
        cell = [r for r in results if r.arm == arm]
        n = len(cell)
        cold = [float(r.input_tokens) for r in cell]
        warm = [int(r.cache_warm_input_tokens) for r in cell if r.cache_warm_input_tokens is not None]
        reads = [int(len(r.files_read)) for r in cell]
        exact_n = sum(1 for r in cell if r.exact_retrieval)
        over_n = sum(1 for r in cell if r.over_read)
        correct_n = sum(1 for r in cell if r.correct)
        warm_str = f"{_median_or_zero(warm):.0f}" if warm else "—"
        out.append(
            f"| {arm} | {_fmt_med_iqr(cold)} | {warm_str} | {_median_or_zero(reads):.0f} | "
            f"{_fmt_pct_ci(exact_n, n)} | {_fmt_pct_ci(over_n, n)} | {_fmt_pct_ci(correct_n, n)} |"
        )
    out += ["", "## Per-domain median cold input tokens", "",
            "| Domain | " + " | ".join(_ARM_NAMES) + " |",
            "|--------|" + "|".join([":---:"] * len(_ARM_NAMES)) + "|"]
    for domain in DOMAINS:
        cells = []
        for arm in _ARM_NAMES:
            toks = [r.input_tokens for r in results if r.arm == arm and r.domain == domain.key]
            cells.append(f"{_median_or_zero(toks):.0f}" if toks else "—")
        out.append(f"| {domain.title} | " + " | ".join(cells) + " |")
    out += ["", f"*Generated by skillspector-quality structure benchmark on {date_str}.*", ""]
    return "\n".join(out)


def _save(results: list[StructRun], provider: str, model: str, n_repeats: int, temperature: float) -> Path:
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    base = f"{date_str}-structure-{provider.replace('_', '-')}-{_model_slug(model)}"
    md_path = _RESULTS_DIR / f"{base}.md"
    md_path.write_text(_markdown(results, provider, model, n_repeats, temperature), encoding="utf-8")
    json_path = _RESULTS_DIR / f"{base}.json"
    json_path.write_text(json.dumps({
        "provider": provider, "model": model, "n_repeats": n_repeats,
        "temperature": temperature, "date": date_str,
        "runs": [r.__dict__ for r in results],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return md_path


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main(n_repeats: int = N_REPEATS, *, cache_cold_only: bool = False) -> None:
    provider = os.environ.get("SKILLSPECTOR_PROVIDER", "anthropic").lower()
    if provider not in _TOOL_PROVIDERS:
        print(
            f"❌  Structure benchmark needs a tool-capable provider "
            f"({', '.join(sorted(_TOOL_PROVIDERS))}); got SKILLSPECTOR_PROVIDER={provider!r}."
        )
        sys.exit(1)
    model = os.environ.get("SKILLSPECTOR_MODEL") or (
        "claude-haiku-4-5-20251001" if provider == "anthropic" else "gpt-4o-mini"
    )
    temperature = float(os.environ.get("SKILLSPECTOR_TEMPERATURE", DEFAULT_TEMPERATURE))

    client = _make_client(provider)
    if client is None:
        key_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        print(f"❌  {key_var} not set.")
        sys.exit(1)

    sep = "═" * 64
    print(f"\n{sep}")
    print(f"  Structure Benchmark · {_provider_display(provider)} · {model} · N={n_repeats}")
    print("  Monolith vs Flat reference.md vs Folder (reference/<domain>.md)")
    if cache_cold_only:
        print("  cache-cold only (skipping the cache-warm pass)")
    print(sep + "\n")

    results = _run(
        client, provider, model, n_repeats, temperature, cache_cold_only=cache_cold_only
    )
    _print_summary(results, n_repeats)
    saved = _save(results, provider, model, n_repeats, temperature)
    print(f"\n  Results saved to: {saved.relative_to(_REPO_ROOT)}\n")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python benchmarks/structure_bench.py",
        description="Folder-structure benchmark: Monolith vs Flat vs Folder (ADR-0003).",
    )
    p.add_argument("-n", "--repeats", type=int, default=N_REPEATS, metavar="N",
                   help=f"repeats per cell (default {N_REPEATS})")
    p.add_argument("--cache-cold-only", action="store_true",
                   help="skip the cache-warm pass (halves API calls; reports cold cost only)")
    p.add_argument("--list", action="store_true",
                   help="load the skill folders from disk, show layout + planted facts, exit "
                        "(no LLM calls); also runs the integrity check")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.list:
        for d in DOMAINS:
            print(f"[{d.key}] asks for {d.code_name} code → planted {d.planted_code!r}")
        print(f"\nArms (loaded from {_SKILLS_DIR.relative_to(_REPO_ROOT)}/):")
        arms = _build_arms()
        for arm in arms:
            files = ", ".join(sorted(arm.files)) or "(none — all in SKILL.md)"
            print(f"  {arm.name:<9} SKILL.md {len(arm.skill_md.splitlines())} lines; files: {files}")
        _verify_arms(arms)
        print("\nIntegrity check passed: every planted code is present in each arm.")
    else:
        main(n_repeats=args.repeats, cache_cold_only=args.cache_cold_only)

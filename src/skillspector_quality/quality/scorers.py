"""Deterministic, math-grounded quality scorers.

Nine dimensions evaluate the whole skill bundle (SKILL.md + markdown docs + scripts) using
information theory, length-invariant lexical statistics, a readability ensemble, TF-IDF
vector-space topic modeling, link-graph structure, and code-maintainability metrics.

Design principles:

* **Length-neutral.** Every content metric is a ratio or a length-invariant statistic, so
  more *good* content is never penalized; redundancy and low information density are.
* **N/A => weight renormalization.** A dimension that does not apply (e.g. no scripts)
  returns ``[]`` and is omitted by the engine, leaving both numerator and denominator — it
  neither rewards nor punishes.
* **Pure & deterministic.** No LLM, no randomness. ``radon`` is used for code metrics; the
  rest is stdlib (``zlib``, ``math``, ``ast``) plus hand-rolled TF-IDF / MTLD / readability.

Each dimension takes a :class:`SkillDoc` and returns ``list[(earned, max, label)]`` where
``max`` is the dimension weight and ``earned = round(weight * s)`` with ``s in [0, 1]``.
"""

from __future__ import annotations

import ast
import functools
import math
import re
import zlib
from collections import Counter, deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

from skillspector_quality.config import ScoringConfig

_EMPTY_CONFIG = ScoringConfig()

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency declared in pyproject
    raise ImportError("pyyaml is required (pip install pyyaml)") from exc

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Valid values for enum-typed behavioral-config fields (spec-defined).
_VALID_EFFORT: frozenset[str] = frozenset({"low", "medium", "high", "xhigh", "max"})
_VALID_SHELL: frozenset[str] = frozenset({"bash", "powershell"})
_VALID_CONTEXT: frozenset[str] = frozenset({"fork"})

# All 13 behavioral/execution/lifecycle frontmatter fields from the spec.
_BEHAVIORAL_FIELDS: frozenset[str] = frozenset(
    {
        "paths",
        "user-invocable",
        "arguments",
        "argument-hint",
        "allowed-tools",
        "disallowed-tools",
        "disable-model-invocation",
        "model",
        "effort",
        "context",
        "agent",
        "shell",
        "hooks",
    }
)

STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "into",
    "when",
    "used",
    "uses",
    "for",
    "and",
    "the",
    "are",
    "your",
    "have",
    "will",
    "about",
    "also",
    "been",
    "each",
    "they",
    "them",
    "then",
    "their",
    "than",
    "more",
    "some",
    "such",
    "just",
    "very",
    "well",
    "both",
}

_TRIGGER_VERBS_RE = re.compile(r"\b(use|invoke|trigger|call|apply|run|activate)\b", re.IGNORECASE)
_NEGATION_RE = re.compile(
    r"\b(do[\s-]not|don't|never|skip|avoid|not for|except when|only when)\b", re.IGNORECASE
)
_CONDITIONAL_RE = re.compile(r"\b(when|if|while|after|before)\b", re.IGNORECASE)

FENCE_RE = re.compile(r"^\s*```([A-Za-z0-9_+-]*)\s*$")
LINK_RE = re.compile(r"\[.*?\]\(([^)]+)\)")
SCRIPT_PATH_RE = re.compile(r"(?<![\w/])((?:scripts|assets|references|reference)/[\w./-]+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
STRUCTURED_LINE_RE = re.compile(r"^\s*([-*+] |\d+[.)]\s)")

# Heading words that name a section as a demonstration. Broader than the original
# "Example"-only match, which found examples in 10% of real skills while 96% had them.
_EXAMPLE_HEADING_RE = re.compile(
    r"(?i)\b(examples?|usage|sample|samples|walkthrough|walk-through|scenarios?|"
    r"demo|demos|recipes?|in practice|quick ?start|getting started)\b"
)

# Vague filler that occupies tokens without telling an agent anything it can act on.
# AGENTbench found exactly this class of prose is what makes context files cost without
# helping. Scored in Instruction Clarity (ADR-0009).
_HEDGE_RE = re.compile(
    r"(?i)\b(appropriate(ly)?|as needed|as necessary|etc\.?|and so on|if applicable|"
    r"where relevant|various|several|some|things?|stuff|generally|typically|usually|"
    r"may want to|consider|might)\b"
)

MARKDOWN_EXTS = {".md", ".markdown"}
SCRIPT_EXTS = {".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".rb", ".go", ".rs", ".pl"}
SHELL_EXTS = {".sh", ".bash", ".zsh"}

# --------------------------------------------------------------------------- #
# Band edges — anchored to a measured corpus, not chosen by hand (ADR-0007).
#
# Two anchoring rules, because the signals differ in kind:
#
# * **Quality-shaped** signals (compression, MTLD, TF-IDF cosine) are ratios or
#   length-invariant statistics — an author cannot raise them by writing more. These are
#   anchored zero-at-p10 / full-at-p90 so the dimension uses its whole range.
# * **Length-shaped** signals (example depth) are raw word counts. Anchoring those at p90
#   would reward padding, which costs runtime tokens on every invocation, so they are
#   anchored at the corpus MEDIAN — enough to be substantial, no reward for more.
#
# Superseded ADR-0004's hand-picked 0.42 / 80.0, which measurement placed at corpus p25 and
# ~p40 respectively: 75% and ~55% of real skills scored full marks, so both dimensions
# reported a near-constant.
# --------------------------------------------------------------------------- #

# Information Density: zlib(level=1) compression ratio. Corpus p10=0.387, p90=0.501.
DENSITY_ZERO_RATIO = 0.38
DENSITY_FULL_RATIO = 0.50
# Lexical Diversity: MTLD. Corpus p10=53.4, p90=136.4.
LEXICAL_ZERO_MTLD = 53.0
LEXICAL_FULL_MTLD = 136.0
# Minimum prose tokens before MTLD is scored at all. Below ~200 tokens MTLD is unstable AND
# biased downward (corpus: mean 76.3 at 150-300 tokens vs 96.1 at 300-800), so scoring it
# would penalize a document for being short — a length-neutrality violation. Real skills are
# far above this: corpus p10 is 431 prose tokens and only 2 of 207 fall under 200.
LEXICAL_MIN_TOKENS = 200
# Topic Coverage: TF-IDF cosine. desc p10=0.226/p90=0.574; cohesion p10=0.165/p90=0.509.
COVERAGE_ZERO_COSINE = 0.23
COVERAGE_FULL_COSINE = 0.57
COHESION_ZERO_COSINE = 0.17
COHESION_FULL_COSINE = 0.51
# Example Quality depth: median demonstration length in words. Corpus p50=84 (p90=191,
# deliberately NOT used — see the length-shaped rule above).
EXAMPLE_DEPTH_FULL = 84.0
# Prose words that must accompany a fenced block for it to count as a demonstration rather
# than a bare code dump. Low on purpose: "Invoke the command like so:" is how skills really
# introduce an example, and the richness gradient — not this gate — grades how good it is.
DEMO_MIN_PROSE_WORDS = 5
# Instruction Clarity (ADR-0009). Both signals are "lower is better" and bottom out at zero,
# so they are anchored full-marks-at-0 / zero-at-p90 rather than the usual p10/p90 ramp.
HEDGE_ZERO_DENSITY = 0.50  # corpus p90: hedge words per 100 prose words
UNTAGGED_FENCE_ZERO = 0.89  # corpus p90: share of code fences with no language tag
# Readability target band (median grade level). Corpus p10=9.1, p75=13.3, p90=16.0.
# Real skills genuinely cluster inside this band, so Readability behaves as a violation
# detector rather than a discriminator; the band is not narrowed past what the data supports.
READABILITY_BAND = (9.0, 14.0)

# Strict-mode variants: set above the corpus p90 so "strict" is a genuinely harder bar.
DENSITY_FULL_RATIO_STRICT = 0.55
LEXICAL_FULL_MTLD_STRICT = 160.0

# Text-file suffixes the loader puts in file_cache (mirrors skillspector.nodes.resolve_input).
# A relative link to one of these that is absent from the cache is a genuine BROKEN link;
# links to other suffixes (.pptx/.png/.pdf …) are binary assets the loader can't see, so we
# never flag them. See docs/adr/0005-link-hygiene.md.
TEXT_LINK_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".txt", ".json", ".toml", ".markdown"}

# Link-hygiene sub-check ids (for config disable/strict) and their default severities.
LINK_SUBCHECKS = ("link.broken", "link.platform", "link.redundant", "link.case-mismatch")
_LINK_SEVERITY = {"broken": 0.34, "platform": 0.34, "redundant": 0.10}
_LINK_SEVERITY_STRICT = {"broken": 0.50, "platform": 0.50, "redundant": 0.20}
# Platform-coupled (machine/OS-specific) link targets: POSIX absolute, home-relative,
# Windows drive, backslash separators, or file:// URLs.
_PLATFORM_LINK_RE = re.compile(r"^(/(?!/)|~/|[A-Za-z]:[\\/]|file://)|\\")


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _trigger_clauses(text: str) -> int:
    """Count distinct trigger situations named in a trigger sentence.

    Approximates "how many separate cases does this cover" by counting conditional markers
    and list separators between them, capped so a run-on sentence cannot farm the signal.
    """
    markers = len(_CONDITIONAL_RE.findall(text))
    separators = len(re.findall(r"(?i),\s|\bor\b|;", text))
    return min(4, max(markers, min(separators, 3) + 1 if markers else 0))


def _when_specificity(when: str) -> float:
    """Score 0..1 for how actionable a trigger description is.

    Based on the AGENTbench finding (Gloaguen et al., 2026) that minimal, specific trigger +
    exclusion conditions are the highest-ROI content in agent context files, while vague
    prose duplicating the description yields cost with no benefit.

    **Length is a floor, never a bonus** (ADR-0007). The original version awarded +0.30 for
    ``len >= 15`` and +0.10 for ``len > 80``; measured over 207 real skills those fired for
    100% and 99% of descriptions respectively, so they contributed a constant while creating
    an incentive to pad. Descriptions are loaded for every skill in every session — they are
    the most token-sensitive text in the system, and the last place to reward length.
    """
    text = when.strip()
    if not text:
        return 0.0  # absent
    if len(text) < 15:
        return 0.15  # present but too thin for an agent to act on
    s = 0.0
    if _TRIGGER_VERBS_RE.search(text):
        s += 0.30  # concrete trigger verb ("Use when…", "Invoke for…")
    if _CONDITIONAL_RE.search(text):
        s += 0.20  # situational framing ("when X", "if Y")
    if _NEGATION_RE.search(text):
        s += 0.30  # exclusion condition — highest-ROI and rarest signal (2% of the corpus)
    s += 0.20 * clamp01((_trigger_clauses(text) - 1) / 3)  # covers several distinct cases
    return clamp01(s)


def _ext(path: str) -> str:
    idx = path.rfind(".")
    return path[idx:].lower() if idx >= 0 else ""


# --------------------------------------------------------------------------- #
# Parsed-skill container
# --------------------------------------------------------------------------- #


@dataclass
class SkillDoc:
    """Everything the dimensions need, parsed once from the file_cache."""

    file_cache: dict[str, str]
    data: dict[str, Any]  # SKILL.md frontmatter
    body: str  # SKILL.md body (after frontmatter)
    body_lines: list[str]
    body_lower: str
    skill_md_key: str  # actual key used for SKILL.md
    markdown_docs: dict[str, str] = field(default_factory=dict)  # non-SKILL.md markdown
    scripts: dict[str, str] = field(default_factory=dict)  # code files

    @classmethod
    def from_file_cache(cls, file_cache: dict[str, str]) -> SkillDoc:
        skill_key = (
            "SKILL.md"
            if "SKILL.md" in file_cache
            else ("skill.md" if "skill.md" in file_cache else "SKILL.md")
        )
        text = file_cache.get(skill_key, "")
        data = _parse_frontmatter(text)
        body = _body(text)

        markdown_docs: dict[str, str] = {}
        scripts: dict[str, str] = {}
        for path, content in file_cache.items():
            if path in ("SKILL.md", "skill.md"):
                continue
            ext = _ext(path)
            if ext in MARKDOWN_EXTS:
                markdown_docs[path] = content
            elif ext in SCRIPT_EXTS:
                scripts[path] = content

        return cls(
            file_cache=file_cache,
            data=data if isinstance(data, dict) else {},
            body=body,
            body_lines=body.splitlines(),
            body_lower=body.lower(),
            skill_md_key=skill_key,
            markdown_docs=markdown_docs,
            scripts=scripts,
        )

    @functools.cached_property
    def all_prose(self) -> str:
        """Concatenated prose (code fences stripped) of SKILL.md body + markdown docs."""
        parts = [_strip_fences_text(self.body)]
        for content in self.markdown_docs.values():
            parts.append(_strip_fences_text(content))
        return "\n".join(parts)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end].strip())
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _body(text: str) -> str:
    text = text.replace("\r\n", "\n")
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        # Unclosed frontmatter: skip the opening --- line to avoid YAML in prose metrics.
        nl = text.find("\n")
        return text[nl + 1 :].lstrip("\n") if nl != -1 else ""
    return text[end + 4 :].lstrip("\n")


# --------------------------------------------------------------------------- #
# Generic text helpers
# --------------------------------------------------------------------------- #


def _strip_code_fences(lines: list[str]) -> list[str]:
    """Return lines outside fenced code blocks."""
    out: list[str] = []
    in_fence = False
    for ln in lines:
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(ln)
    return out


def _strip_fences_text(text: str) -> str:
    return "\n".join(_strip_code_fences(text.splitlines()))


def _word_tokens(text: str) -> list[str]:
    """All lowercase word tokens (apostrophes kept)."""
    return re.findall(r"[a-z][a-z']*", text.lower())


def _terms(text: str) -> list[str]:
    """Content terms for topic modeling: lowercase, >=3 chars, stopwords removed."""
    return [w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOPWORDS]


def _count_syllables(word: str) -> int:
    """Cheap syllable estimate: count vowel groups, min 1."""
    groups = re.findall(r"[aeiouy]+", word.lower())
    n = len(groups)
    if word.lower().endswith("e") and n > 1:
        n -= 1
    return max(1, n)


# --------------------------------------------------------------------------- #
# Information-theory helpers
# --------------------------------------------------------------------------- #


def _compression_ratio(text: str) -> float:
    """len(compressed) / len(raw) in bytes. Higher => denser / less redundant."""
    raw = text.encode("utf-8", errors="replace")
    if not raw:
        return 0.0
    comp = zlib.compress(raw, 1)
    return len(comp) / len(raw)


def _ngram_dup(tokens: list[str], n: int = 5) -> float:
    """Fraction of n-gram shingles that are repeats (0 = no duplication)."""
    if len(tokens) < n:
        return 0.0
    shingles = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    total = len(shingles)
    unique = len(set(shingles))
    return 1.0 - unique / total


# --------------------------------------------------------------------------- #
# Lexical-diversity helpers (length-invariant)
# --------------------------------------------------------------------------- #


def _mtld_one_pass(tokens: list[str], threshold: float) -> float:
    factors = 0.0
    types: set[str] = set()
    count = 0
    for t in tokens:
        count += 1
        types.add(t)
        if len(types) / count <= threshold:
            factors += 1
            types = set()
            count = 0
    if count > 0:
        ttr = len(types) / count
        factors += (1 - ttr) / (1 - threshold)
    if factors == 0:
        return float(len(tokens))
    return len(tokens) / factors


def _mtld(tokens: list[str], threshold: float = 0.72) -> float:
    """Measure of Textual Lexical Diversity (bidirectional mean). Length-invariant."""
    if not tokens:
        return 0.0
    fwd = _mtld_one_pass(tokens, threshold)
    bwd = _mtld_one_pass(list(reversed(tokens)), threshold)
    return (fwd + bwd) / 2


def _hdd(tokens: list[str], sample_size: int = 42) -> float | None:
    """HD-D: mean per-type probability of appearing in a random sample. None if too short."""
    n = len(tokens)
    if n < sample_size:
        return None
    freq = Counter(tokens)
    denom = math.comb(n, sample_size)
    hdd = 0.0
    for cnt in freq.values():
        # P(type appears at least once in a sample of sample_size)
        p_absent = math.comb(n - cnt, sample_size) / denom if n - cnt >= sample_size else 0.0
        hdd += (1 - p_absent) * (1 / sample_size)
    return hdd


# --------------------------------------------------------------------------- #
# Readability helpers (ensemble)
# --------------------------------------------------------------------------- #


def _prose_for_readability(doc: SkillDoc) -> str:
    lines = [
        ln
        for ln in _strip_code_fences(doc.body_lines)
        if ln.strip()
        and not ln.lstrip().startswith(("#", "|", ">"))
        and not STRUCTURED_LINE_RE.match(ln)
    ]
    for content in doc.markdown_docs.values():
        for ln in _strip_code_fences(content.splitlines()):
            s = ln.strip()
            if (
                s
                and not ln.lstrip().startswith(("#", "|", ">"))
                and not STRUCTURED_LINE_RE.match(ln)
            ):
                lines.append(ln)
    return " ".join(lines)


def _readability_grades(text: str) -> tuple[list[float], int]:
    """Return (list of 5 grade levels, word count). Empty list if too little prose."""
    words = re.findall(r"[A-Za-z]+", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    w = len(words)
    s = max(1, len(sentences))
    if w < 30:
        return [], w

    syll = [_count_syllables(x) for x in words]
    total_syll = sum(syll)
    complex_words = sum(1 for c in syll if c >= 3)
    letters = sum(len(x) for x in words)

    wps = w / s  # words per sentence
    spw = total_syll / w  # syllables per word

    fk = 0.39 * wps + 11.8 * spw - 15.59
    fog = 0.4 * (wps + 100 * complex_words / w)
    smog = 1.0430 * math.sqrt(complex_words * (30 / s)) + 3.1291
    ari = 4.71 * (letters / w) + 0.5 * wps - 21.43
    cl = 0.0588 * (letters / w * 100) - 0.296 * (s / w * 100) - 15.8

    return [fk, fog, smog, ari, cl], w


def _median(xs: list[float]) -> float:
    ys = sorted(xs)
    n = len(ys)
    mid = n // 2
    return ys[mid] if n % 2 else (ys[mid - 1] + ys[mid]) / 2


# --------------------------------------------------------------------------- #
# TF-IDF helpers (vector space)
# --------------------------------------------------------------------------- #


def _tf(terms: list[str]) -> dict[str, float]:
    if not terms:
        return {}
    c = Counter(terms)
    total = len(terms)
    return {t: n / total for t, n in c.items()}


def _build_idf(corpus_terms: list[list[str]]) -> dict[str, float]:
    n = len(corpus_terms)
    df: Counter[str] = Counter()
    for terms in corpus_terms:
        for t in set(terms):
            df[t] += 1
    return {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}


def _tfidf_vec(terms: list[str], idf: dict[str, float]) -> dict[str, float]:
    vec = {t: tf * idf.get(t, 0.0) for t, tf in _tf(terms).items()}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return {}
    return {t: v / norm for t, v in vec.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    small, big = (a, b) if len(a) < len(b) else (b, a)
    return sum(v * big.get(t, 0.0) for t, v in small.items())


# --------------------------------------------------------------------------- #
# Structure helpers (graph + heading tree)
# --------------------------------------------------------------------------- #


def _heading_levels(text: str) -> list[int]:
    levels: list[int] = []
    for ln in _strip_code_fences(text.splitlines()):
        m = HEADING_RE.match(ln)
        if m:
            levels.append(len(m.group(1)))
    return levels


def _relative_targets(text: str) -> list[str]:
    out: list[str] = []
    for t in LINK_RE.findall(text):
        out.append(t)
    out.extend(SCRIPT_PATH_RE.findall(text))
    cleaned: list[str] = []
    for t in out:
        t = t.strip()
        if not t or re.match(r"^(https?://|mailto:|#|//)", t):
            continue
        t = t.split("#", 1)[0].split("?", 1)[0]
        if t.startswith("./"):
            t = t[2:]
        if t:
            cleaned.append(t)
    return cleaned


def _resolve_target(target: str, keys: set[str]) -> str | None:
    if target in keys:
        return target
    if target.endswith("/"):
        for k in keys:
            if k.startswith(target):
                return k
        return None
    for k in keys:
        if k == target or k.endswith("/" + target):
            return k
    return None


def _link_graph(doc: SkillDoc) -> tuple[dict[str, set[str]], set[str]]:
    """Return (adjacency, nodes). Edges = resolved relative refs from each markdown file."""
    keys = set(doc.file_cache.keys())
    adj: dict[str, set[str]] = {k: set() for k in keys}
    md_files = {doc.skill_md_key: doc.body, **doc.markdown_docs}
    for src, content in md_files.items():
        for tgt in _relative_targets(content):
            resolved = _resolve_target(tgt, keys)
            if resolved and resolved != src:
                adj[src].add(resolved)
    return adj, keys


def _bfs_depths(adj: dict[str, set[str]], root: str) -> dict[str, int]:
    """Shortest-path depth of each reachable node from ``root`` (root = 0).

    Unreachable nodes are omitted. Used by Progressive Disclosure to tell a doc linked
    directly from SKILL.md (depth 1) from one nested behind another doc (depth >= 2).
    """
    depths: dict[str, int] = {root: 0}
    queue: deque[str] = deque([root])
    while queue:
        node = queue.popleft()
        for nxt in adj.get(node, ()):
            if nxt not in depths:
                depths[nxt] = depths[node] + 1
                queue.append(nxt)
    return depths


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into ``(heading_text, section_body)`` at ATX headings.

    Fence-aware: a ``#`` inside a code block is content, not a heading. The first tuple is
    the pre-heading preamble with an empty heading.
    """
    sections: list[tuple[str, str]] = []
    heading = ""
    buf: list[str] = []
    in_fence = False
    for ln in text.splitlines():
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            buf.append(ln)
            continue
        if not in_fence and HEADING_RE.match(ln):
            sections.append((heading, "\n".join(buf)))
            heading = ln.lstrip("#").strip()
            buf = []
            continue
        buf.append(ln)
    sections.append((heading, "\n".join(buf)))
    return sections


def _fenced_blocks(text: str) -> int:
    """Number of complete fenced code blocks (two delimiter lines each)."""
    return sum(1 for ln in text.splitlines() if FENCE_RE.match(ln)) // 2


def _prose_words(text: str) -> int:
    """Word count of non-heading prose outside code fences."""
    lines = [
        ln
        for ln in _strip_code_fences(text.splitlines())
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    return len(_word_tokens(" ".join(lines)))


def _demonstrations(doc: SkillDoc) -> list[str]:
    """Sections of the bundle that concretely show the skill in use.

    Two detectors, because the ecosystem writes examples both ways: a heading that *names*
    the section (Example / Usage / Walkthrough / …), or an unlabeled section carrying a
    fenced block with explanatory prose around it. Measured over 207 real skills, the old
    ``^## Example`` regex matched 10% while 96% demonstrated usage somehow — so heading-word
    matching alone was reporting a near-constant zero. See ADR-0007.

    A labelled section with no concrete content still counts: it is a demonstration that
    scores badly on richness, not the absence of one.
    """
    out: list[str] = []
    for source in (doc.body, *doc.markdown_docs.values()):
        for heading, section in _split_sections(source):
            if not section.strip():
                continue
            if _EXAMPLE_HEADING_RE.search(heading):
                out.append(section)
            elif _fenced_blocks(section) >= 1 and _prose_words(section) >= DEMO_MIN_PROSE_WORDS:
                out.append(section)
    return out


def _fence_tags(text: str) -> list[str]:
    """Language tag of each opening code fence ("" when untagged)."""
    marks = [m for m in (FENCE_RE.match(ln) for ln in text.splitlines()) if m]
    return [m.group(1) for m in marks[::2]]  # every other fence is an opener


def _hedge_density(prose: str) -> float:
    """Hedge words per 100 prose words. Length-invariant, so padding cannot dilute it."""
    tokens = _word_tokens(prose)
    if not tokens:
        return 0.0
    return 100.0 * len(_HEDGE_RE.findall(prose)) / len(tokens)


@dataclass
class DuplicateSpan:
    """One pair of files sharing prose, with the size of the overlap."""

    source: str
    target: str
    shared_tokens: int


# Above this many markdown files, compare only SKILL.md against each doc rather than every
# pair — a bundle with 135 docs would otherwise mean over 9,000 comparisons.
_DUP_ALL_PAIRS_LIMIT = 12


def _covered_token_count(tokens: list[str], other: set[tuple[str, ...]], n: int) -> int:
    """How many of ``tokens`` sit inside a window that also appears in ``other``.

    Counts covered *positions*, not distinct shingles. Distinct-shingle counting collapses on
    repetitive prose — 300 duplicated words built from a handful of repeating phrases yield
    only a handful of unique windows, understating the duplication by an order of magnitude.
    """
    covered: set[int] = set()
    for i in range(len(tokens) - n + 1):
        if tuple(tokens[i : i + n]) in other:
            covered.update(range(i, i + n))
    return len(covered)


def _duplicate_spans(doc: SkillDoc, n: int = 6) -> list[DuplicateSpan]:
    """Find prose shared between SKILL.md and each supporting doc, and between docs.

    Diagnostic only — this is deliberately NOT a scored quality signal. Measured over 207
    skills it correlates with the existing ``_ngram_dup`` at **r = +0.951**, so scoring it
    would count the same evidence twice (ADR-0009). What it adds is *attribution*:
    ``_ngram_dup`` returns one opaque fraction, while this names the files involved, and the
    duplicated tokens are real spend on the cost axis — removing one copy recovers them.
    """
    files = {doc.skill_md_key: doc.body, **doc.markdown_docs}
    tokens: dict[str, list[str]] = {}
    shingles: dict[str, set[tuple[str, ...]]] = {}
    for path, content in files.items():
        toks = _word_tokens(_strip_fences_text(content))
        if len(toks) < n:
            continue
        tokens[path] = toks
        shingles[path] = {tuple(toks[i : i + n]) for i in range(len(toks) - n + 1)}

    names = sorted(shingles)
    if len(names) > _DUP_ALL_PAIRS_LIMIT:
        root = doc.skill_md_key
        pairs = [(root, b) for b in names if b != root] if root in shingles else []
    else:
        pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1 :]]

    out: list[DuplicateSpan] = []
    for a, b in pairs:
        if not (shingles[a] & shingles[b]):
            continue  # cheap reject before the positional pass
        # Both directions, because the overlap may cover most of a short file and little of a
        # long one; the larger figure is what an author would actually recover by deduping.
        shared = max(
            _covered_token_count(tokens[a], shingles[b], n),
            _covered_token_count(tokens[b], shingles[a], n),
        )
        if shared:
            out.append(DuplicateSpan(a, b, shared))
    out.sort(key=lambda s: -s.shared_tokens)
    return out


def _demo_richness(section: str) -> float:
    """0/0.5/1 for how completely one demonstration shows the skill working.

    Full credit needs a contrast an agent can learn the shape from — two code blocks, or
    explicit input/output or before/after framing. A lone block with prose around it is
    partial. A heading promising an example that shows nothing concrete earns zero.
    """
    low = section.lower()
    blocks = _fenced_blocks(section)
    if blocks >= 2 or ("input" in low and "output" in low) or ("before" in low and "after" in low):
        return 1.0
    if blocks >= 1 and _prose_words(section) >= DEMO_MIN_PROSE_WORDS:
        return 0.5
    return 0.0


def _has_toc(content: str) -> bool:
    """True if a markdown doc opens with a 'Contents'/'Table of Contents' heading."""
    head = "\n".join(content.splitlines()[:40])
    return bool(re.search(r"(?im)^#{1,4}\s+(table of\s+)?contents\b", head))


def _reachable_from(adj: dict[str, set[str]], root: str) -> set[str]:
    seen: set[str] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adj.get(node, ()))
    return seen


def _is_acyclic(adj: dict[str, set[str]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2  # noqa: N806
    color: dict[str, int] = dict.fromkeys(adj, WHITE)

    for start in adj:
        if color[start] != WHITE:
            continue
        stack: list[tuple[str, Iterator[str]]] = [(start, iter(adj.get(start, ())))]
        color[start] = GRAY
        while stack:
            node, neighbors = stack[-1]
            try:
                m = next(neighbors)
                c = color.get(m, WHITE)
                if c == GRAY:
                    return False
                if c == WHITE:
                    color[m] = GRAY
                    stack.append((m, iter(adj.get(m, ()))))
            except StopIteration:
                color[node] = BLACK
                stack.pop()
    return True


# --------------------------------------------------------------------------- #
# Link-hygiene helpers (broken / platform-coupled / case-mismatch / redundant)
# --------------------------------------------------------------------------- #


def _resolve_target_ci(target: str, keys: set[str]) -> str | None:
    """Case-insensitive variant of ``_resolve_target`` — detects case-only mismatches."""
    t = target.lower()
    for k in keys:
        kl = k.lower()
        if kl == t or kl.endswith("/" + t):
            return k
    return None


def _iter_link_refs(doc: SkillDoc) -> Iterator[tuple[str, bool]]:
    """Yield ``(target, is_markdown)`` for each link reference in SKILL.md + markdown docs.

    Markdown links (``LINK_RE``) carry ``is_markdown=True``; bare ``reference/...`` paths
    (``SCRIPT_PATH_RE``) carry ``False``. Code fences are stripped so fenced examples are
    ignored. Targets are yielded raw; the caller filters and normalizes.
    """
    md_files = {doc.skill_md_key: doc.body, **doc.markdown_docs}
    for content in md_files.values():
        clean = "\n".join(_strip_code_fences(content.splitlines()))
        for t in LINK_RE.findall(clean):
            yield t, True
        for t in SCRIPT_PATH_RE.findall(clean):
            yield t, False


@dataclass
class LinkHygiene:
    """Distinct link-hygiene offenders found in a skill."""

    broken: list[str] = field(default_factory=list)  # text-suffix targets that don't exist
    case_mismatch: list[tuple[str, str]] = field(default_factory=list)  # (target, real key)
    platform: list[str] = field(default_factory=list)  # machine/OS-specific paths
    redundant: list[tuple[str, int]] = field(default_factory=list)  # (target, link count)

    def has_any(self) -> bool:
        return bool(self.broken or self.case_mismatch or self.platform or self.redundant)


def _link_hygiene(doc: SkillDoc) -> LinkHygiene:
    """Classify every link reference into broken / case-mismatch / platform / redundant.

    Classification order per target (first match wins, so no double-counting): skip
    external/anchor refs -> platform-coupled -> resolves (clean) -> case-only mismatch ->
    broken (text suffix only; binary assets the loader can't see are never flagged).
    Redundancy is counted on resolvable **markdown-link** targets only.
    """
    keys = set(doc.file_cache.keys())
    h = LinkHygiene()
    seen_broken: set[str] = set()
    seen_cm: set[str] = set()
    seen_plat: set[str] = set()
    md_targets: list[str] = []
    for raw, is_md in _iter_link_refs(doc):
        t = raw.strip()
        if not t or re.match(r"^(https?://|mailto:|#|//)", t):
            continue
        if _PLATFORM_LINK_RE.search(t):
            if t not in seen_plat:
                seen_plat.add(t)
                h.platform.append(t)
            continue
        core = t.split("#", 1)[0].split("?", 1)[0]
        if core.startswith("./"):
            core = core[2:]
        if not core:
            continue
        if _resolve_target(core, keys) is not None:
            if is_md:
                md_targets.append(core)
            continue
        ci = _resolve_target_ci(core, keys)
        if ci is not None:
            if core not in seen_cm:
                seen_cm.add(core)
                h.case_mismatch.append((core, ci))
            continue
        if _ext(core) in TEXT_LINK_SUFFIXES and core not in seen_broken:
            seen_broken.add(core)
            h.broken.append(core)
        # else: extension-less or binary target -> unverifiable, not flagged
    for tgt, c in Counter(md_targets).items():
        if c > 1:
            h.redundant.append((tgt, c))
    return h


def _link_sev(bucket: str, sub_id: str, config: ScoringConfig) -> float:
    """Severity for a link bucket, raised when its sub-check or the dimension is strict."""
    strict = config.is_strict("Structural Coherence", sub_id)
    return (_LINK_SEVERITY_STRICT if strict else _LINK_SEVERITY)[bucket]


def _link_valid_score(h: LinkHygiene, config: ScoringConfig) -> float:
    """Map offenders to a 0-1 sub-signal: 1 - (Σ severity·count), honoring disable/strict."""
    penalty = 0.0
    if not config.is_disabled("link.broken"):
        penalty += _link_sev("broken", "link.broken", config) * len(h.broken)
    if not config.is_disabled("link.case-mismatch"):
        penalty += _link_sev("broken", "link.case-mismatch", config) * len(h.case_mismatch)
    if not config.is_disabled("link.platform"):
        penalty += _link_sev("platform", "link.platform", config) * len(h.platform)
    if not config.is_disabled("link.redundant"):
        penalty += _link_sev("redundant", "link.redundant", config) * sum(
            c - 1 for _, c in h.redundant
        )
    return clamp01(1.0 - penalty)


def _link_hygiene_labels(h: LinkHygiene, config: ScoringConfig) -> list[str]:
    """Human-readable offender descriptions for enabled sub-checks (for the dimension label)."""
    parts: list[str] = []
    if h.broken and not config.is_disabled("link.broken"):
        parts.append(f"{len(h.broken)} broken link(s) ({', '.join(h.broken)}) — fix or remove")
    if h.case_mismatch and not config.is_disabled("link.case-mismatch"):
        ex = ", ".join(f"{t} vs {k}" for t, k in h.case_mismatch)
        parts.append(f"{len(h.case_mismatch)} case-mismatched link(s) ({ex}) — breaks on Linux")
    if h.platform and not config.is_disabled("link.platform"):
        parts.append(
            f"{len(h.platform)} platform-coupled path(s) ({', '.join(h.platform)}) — "
            "use a repo-relative path"
        )
    if h.redundant and not config.is_disabled("link.redundant"):
        ex = ", ".join(f"{t} linked {c}x" for t, c in h.redundant)
        parts.append(f"{len(h.redundant)} redundant link(s) ({ex})")
    return parts


def link_gate_violations(doc: SkillDoc, config: ScoringConfig) -> list[str]:
    """Gate messages for strict, enabled link sub-checks that have offenders (exit-1 source)."""
    h = _link_hygiene(doc)
    out: list[str] = []
    checks = (
        ("link.broken", bool(h.broken), f"broken link(s): {', '.join(h.broken)}"),
        (
            "link.case-mismatch",
            bool(h.case_mismatch),
            f"case-mismatched link(s): {', '.join(t for t, _ in h.case_mismatch)}",
        ),
        ("link.platform", bool(h.platform), f"platform-coupled path(s): {', '.join(h.platform)}"),
        (
            "link.redundant",
            bool(h.redundant),
            f"redundant link(s): {', '.join(t for t, _ in h.redundant)}",
        ),
    )
    for sub_id, has, msg in checks:
        if has and config.is_strict("Structural Coherence", sub_id) and not config.is_disabled(
            sub_id
        ):
            out.append(f"Structural Coherence [{sub_id}]: {msg}")
    return out


# --------------------------------------------------------------------------- #
# Code-maintainability helpers (radon + ast)
# --------------------------------------------------------------------------- #


def _python_maintainability(code: str) -> tuple[float, dict[str, Any]]:
    """Return (s in [0,1], metrics) for one Python script."""
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit
    except ImportError:
        return 0.5, {"error": "radon not installed (pip install skillspector-quality[code])"}

    metrics: dict[str, Any] = {}
    # Maintainability Index (0-100).
    try:
        mi = mi_visit(code, multi=True)
    except (SyntaxError, Exception):  # noqa: BLE001 - radon may raise various errors
        return 0.0, {"error": "unparseable"}
    metrics["mi"] = round(mi, 1)
    mi_norm = clamp01(mi / 100)

    # Average cyclomatic complexity.
    try:
        blocks = cc_visit(code)
        avg_cc = sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
    except (SyntaxError, Exception):  # noqa: BLE001
        blocks = []
        avg_cc = 1.0
    metrics["avg_cc"] = round(avg_cc, 1)
    cc_norm = clamp01((15 - avg_cc) / 14)

    # Docstring coverage via ast.
    try:
        tree = ast.parse(code)
        units = 1  # module
        documented = 1 if ast.get_docstring(tree) else 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                units += 1
                if ast.get_docstring(node):
                    documented += 1
        dc = documented / units
    except SyntaxError:
        dc = 0.0
    metrics["docstring_cov"] = round(dc, 2)

    # Comment density.
    lines = code.splitlines()
    comment_lines = sum(
        1 for ln in lines if ln.lstrip().startswith("#") and not ln.lstrip().startswith("#!")
    )
    code_lines = sum(1 for ln in lines if ln.strip() and not ln.lstrip().startswith("#"))
    cd = comment_lines / code_lines if code_lines else 0.0
    cd_norm = clamp01(cd / 0.10)
    metrics["comment_density"] = round(cd, 2)

    s = 0.40 * mi_norm + 0.25 * cc_norm + 0.20 * dc + 0.15 * cd_norm
    return s, metrics


def _other_script_quality(path: str, code: str) -> float:
    lines = code.splitlines()
    nonblank = [ln for ln in lines if ln.strip()]
    if not nonblank:
        return 0.0
    signals: list[float] = []
    if _ext(path) in SHELL_EXTS:
        signals.append(1.0 if lines and lines[0].startswith("#!") else 0.0)
    first = nonblank[0].lstrip()
    signals.append(1.0 if first.startswith(("#", "//", "/*", "--")) else 0.0)
    comment_lines = sum(
        1
        for ln in lines
        if ln.lstrip().startswith(("#", "//", "--")) and not ln.lstrip().startswith("#!")
    )
    code_lines = max(1, len(nonblank) - comment_lines)
    signals.append(clamp01((comment_lines / code_lines) / 0.10))
    signals.append(1.0 if 1 <= len(nonblank) <= 500 else 0.5)
    return sum(signals) / len(signals)


# --------------------------------------------------------------------------- #
# Dimensions (each: (name, weight, scorer))
# --------------------------------------------------------------------------- #


def dim_metadata(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    data = doc.data
    desc = data.get("description") or ""
    when = data.get("when_to_use") or ""
    _meta_raw = data.get("metadata")
    meta: dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    name = str(data.get("name") or "")
    # Only name and description are required by the official spec.
    # author/version are advisory only (ADR-0001): surfaced as guidance, never scored,
    # so their absence cannot lower the score.
    #
    # Trigger specificity is scored on `when_to_use` when set, else on `description`
    # (ADR-0007). Across 207 real skills, `when_to_use` appeared in ZERO of them while
    # `description` appeared in all 207 and is where authors actually write their triggers
    # ("Use when the user wants to…", "Do not use for…"). Scoring only the unused field made
    # this dimension a constant 0.88 for every skill — eight points that could not rank
    # anything, and the AGENTbench specificity model never ran on real input.
    trigger_text = when or desc
    trigger_source = "when_to_use" if when else "description"
    when_spec = _when_specificity(trigger_text) if trigger_text else 0.0
    name_ok = bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name))
    signals = [
        1.0 if 0 < len(desc) <= 1024 else (0.5 if desc else 0.0),  # required: description
        when_spec if trigger_text else 0.5,  # trigger specificity, scored where it is written
        1.0 if name_ok else 0.0,  # required: name
    ]
    s = sum(signals) / len(signals)
    missing_required = []
    if not desc:
        missing_required.append("description")
    if not name_ok:
        missing_required.append("name (kebab-case format required)")
    # Scored improvements move the number; advisory items (author/version) never do.
    scored_improvements = []
    if trigger_text and when_spec < 0.7:
        scored_improvements.append(
            f"trigger specificity in {trigger_source} — name the conditions that should "
            "invoke this skill and add a 'Do not use for X' exclusion"
        )
    advisory = []
    if not meta.get("author"):
        advisory.append("author")
    if not meta.get("version"):
        advisory.append("version")

    if missing_required:
        label = f"Required fields missing: {', '.join(missing_required)}"
        if scored_improvements:
            label += f" — also consider: {', '.join(scored_improvements)}"
    elif scored_improvements:
        label = f"Required fields present; consider: {', '.join(scored_improvements)} (improves agent ROI)"
    else:
        label = "All fields complete"
    if advisory:
        # Advisory note (ADR-0001): nice-to-have provenance, no effect on score.
        label += f" — advisory (no score impact): add {', '.join(advisory)} for provenance"
    return [(round(w * s), w, label)]


def dim_information_density(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    prose = doc.all_prose
    if not prose.strip():
        return [(0, w, "no prose to assess")]
    config = config or _EMPTY_CONFIG
    full_ratio = (
        DENSITY_FULL_RATIO_STRICT
        if config.is_strict("Information Density")
        else DENSITY_FULL_RATIO
    )
    r = _compression_ratio(prose)
    # Percentile-anchored ramp: zero at corpus p10 (0.387), full at p90 (0.501). Compression
    # ratio is length-invariant, so this cannot be raised by writing more — only by writing
    # denser, less redundant prose. See docs/adr/0007-percentile-calibration.md.
    density = clamp01((r - DENSITY_ZERO_RATIO) / (full_ratio - DENSITY_ZERO_RATIO))
    dup = _ngram_dup(_word_tokens(prose), n=5)
    s = 0.6 * density + 0.4 * (1 - dup)
    if dup > 0.3:
        label = f"Repeated phrases make up {dup:.0%} of content — reduce copy-paste text"
    elif density < 0.4:
        label = "Content is thin — add more concrete, specific detail"
    else:
        label = "Content is dense and non-repetitive"

    # Advisory (zero score impact, ADR-0001): name WHICH files overlap. The duplication is
    # already priced into `dup` above — this only attributes it, since `_ngram_dup` returns
    # one opaque fraction. Re-scoring it here would double-count (r=+0.951, ADR-0009).
    spans = [s for s in _duplicate_spans(doc) if s.shared_tokens >= 30]
    if spans:
        worst = "; ".join(f"{s.source} ↔ {s.target} (~{s.shared_tokens} tokens)" for s in spans[:3])
        label += (
            f" — advisory (no score impact): duplicated prose between {worst}"
            "; every duplicated token is paid twice"
        )
    return [(round(w * s), w, label)]


def dim_lexical_diversity(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    tokens = _word_tokens(doc.all_prose)
    if len(tokens) < LEXICAL_MIN_TOKENS:
        return []  # N/A: too little text for MTLD to be reliable
    config = config or _EMPTY_CONFIG
    full_mtld = (
        LEXICAL_FULL_MTLD_STRICT if config.is_strict("Lexical Diversity") else LEXICAL_FULL_MTLD
    )
    mtld = _mtld(tokens)
    # Percentile-anchored ramp: zero at corpus p10 (53.4), full at p90 (136.4). MTLD is
    # length-invariant by construction. See docs/adr/0007-percentile-calibration.md.
    s = clamp01((mtld - LEXICAL_ZERO_MTLD) / (full_mtld - LEXICAL_ZERO_MTLD))
    if s >= 0.7:
        label = f"Vocabulary is rich and varied ({len(tokens)} words)"
    elif s >= 0.4:
        label = f"Vocabulary is adequate but somewhat repetitive ({len(tokens)} words)"
    else:
        label = f"Vocabulary is repetitive — try using more varied language ({len(tokens)} words)"
    return [(round(w * s), w, label)]


def dim_readability(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    grades, words = _readability_grades(_prose_for_readability(doc))
    if not grades:
        return []  # N/A: <30 words of prose
    g = _median(grades)
    low, high = READABILITY_BAND
    if low <= g <= high:
        s = 1.0
    elif g < low:
        s = clamp01((g - 4) / (low - 4))
    else:
        s = clamp01((22 - g) / (22 - high))
    g_int = round(g)
    if low <= g <= high:
        label = f"Reading level: {g_int}th grade — good for technical documentation"
    elif g < low:
        label = f"Writing is too simple ({g_int}th grade) — add more technical depth"
    else:
        label = f"Writing is too complex ({g_int}th grade) — simplify for broader audiences"
    return [(round(w * s), w, label)]


def dim_topic_coverage(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    desc = doc.data.get("description") or ""
    body_terms = _terms(doc.body)
    if not body_terms:
        return [(0, w, "empty body")]

    corpus_terms = [body_terms] + [_terms(c) for c in doc.markdown_docs.values()]
    idf = _build_idf(corpus_terms)

    body_vec = _tfidf_vec(body_terms, idf)
    desc_vec = _tfidf_vec(_terms(desc), idf)
    coverage = _cosine(desc_vec, body_vec) if desc else 0.0

    # Percentile-anchored: zero at corpus p10, full at p90. Description-to-body coverage and
    # body-to-doc cohesion sit at different points in TF-IDF space (a terse description shares
    # fewer terms with the body than two full documents share with each other), so they get
    # separate anchors rather than the single hand-picked 0.5 they shared before.
    cov_norm = clamp01(
        (coverage - COVERAGE_ZERO_COSINE) / (COVERAGE_FULL_COSINE - COVERAGE_ZERO_COSINE)
    )

    if doc.markdown_docs:
        cohesions = [
            _cosine(body_vec, _tfidf_vec(_terms(c), idf)) for c in doc.markdown_docs.values()
        ]
        cohesion = sum(cohesions) / len(cohesions)
        coh_norm = clamp01(
            (cohesion - COHESION_ZERO_COSINE) / (COHESION_FULL_COSINE - COHESION_ZERO_COSINE)
        )
        s = 0.5 * cov_norm + 0.5 * coh_norm
        if s >= 0.9:
            label = "Description aligns well with skill content and supporting docs"
        elif coverage < 0.25:
            label = "Description doesn't match the skill body — rewrite it to reflect what the skill actually does"
        else:
            label = "Description partially matches skill content — refine it to better reflect actual functionality"
    else:
        s = cov_norm
        if cov_norm >= 0.9:
            label = "Description aligns well with skill content"
        elif coverage < 0.25:
            label = "Description doesn't match the skill body — rewrite it to reflect what the skill actually does"
        else:
            label = "Description partially matches skill content — refine it to better reflect actual functionality"
    return [(round(w * s), w, label)]


def dim_structural_coherence(
    doc: SkillDoc, w: int, config: ScoringConfig | None = None
) -> list[tuple[int, int, str]]:
    config = config or _EMPTY_CONFIG
    levels = _heading_levels(doc.body)
    if len(levels) <= 1:
        s_head = 1.0 if levels == [1] else 0.5
        skips = 0
    else:
        skips = sum(1 for a, b in zip(levels, levels[1:], strict=False) if b - a > 1)
        transitions = len(levels) - 1
        s_head = 1 - skips / transitions
    h1_count = sum(1 for lv in levels if lv == 1)
    if h1_count != 1:
        s_head *= 0.5

    adj, nodes = _link_graph(doc)
    if len(nodes) <= 1:
        reach = 1.0
    else:
        reachable = _reachable_from(adj, doc.skill_md_key)
        reach = len(reachable) / len(nodes)
    acyclic = 1.0 if _is_acyclic(adj) else 0.0

    hygiene = _link_hygiene(doc)
    link_valid = _link_valid_score(hygiene, config)

    s = 0.40 * s_head + 0.25 * reach + 0.10 * acyclic + 0.25 * link_valid
    parts: list[str] = []
    if skips > 0:
        parts.append(f"{skips} heading level skip(s) — avoid jumping over heading levels")
    else:
        parts.append("heading structure is correct")
    if reach < 1.0:
        unreachable = max(1, round(len(nodes) * (1 - reach)))
        parts.append(f"{unreachable} file(s) not linked from SKILL.md — add links to connect them")
    else:
        parts.append("all files are linked")
    if not acyclic:
        parts.append("circular links detected — fix link loops")
    parts.extend(_link_hygiene_labels(hygiene, config))
    label = "; ".join(parts)
    return [(round(w * s), w, label)]


def dim_code_maintainability(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    if not doc.scripts:
        return []  # N/A: omit, weights renormalize
    scores: list[float] = []
    py_detail = ""
    for path, code in sorted(doc.scripts.items()):
        if _ext(path) == ".py":
            s, m = _python_maintainability(code)
            if not py_detail and "mi" in m:
                py_detail = f" e.g. {path}: MI={m['mi']}, CC={m['avg_cc']}, docstrings={m['docstring_cov']:.0%}"
        else:
            s = _other_script_quality(path, code)
        scores.append(s)
    s = sum(scores) / len(scores)
    if s >= 0.8:
        label = f"{len(scores)} script(s) — code is clean and well-documented"
    elif s >= 0.5:
        label = f"{len(scores)} script(s) — code needs more documentation or has complex functions"
    else:
        label = f"{len(scores)} script(s) — code is hard to maintain; add docstrings and reduce complexity"
    return [(round(w * s), w, label)]


def dim_example_quality(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    """Score whether the skill concretely demonstrates itself, and how well (ADR-0007).

    Detection covers both ways real skills write examples — a naming heading, or a fenced
    block with explanatory prose. Scoring keeps a gradient over the ~96% that demonstrate
    something: *richness* (does each demonstration show a contrast an agent can generalize
    from) and *depth* (are demonstrations substantial), anchored to corpus percentiles.
    """
    demos = _demonstrations(doc)
    if not demos:
        if len(_word_tokens(doc.body)) < 100:
            return []  # N/A: minimal skill, examples not expected
        return [
            (
                0,
                w,
                "No worked examples found — show the skill in use with a fenced "
                "input/output block or an Example section",
            )
        ]

    richness = sum(_demo_richness(d) for d in demos) / len(demos)
    lengths = sorted(len(_word_tokens(d)) for d in demos)
    median_len = lengths[len(lengths) // 2]
    depth = clamp01(median_len / EXAMPLE_DEPTH_FULL)
    s = 0.6 * richness + 0.4 * depth

    if richness >= 0.8 and depth >= 0.8:
        label = f"{len(demos)} worked example(s) with clear input/output or before/after contrast"
    elif richness < 0.5:
        label = (
            f"{len(demos)} example(s) found, but most show only one side — "
            "add the expected output (or a before/after pair) so the shape is unambiguous"
        )
    else:
        label = (
            f"{len(demos)} example(s) found, but they are thin (median {median_len} words) — "
            "expand them to show a realistic case end to end"
        )
    return [(round(w * s), w, label)]


def dim_progressive_disclosure(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    """Score whether content is appropriately disclosed given its volume (ADR-0002).

    Reframed from "are reference.md + examples.md present?" to "is a large SKILL.md body
    pushed into linked supporting docs, one level deep?". Recognizes ANY supporting doc
    (arbitrary filenames, ``reference/`` folders) — not a fixed pair of names.

    * **Trigger** — body < 100 lines and no supporting docs => N/A (concise skill, nothing
      to disclose). Body > 500 lines => full expectation; 100-500 ramps linearly.
    * **Scored** — body-leanness vs. volume (a big body with no linked docs is penalized);
      a flatness penalty for any doc reachable only at depth >= 2 ("keep references one
      level deep").
    * **Advisory (zero weight)** — a supporting doc longer than 100 lines without a TOC.
    """
    body = doc.body
    body_lines = len(body.splitlines())
    supporting = {p: c for p, c in doc.markdown_docs.items() if c and c.strip()}
    if not supporting and body_lines < 100:
        return []  # N/A: concise skill without supporting files — follows best practices

    # How strongly does this body owe disclosure? 0 at <=100 lines, 1.0 at >=500.
    expectation = clamp01((body_lines - 100) / (500 - 100))

    adj, _nodes = _link_graph(doc)
    depths = _bfs_depths(adj, doc.skill_md_key)
    depth1 = [p for p in supporting if depths.get(p) == 1]
    nested = [p for p in supporting if depths.get(p, -1) >= 2]
    orphans = [p for p in supporting if p not in depths]

    # Signal 1 — leanness: a body that owes disclosure should have depth-1 docs.
    lean = 1.0 if depth1 else (1.0 - expectation)
    signals: list[float] = [lean]

    # Signal 2 — link quality: of the docs that exist, what fraction sit one level deep?
    # Penalizes both nesting (depth >= 2) and orphans (unreachable from SKILL.md).
    if supporting:
        signals.append(len(depth1) / len(supporting))

    s = sum(signals) / len(signals)

    # Advisory (no score impact): long docs that lack a table of contents.
    no_toc = sorted(p for p, c in supporting.items() if len(c.splitlines()) > 100 and not _has_toc(c))

    parts: list[str] = []
    if not supporting:
        parts.append(
            f"SKILL.md is {body_lines} lines with no supporting docs — "
            "move detail into linked reference files"
        )
    elif depth1 and not nested and not orphans:
        parts.append(f"{len(depth1)} supporting doc(s) linked one level deep from SKILL.md")
    elif depth1:
        parts.append(f"{len(depth1)} doc(s) linked directly")
    elif not depth1:
        parts.append("supporting docs exist but none are linked one level deep from SKILL.md")
    if nested:
        parts.append(
            f"{len(nested)} doc(s) nested >=2 levels deep ({', '.join(sorted(nested))}) — "
            "link them directly from SKILL.md"
        )
    if orphans:
        parts.append(
            f"{len(orphans)} doc(s) not linked from SKILL.md ({', '.join(sorted(orphans))}) — add links"
        )
    if no_toc:
        parts.append(
            f"advisory (no score impact): add a table of contents to {', '.join(no_toc)} "
            "(>100 lines) so partial reads see full scope"
        )
    label = "; ".join(parts) if parts else "Progressive disclosure looks healthy"
    return [(round(w * s), w, label)]


def dim_instruction_clarity(
    doc: SkillDoc, w: int, config: ScoringConfig | None = None
) -> list[tuple[int, int, str]]:
    """Score how directly the prose tells an agent what to do (ADR-0009).

    Two signals, both "lower is better" and both bottoming out at a genuine zero, so they are
    anchored full-marks-at-0 / zero-at-corpus-p90 rather than the usual p10/p90 ramp:

    * **Hedging density** — vague filler per 100 prose words ("appropriate", "as needed",
      "etc.", "various"). AGENTbench found this class of prose is precisely what makes context
      files cost tokens without improving task success. Length-invariant, so padding around it
      cannot dilute the measurement.
    * **Untagged code fences** — a fence with no language tag makes an agent guess whether a
      block is shell, JSON, or output. Strongly bimodal in the corpus: most skills tag
      everything, some tag nothing.

    N/A when there is too little prose to measure and no code fences to judge.
    """
    prose = _strip_fences_text(doc.body)
    tokens = _word_tokens(prose)
    tags = _fence_tags(doc.body)
    for content in doc.markdown_docs.values():
        tags.extend(_fence_tags(content))
    if len(tokens) < 50 and not tags:
        return []  # N/A: nothing to judge

    signals: list[float] = []
    parts: list[str] = []

    if len(tokens) >= 50:
        density = _hedge_density(prose)
        s_hedge = clamp01(1.0 - density / HEDGE_ZERO_DENSITY)
        signals.append(s_hedge)
        if s_hedge >= 0.8:
            parts.append("instructions are concrete")
        else:
            parts.append(
                f"{density:.2f} vague words per 100 ("
                "'appropriate', 'as needed', 'etc.') — replace with the specific condition"
            )

    if tags:
        untagged = sum(1 for t in tags if not t) / len(tags)
        s_fence = clamp01(1.0 - untagged / UNTAGGED_FENCE_ZERO)
        signals.append(s_fence)
        if untagged == 0:
            parts.append(f"all {len(tags)} code fence(s) tagged")
        else:
            parts.append(
                f"{round(untagged * len(tags))} of {len(tags)} code fence(s) have no language "
                "tag — add one (```bash, ```json) so the agent knows what it is reading"
            )

    s = sum(signals) / len(signals)
    return [(round(w * s), w, "; ".join(parts))]


def dim_behavioral_config(doc: SkillDoc, w: int, config: ScoringConfig | None = None) -> list[tuple[int, int, str]]:
    """Score the 13 behavioral/execution/lifecycle frontmatter fields.

    Returns N/A (empty list) when none of the 13 spec fields appear in the
    frontmatter, so simple skills that need no configuration are not penalized.
    For skills that do configure these fields, validity and consistency are
    checked: correct enum values, proper types, and coherent field combinations
    (e.g. ``agent`` should accompany ``context: fork``).

    Sub-weights (integer fractions of w, remainder goes to lifecycle):
      discovery 30%, constraints 40%, execution 20%, lifecycle = remainder.
    """
    data = doc.data

    if not any(f in data for f in _BEHAVIORAL_FIELDS):
        return []  # N/A: no behavioral config present; weight renormalizes away

    disc_w = max(1, w * 3 // 10)
    con_w = max(1, w * 4 // 10)
    exec_w = max(1, w * 2 // 10)
    hook_w = max(1, w - disc_w - con_w - exec_w)
    items: list[tuple[int, int, str]] = []

    # ------------------------------------------------------------------ #
    # 1. Discovery configuration                                          #
    # paths / user-invocable get neutral (0.5) when absent because they  #
    # are optional; argument-hint is required whenever arguments is set.  #
    # ------------------------------------------------------------------ #
    disc_signals: list[float] = []
    disc_parts: list[str] = []

    if "paths" in data:
        paths_val = data["paths"]
        valid = isinstance(paths_val, (str, list)) and bool(paths_val)
        disc_signals.append(1.0 if valid else 0.0)
        disc_parts.append(
            f"paths: {'valid ✓' if valid else 'empty or invalid — provide a glob pattern'}"
        )
    else:
        disc_signals.append(0.5)  # absent: neutral for general-scope skills
        disc_parts.append("paths: not set (skill applies to all files)")

    if "user-invocable" in data:
        valid = isinstance(data["user-invocable"], bool)
        disc_signals.append(1.0 if valid else 0.0)
        disc_parts.append(f"user-invocable: {'✓' if valid else 'invalid — must be true or false'}")
    else:
        disc_signals.append(0.5)  # absent: neutral
        disc_parts.append("user-invocable: not set (defaults to agent-only)")

    if "arguments" in data:
        has_hint = "argument-hint" in data and bool(data.get("argument-hint"))
        disc_signals.append(1.0 if has_hint else 0.0)
        disc_parts.append(
            f"argument-hint: {'✓' if has_hint else 'missing — required when arguments is set'}"
        )
    elif "argument-hint" in data:
        disc_signals.append(0.8)  # hint set without arguments: unusual but not wrong
        disc_parts.append("argument-hint: set (no arguments field — consider adding one)")

    disc_s = sum(disc_signals) / len(disc_signals)
    items.append((round(disc_w * disc_s), disc_w, "Agent discovery: " + "; ".join(disc_parts)))

    # ------------------------------------------------------------------ #
    # 2. Behavioral constraints                                           #
    # Validate types when fields are present; full credit when absent     #
    # (no constraints is a valid configuration).                          #
    # ------------------------------------------------------------------ #
    con_signals: list[float] = []
    con_parts: list[str] = []

    for key in ("allowed-tools", "disallowed-tools"):
        if key in data:
            valid = isinstance(data[key], (str, list))
            con_signals.append(1.0 if valid else 0.0)
            con_parts.append(
                f"{key}: {'valid ✓' if valid else 'invalid — must be a string or list'}"
            )

    if "disable-model-invocation" in data:
        valid = isinstance(data["disable-model-invocation"], bool)
        con_signals.append(1.0 if valid else 0.0)
        con_parts.append(
            f"disable-model-invocation: {'✓' if valid else 'invalid — must be true or false'}"
        )

    if not con_signals:
        con_s = 1.0  # nothing configured: defaults apply, nothing wrong
        con_parts.append("no tool restrictions (all tools allowed by default)")
    else:
        con_s = sum(con_signals) / len(con_signals)
    items.append((round(con_w * con_s), con_w, "Tool restrictions: " + "; ".join(con_parts)))

    # ------------------------------------------------------------------ #
    # 3. Execution configuration                                          #
    # Validate enum values; check that agent accompanies context:fork.   #
    # ------------------------------------------------------------------ #
    exec_signals: list[float] = []
    exec_parts: list[str] = []

    if "context" in data:
        ctx = data.get("context")
        valid_ctx = ctx in _VALID_CONTEXT
        exec_signals.append(1.0 if valid_ctx else 0.0)
        # Built outside the f-string on purpose: reusing double quotes inside a
        # "-delimited f-string is PEP 701 syntax (3.12+). The fuzzing base image parses
        # this file with Python 3.11, where it is a SyntaxError — and PyInstaller drops
        # the unparseable module instead of failing, yielding a broken fuzz target.
        ctx_note = "✓" if valid_ctx else '— invalid (only "fork" is allowed)'
        exec_parts.append(f"context: {ctx} {ctx_note}")
        if valid_ctx and ctx == "fork" and "agent" not in data:
            exec_signals.append(0.0)
            exec_parts.append("agent: missing — recommended when context is fork")
        elif "agent" in data:
            exec_signals.append(1.0)
            exec_parts.append(f"agent: {data['agent']} ✓")

    if "effort" in data:
        val = data.get("effort")
        valid = val in _VALID_EFFORT
        exec_signals.append(1.0 if valid else 0.0)
        # Same 3.11-parseability constraint as the context note above.
        allowed = ", ".join(sorted(_VALID_EFFORT))
        effort_note = "✓" if valid else f"— invalid (must be one of: {allowed})"
        exec_parts.append(f"effort: {val} {effort_note}")

    if "shell" in data:
        val = str(data.get("shell") or "").lower()
        valid = val in _VALID_SHELL
        exec_signals.append(1.0 if valid else 0.0)
        exec_parts.append(
            f"shell: {data['shell']} {'✓' if valid else '— invalid (must be bash or powershell)'}"
        )

    if "model" in data and data.get("model") is not None:
        exec_signals.append(1.0)  # any non-null model string is structurally valid
        exec_parts.append(f"model: {data['model']} ✓")

    if not exec_signals:
        exec_s = 1.0  # no execution overrides: defaults apply, nothing wrong
        exec_parts.append("no execution overrides (using defaults)")
    else:
        exec_s = sum(exec_signals) / len(exec_signals)
    items.append((round(exec_w * exec_s), exec_w, "Execution settings: " + "; ".join(exec_parts)))

    # ------------------------------------------------------------------ #
    # 4. Lifecycle hooks                                                  #
    # hooks must be a non-empty dict when set; absent is fine.            #
    # ------------------------------------------------------------------ #
    if "hooks" in data:
        hooks = data.get("hooks")
        valid = isinstance(hooks, dict) and len(hooks) > 0
        hook_s = 1.0 if valid else 0.0
        hook_label = f"hooks: {'configured ✓' if valid else 'invalid — must be a non-empty object with event keys'}"
    else:
        hook_s = 1.0  # absent: lifecycle defaults apply
        hook_label = "hooks: not set (no lifecycle hooks)"
    items.append((round(hook_w * hook_s), hook_w, "Lifecycle hooks: " + hook_label))

    return items


# --------------------------------------------------------------------------- #
# Registry: (display name, weight, scorer). Weights sum to 100 for prose-only #
# skills; skills with behavioral config fields are scored over 110.            #
# --------------------------------------------------------------------------- #

ScorerFn = Callable[[SkillDoc, int, "ScoringConfig | None"], list[tuple[int, int, str]]]
BoundScorerFn = Callable[..., list[tuple[int, int, str]]]


def _bind(fn: ScorerFn, w: int) -> BoundScorerFn:
    def bound(
        doc: SkillDoc, config: ScoringConfig | None = None
    ) -> list[tuple[int, int, str]]:
        return fn(doc, w, config)

    return bound


DIMENSIONS: list[tuple[str, int, ScorerFn]] = [
    ("Metadata & Discovery", 8, dim_metadata),
    ("Information Density", 15, dim_information_density),  # raised: redundancy = wasted tokens
    ("Lexical Diversity", 6, dim_lexical_diversity),  # lowered: ceded 3pts to Progressive Disclosure
    ("Readability", 10, dim_readability),
    ("Topic Coverage", 15, dim_topic_coverage),
    ("Structural Coherence", 13, dim_structural_coherence),
    ("Code Maintainability", 15, dim_code_maintainability),
    ("Example Quality", 10, dim_example_quality),
    ("Progressive Disclosure", 8, dim_progressive_disclosure),  # raised: now penalizes bloated body + nesting
    ("Instruction Clarity", 8, dim_instruction_clarity),  # ADR-0009: hedging + untagged fences
    ("Behavioral Configuration", 10, dim_behavioral_config),
]

# Back-compat alias: the engine iterates (name, scorer) pairs; bind the weight.
CATEGORY_SCORERS: list[tuple[str, BoundScorerFn]] = [
    (name, _bind(fn, w)) for name, w, fn in DIMENSIONS
]

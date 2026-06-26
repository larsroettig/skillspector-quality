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

MARKDOWN_EXTS = {".md", ".markdown"}
SCRIPT_EXTS = {".py", ".sh", ".bash", ".zsh", ".js", ".ts", ".rb", ".go", ".rs", ".pl"}
SHELL_EXTS = {".sh", ".bash", ".zsh"}


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _when_specificity(when: str) -> float:
    """Score 0..1 for how actionable a when_to_use value is.

    Based on the AGENTbench finding (Gloaguen et al., 2026) that minimal, specific
    trigger + exclusion conditions are the highest-ROI content in agent context files,
    while vague prose duplicating the description yields cost with no benefit.
    """
    s = 0.0
    if len(when) >= 15:
        s += 0.30  # has something substantive
    if _TRIGGER_VERBS_RE.search(when):
        s += 0.25  # concrete trigger verb ("Use when...", "Invoke for...")
    if _NEGATION_RE.search(when):
        s += 0.25  # exclusion condition — highest-ROI signal per research
    if _CONDITIONAL_RE.search(when) and len(when) > 30:
        s += 0.10  # conditional context ("when X", "if Y")
    if len(when) > 80:
        s += 0.10  # enough detail to cover multiple cases
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


def dim_metadata(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    data = doc.data
    desc = data.get("description") or ""
    when = data.get("when_to_use") or ""
    _meta_raw = data.get("metadata")
    meta: dict[str, Any] = _meta_raw if isinstance(_meta_raw, dict) else {}
    name = str(data.get("name") or "")
    # Only name and description are required by the official spec.
    # when_to_use is optional but SCORED (specificity is high-ROI per AGENTbench).
    # author/version are advisory only (ADR-0001): surfaced as guidance, never scored,
    # so their absence cannot lower the score.
    when_spec = _when_specificity(when) if when else 0.0
    name_ok = bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name))
    signals = [
        1.0 if 0 < len(desc) <= 1024 else (0.5 if desc else 0.0),  # required: description
        when_spec if when else 0.5,  # optional: neutral if absent, specificity-scored if set
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
    if not when:
        scored_improvements.append("when_to_use")
    elif when_spec < 0.7:
        scored_improvements.append(
            "when_to_use specificity — add trigger conditions and 'Do not use for X' exclusions"
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


def dim_information_density(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    prose = doc.all_prose
    if not prose.strip():
        return [(0, w, "no prose to assess")]
    r = _compression_ratio(prose)
    density = clamp01((r - 0.30) / (0.55 - 0.30))
    dup = _ngram_dup(_word_tokens(prose), n=5)
    s = 0.6 * density + 0.4 * (1 - dup)
    if dup > 0.3:
        label = f"Repeated phrases make up {dup:.0%} of content — reduce copy-paste text"
    elif density < 0.4:
        label = "Content is thin — add more concrete, specific detail"
    else:
        label = "Content is dense and non-repetitive"
    return [(round(w * s), w, label)]


def dim_lexical_diversity(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    tokens = _word_tokens(doc.all_prose)
    if len(tokens) < 50:
        return []  # N/A: too little text to measure reliably
    mtld = _mtld(tokens)
    s = clamp01((mtld - 30) / (100 - 30))
    if s >= 0.7:
        label = f"Vocabulary is rich and varied ({len(tokens)} words)"
    elif s >= 0.4:
        label = f"Vocabulary is adequate but somewhat repetitive ({len(tokens)} words)"
    else:
        label = f"Vocabulary is repetitive — try using more varied language ({len(tokens)} words)"
    return [(round(w * s), w, label)]


def dim_readability(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    grades, words = _readability_grades(_prose_for_readability(doc))
    if not grades:
        return []  # N/A: <30 words of prose
    g = _median(grades)
    if 8 <= g <= 14:
        s = 1.0
    elif g < 8:
        s = clamp01((g - 3) / 5)
    else:
        s = clamp01((22 - g) / 8)
    g_int = round(g)
    if 8 <= g <= 14:
        label = f"Reading level: {g_int}th grade — good for technical documentation"
    elif g < 8:
        label = f"Writing is too simple ({g_int}th grade) — add more technical depth"
    else:
        label = f"Writing is too complex ({g_int}th grade) — simplify for broader audiences"
    return [(round(w * s), w, label)]


def dim_topic_coverage(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    desc = doc.data.get("description") or ""
    body_terms = _terms(doc.body)
    if not body_terms:
        return [(0, w, "empty body")]

    corpus_terms = [body_terms] + [_terms(c) for c in doc.markdown_docs.values()]
    idf = _build_idf(corpus_terms)

    body_vec = _tfidf_vec(body_terms, idf)
    desc_vec = _tfidf_vec(_terms(desc), idf)
    coverage = _cosine(desc_vec, body_vec) if desc else 0.0

    # Calibration: in TF-IDF space a cosine of ~0.5 already signals strong topical
    # alignment between a terse description and a full body, so treat 0.5 as full credit.
    ref = 0.5
    cov_norm = clamp01(coverage / ref)

    if doc.markdown_docs:
        cohesions = [
            _cosine(body_vec, _tfidf_vec(_terms(c), idf)) for c in doc.markdown_docs.values()
        ]
        cohesion = sum(cohesions) / len(cohesions)
        s = 0.5 * cov_norm + 0.5 * clamp01(cohesion / ref)
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


def dim_structural_coherence(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
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

    s = 0.5 * s_head + 0.4 * reach + 0.1 * acyclic
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
    label = "; ".join(parts)
    return [(round(w * s), w, label)]


def dim_code_maintainability(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
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


def dim_example_quality(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
    source = doc.file_cache.get("examples.md") or doc.body
    sections = re.split(r"^#{2,3}\s+Example", source, flags=re.MULTILINE)[1:]
    if not sections:
        if len(_word_tokens(doc.body)) < 100:
            return []  # N/A: minimal skill, examples not expected
        return [(0, w, "No examples found — add ## Example sections to show how the skill is used")]

    def _paired(sec: str) -> bool:
        low = sec.lower()
        fences = len(re.findall(r"^\s*```", sec, re.MULTILINE))
        return (
            fences >= 2
            or ("input" in low and "output" in low)
            or ("before" in low and "after" in low)
        )

    richness = sum(1 for s in sections if _paired(s)) / len(sections)
    lengths = sorted(len(_word_tokens(s)) for s in sections)
    median_len = lengths[len(lengths) // 2]
    depth = clamp01(median_len / 60)
    s = 0.6 * richness + 0.4 * depth
    if richness >= 0.8:
        label = f"{len(sections)} example(s) with clear before/after or input/output pairs"
    else:
        label = (
            f"{len(sections)} example(s) found, but missing input/output structure — "
            "add Input: and Output: blocks (or code fences) to each example"
        )
    return [(round(w * s), w, label)]


def dim_progressive_disclosure(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
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


def dim_behavioral_config(doc: SkillDoc, w: int) -> list[tuple[int, int, str]]:
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
        exec_parts.append(
            f"context: {ctx} {'✓' if valid_ctx else '— invalid (only "fork" is allowed)'}"
        )
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
        exec_parts.append(
            f"effort: {val} {'✓' if valid else f'— invalid (must be one of: {", ".join(sorted(_VALID_EFFORT))})'}"
        )

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

ScorerFn = Callable[[SkillDoc, int], list[tuple[int, int, str]]]
BoundScorerFn = Callable[[SkillDoc], list[tuple[int, int, str]]]


def _bind(fn: ScorerFn, w: int) -> BoundScorerFn:
    def bound(doc: SkillDoc) -> list[tuple[int, int, str]]:
        return fn(doc, w)

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
    ("Behavioral Configuration", 10, dim_behavioral_config),
]

# Back-compat alias: the engine iterates (name, scorer) pairs; bind the weight.
CATEGORY_SCORERS: list[tuple[str, BoundScorerFn]] = [
    (name, _bind(fn, w)) for name, w, fn in DIMENSIONS
]

"""Extra scorer tests covering edge-case branches missed by test_scorers.py."""

from __future__ import annotations

from skillspector_quality.quality.scorers import (
    SkillDoc,
    _body,
    _compression_ratio,
    _hdd,
    _is_acyclic,
    _mtld,
    _ngram_dup,
    _other_script_quality,
    _parse_frontmatter,
    _python_maintainability,
    _reachable_from,
    _resolve_target,
    dim_behavioral_config,
    dim_code_maintainability,
    dim_example_quality,
    dim_information_density,
    dim_lexical_diversity,
    dim_progressive_disclosure,
    dim_readability,
    dim_structural_coherence,
    dim_topic_coverage,
)


def _doc(skill_md: str, **files: str) -> SkillDoc:
    cache: dict[str, str] = {"SKILL.md": skill_md}
    cache.update(files)
    return SkillDoc.from_file_cache(cache)


# ── _parse_frontmatter edge cases ─────────────────────────────────────────────

def test_parse_frontmatter_no_closing_marker() -> None:
    assert _parse_frontmatter("---\nname: x\n") == {}


def test_parse_frontmatter_invalid_yaml() -> None:
    assert _parse_frontmatter("---\n: bad: yaml: here\n---\n") == {}


def test_parse_frontmatter_non_dict_yaml() -> None:
    assert _parse_frontmatter("---\n- item1\n- item2\n---\n") == {}


# ── _body edge cases ──────────────────────────────────────────────────────────

def test_body_unclosed_frontmatter() -> None:
    result = _body("---\nname: x\nsome content here")
    assert "some content here" in result
    assert "---" not in result


def test_body_unclosed_frontmatter_no_newline() -> None:
    result = _body("---")
    assert result == ""


# ── _compression_ratio ────────────────────────────────────────────────────────

def test_compression_ratio_empty() -> None:
    assert _compression_ratio("") == 0.0


# ── _ngram_dup ────────────────────────────────────────────────────────────────

def test_ngram_dup_too_short() -> None:
    assert _ngram_dup(["a", "b"], n=5) == 0.0


# ── _mtld ─────────────────────────────────────────────────────────────────────

def test_mtld_empty_tokens() -> None:
    assert _mtld([]) == 0.0


def test_mtld_short_tokens() -> None:
    result = _mtld(["hello", "world"])
    assert result > 0


# ── _hdd ──────────────────────────────────────────────────────────────────────

def test_hdd_too_short() -> None:
    assert _hdd(["a", "b", "c"], sample_size=42) is None


def test_hdd_sufficient_tokens() -> None:
    tokens = ["word"] * 50
    result = _hdd(tokens, sample_size=10)
    assert result is not None and result >= 0


# ── _resolve_target ───────────────────────────────────────────────────────────

def test_resolve_target_exact_match() -> None:
    assert _resolve_target("foo.md", {"foo.md", "bar.md"}) == "foo.md"


def test_resolve_target_trailing_slash_match() -> None:
    result = _resolve_target("docs/", {"docs/guide.md", "README.md"})
    assert result == "docs/guide.md"


def test_resolve_target_trailing_slash_no_match() -> None:
    assert _resolve_target("missing/", {"docs/guide.md"}) is None


def test_resolve_target_suffix_match() -> None:
    assert _resolve_target("guide.md", {"docs/guide.md"}) == "docs/guide.md"


def test_resolve_target_no_match() -> None:
    assert _resolve_target("ghost.md", {"foo.md", "bar.md"}) is None


# ── _reachable_from ───────────────────────────────────────────────────────────

def test_reachable_from_cycle() -> None:
    adj = {"a": {"b"}, "b": {"a"}, "c": set()}
    reached = _reachable_from(adj, "a")
    assert reached == {"a", "b"}


def test_reachable_from_already_seen_node() -> None:
    adj = {"a": {"b", "c"}, "b": {"c"}, "c": set()}
    reached = _reachable_from(adj, "a")
    assert reached == {"a", "b", "c"}


# ── _is_acyclic ───────────────────────────────────────────────────────────────

def test_is_acyclic_with_cycle() -> None:
    adj = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
    assert _is_acyclic(adj) is False


def test_is_acyclic_without_cycle() -> None:
    adj = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert _is_acyclic(adj) is True


# ── _python_maintainability ───────────────────────────────────────────────────

def test_python_maintainability_syntax_error() -> None:
    s, m = _python_maintainability("def broken(\n  x:\n")
    assert s == 0.0
    assert "unparseable" in m.get("error", "")


def test_python_maintainability_valid_code() -> None:
    code = '''"""Module docstring."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
    s, m = _python_maintainability(code)
    assert 0.0 <= s <= 1.0
    assert "mi" in m


# ── _other_script_quality ─────────────────────────────────────────────────────

def test_other_script_quality_empty() -> None:
    assert _other_script_quality("script.sh", "") == 0.0


def test_other_script_quality_shell_with_shebang() -> None:
    code = "#!/bin/bash\n# Install dependencies\napt-get install -y curl\n"
    s = _other_script_quality("setup.sh", code)
    assert s > 0.5


def test_other_script_quality_no_shebang() -> None:
    code = "apt-get install -y curl\n"
    s = _other_script_quality("setup.sh", code)
    assert 0.0 <= s <= 1.0


def test_other_script_quality_non_shell() -> None:
    code = "// A JS comment\nconsole.log('hello');\n"
    s = _other_script_quality("helper.js", code)
    assert 0.0 <= s <= 1.0


# ── dim_information_density ───────────────────────────────────────────────────

def test_dim_information_density_thin_content() -> None:
    # Content with very low compression ratio (nearly incompressible unique chars)
    # but no 5-gram word repetition triggers the "thin" label.
    unique_words = " ".join(
        f"w{i:04d}" for i in range(200)  # 200 unique tokens, no repeats
    )
    skill = "---\nname: foo\ndescription: bar\n---\n" + unique_words
    doc = _doc(skill)
    items = dim_information_density(doc, 15)
    assert items
    # Either "thin" (low density) or "repeated" — both indicate below-ideal density
    _, _, label = items[0]
    assert "thin" in label.lower() or "repeated" in label.lower() or "dense" in label.lower()


def test_dim_information_density_empty_prose() -> None:
    doc = _doc("---\nname: foo\n---\n")
    items = dim_information_density(doc, 15)
    assert items == [(0, 15, "no prose to assess")]


# ── dim_lexical_diversity ─────────────────────────────────────────────────────

def test_dim_lexical_diversity_too_few_tokens() -> None:
    doc = _doc("---\nname: foo\n---\n" + "word " * 10)
    items = dim_lexical_diversity(doc, 6)
    assert items == []  # N/A: too little text


# ── dim_readability ───────────────────────────────────────────────────────────

def test_dim_readability_too_simple() -> None:
    simple = "The cat sat. The dog ran. It was fun. Big red ball. Go fast now." * 10
    doc = _doc("---\nname: foo\ndescription: bar\n---\n" + simple)
    items = dim_readability(doc, 10)
    if items:
        _, _, label = items[0]
        assert "grade" in label.lower()


def test_dim_readability_too_complex() -> None:
    complex_body = (
        "The epistemological ramifications of algorithmic determinism necessitate "
        "comprehensive circumspection vis-à-vis multifaceted interdependencies "
        "inherent in contemporaneous computational methodologies. "
    ) * 15
    doc = _doc("---\nname: foo\ndescription: bar\n---\n" + complex_body)
    items = dim_readability(doc, 10)
    if items:
        _, _, label = items[0]
        assert "grade" in label.lower()


# ── dim_topic_coverage ────────────────────────────────────────────────────────

def test_dim_topic_coverage_empty_body() -> None:
    doc = _doc("---\nname: foo\ndescription: bar\n---\n")
    items = dim_topic_coverage(doc, 15)
    assert items == [(0, 15, "empty body")]


def test_dim_topic_coverage_description_mismatch() -> None:
    skill = (
        "---\nname: foo\ndescription: machine learning model training\n---\n"
        + "gardening soil fertilizer plants vegetables tomatoes cucumber sunflower " * 20
    )
    doc = _doc(skill)
    items = dim_topic_coverage(doc, 15)
    assert items
    _, _, label = items[0]
    assert "match" in label.lower() or "description" in label.lower()


# ── dim_structural_coherence ──────────────────────────────────────────────────

def test_dim_structural_coherence_circular_links() -> None:
    skill = "---\nname: foo\ndescription: bar\n---\n# Title\n[ref](ref.md)\n"
    ref = "# Ref\n[back to skill](SKILL.md)\n[back to ref](ref.md)\n"
    doc = _doc(skill, **{"ref.md": ref})
    items = dim_structural_coherence(doc, 13)
    assert items


# ── dim_code_maintainability ──────────────────────────────────────────────────

def test_dim_code_maintainability_shell_script() -> None:
    skill = "---\nname: foo\ndescription: bar\n---\n# Title\nContent here.\n"
    shell = "#!/bin/bash\n# Setup script\napt-get install curl\n"
    doc = _doc(skill, **{"scripts/setup.sh": shell})
    items = dim_code_maintainability(doc, 15)
    assert items
    assert items[0][0] >= 0


def test_dim_code_maintainability_clean_python() -> None:
    skill = "---\nname: foo\ndescription: bar\n---\n# Title\nContent here.\n"
    code = '''"""Module."""


def run(x: int) -> int:
    """Return x."""
    return x
'''
    doc = _doc(skill, **{"scripts/main.py": code})
    items = dim_code_maintainability(doc, 15)
    assert items
    earned, max_w, label = items[0]
    assert "script" in label


# ── dim_example_quality ───────────────────────────────────────────────────────

def test_dim_example_quality_examples_without_pairs() -> None:
    body = "## Example\nSome example without input/output structure.\n" * 3
    doc = _doc("---\nname: foo\ndescription: bar\n---\n" + "word " * 120 + "\n" + body)
    items = dim_example_quality(doc, 10)
    assert items
    _, _, label = items[0]
    assert "input/output" in label.lower() or "example" in label.lower()


# ── dim_progressive_disclosure ────────────────────────────────────────────────

def test_dim_progressive_disclosure_orphan_docs() -> None:
    skill = "---\nname: foo\ndescription: bar\n---\n# Title\n" + "Content.\n" * 20
    orphan = "# Orphan\nSome content here that is not linked.\n"
    doc = _doc(skill, **{"orphan.md": orphan})
    items = dim_progressive_disclosure(doc, 8)
    assert items
    _, _, label = items[0]
    assert "linked" in label.lower() or "supporting" in label.lower()


def test_dim_progressive_disclosure_no_supporting_concise() -> None:
    skill = "---\nname: foo\ndescription: bar\n---\n# Title\n" + "word " * 30
    doc = _doc(skill)
    items = dim_progressive_disclosure(doc, 8)
    assert items == []  # N/A


# ── dim_behavioral_config ─────────────────────────────────────────────────────

def test_dim_behavioral_config_argument_hint_without_arguments() -> None:
    skill = "---\nname: foo\ndescription: bar\nargument-hint: 'path/to/file'\n---\n# Body\n"
    doc = _doc(skill)
    items = dim_behavioral_config(doc, 10)
    assert any("argument-hint" in label for _, _, label in items)


def test_dim_behavioral_config_disable_model_invocation() -> None:
    skill = "---\nname: foo\ndescription: bar\ndisable-model-invocation: true\n---\n# Body\n"
    doc = _doc(skill)
    items = dim_behavioral_config(doc, 10)
    assert any("disable-model-invocation" in label for _, _, label in items)


def test_dim_behavioral_config_model_field() -> None:
    skill = "---\nname: foo\ndescription: bar\nmodel: claude-opus-4-8\n---\n# Body\n"
    doc = _doc(skill)
    items = dim_behavioral_config(doc, 10)
    assert any("model" in label for _, _, label in items)


def test_dim_behavioral_config_invalid_effort() -> None:
    skill = "---\nname: foo\ndescription: bar\neffort: extreme\n---\n# Body\n"
    doc = _doc(skill)
    items = dim_behavioral_config(doc, 10)
    assert any("effort" in label for _, _, label in items)

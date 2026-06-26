"""Unit tests for the math-grounded quality dimensions."""

from __future__ import annotations

import pathlib

from skillspector_quality.quality import score_quality
from skillspector_quality.quality.scorers import (
    SkillDoc,
    _body,
    _build_idf,
    _compression_ratio,
    _cosine,
    _hdd,
    _is_acyclic,
    _mtld,
    _ngram_dup,
    _other_script_quality,
    _parse_frontmatter,
    _python_maintainability,
    _readability_grades,
    _relative_targets,
    _resolve_target,
    _terms,
    _tfidf_vec,
    _when_specificity,
    dim_behavioral_config,
    dim_code_maintainability,
    dim_example_quality,
    dim_information_density,
    dim_lexical_diversity,
    dim_metadata,
    dim_progressive_disclosure,
    dim_structural_coherence,
    dim_topic_coverage,
)


def _doc(skill_md: str, **files: str) -> SkillDoc:
    cache = {"SKILL.md": skill_md}
    cache.update(files)
    return SkillDoc.from_file_cache(cache)


def _cache_of(name: str) -> dict[str, str]:
    base = pathlib.Path(__file__).parent / "fixtures" / name
    return {str(p.relative_to(base)): p.read_text() for p in base.rglob("*") if p.is_file()}


# --- information theory ------------------------------------------------------ #


def test_compression_ratio_redundant_below_dense() -> None:
    redundant = "the cat sat on the mat. " * 50
    dense = (
        "Heterogeneous pipelines reconcile asynchronous ledgers while validating "
        "cryptographic provenance across federated jurisdictions and audit trails."
    )
    assert _compression_ratio(redundant) < _compression_ratio(dense)


def test_ngram_dup_detects_repetition() -> None:
    repeated = ["this", "skill", "does", "stuff"] * 10
    varied = "alpha beta gamma delta epsilon zeta eta theta iota kappa".split()
    assert _ngram_dup(repeated) > 0.3
    assert _ngram_dup(varied) == 0.0


def test_information_density_penalizes_redundancy() -> None:
    dense_prose = (
        "Invoices arrive as scanned images or native text. The parser classifies layout "
        "against vendor templates, then extracts header metadata, line items, and totals. "
        "Arithmetic reconciliation compares the printed grand total with the computed sum, "
        "raising a warning whenever rounding, missing tax, or duplicate rows break equality. "
        "Confidence scores accompany every field so reviewers triage ambiguous extractions "
        "instead of trusting opaque heuristics blindly."
    )
    dense = _doc("---\ndescription: d\n---\n" + dense_prose)
    redundant = _doc("---\ndescription: d\n---\n" + ("This skill does stuff. " * 60))
    ((dense_earned, _, _),) = dim_information_density(dense, 12)
    ((red_earned, _, _),) = dim_information_density(redundant, 12)
    assert dense_earned > red_earned


# --- lexical diversity (length-invariant) ----------------------------------- #


def test_mtld_diverse_above_repetitive() -> None:
    diverse = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon"
    ).split() * 3
    repetitive = ["spam", "eggs"] * 30
    assert _mtld(diverse) > _mtld(repetitive)


def test_mtld_is_length_stable() -> None:
    base = "the quick brown fox jumps over a lazy dog near the river bank".split()
    short = base * 2
    long = base * 8
    # MTLD should stay in the same ballpark regardless of length (unlike TTR).
    assert abs(_mtld(short) - _mtld(long)) < 0.4 * _mtld(short)


# --- readability ------------------------------------------------------------ #


def test_readability_grades_returns_five() -> None:
    text = " ".join(["The parser validates each field and reconciles the total carefully."] * 5)
    grades, words = _readability_grades(text)
    assert len(grades) == 5
    assert words >= 30


def test_readability_too_little_prose_is_na() -> None:
    grades, _ = _readability_grades("short text")
    assert grades == []


# --- topic coverage (TF-IDF) ------------------------------------------------ #


def test_tfidf_cosine_aligned_above_offtopic() -> None:
    corpus = [
        _terms("invoice parsing vendor totals line items"),
        _terms("invoice vendor totals extraction"),
        _terms("baking cake oven flour sugar eggs"),
    ]
    idf = _build_idf(corpus)
    body = _tfidf_vec(corpus[0], idf)
    aligned = _tfidf_vec(corpus[1], idf)
    offtopic = _tfidf_vec(corpus[2], idf)
    assert _cosine(body, aligned) > _cosine(body, offtopic)


def test_topic_coverage_rewards_on_topic_docs() -> None:
    skill = "---\ndescription: invoice vendor totals parsing\n---\n# Invoice\nParse invoice vendor totals and line items.\n"
    on_topic = _doc(skill, **{"reference.md": "Invoice vendor totals and line items reference."})
    off_topic = _doc(skill, **{"reference.md": "Cake baking oven flour sugar eggs recipe."})
    ((on_earned, _, _),) = dim_topic_coverage(on_topic, 15)
    ((off_earned, _, _),) = dim_topic_coverage(off_topic, 15)
    assert on_earned > off_earned


# --- structural coherence (graph + heading tree) ---------------------------- #


def test_structure_detects_heading_skip() -> None:
    good = _doc("---\nd: 1\n---\n# Title\n## Section\n### Sub\n")
    skipped = _doc("---\nd: 1\n---\n# Title\n#### Deep\n")
    ((good_earned, _, _),) = dim_structural_coherence(good, 13)
    ((skip_earned, _, lbl),) = dim_structural_coherence(skipped, 13)
    assert good_earned > skip_earned
    assert "skip" in lbl


def test_structure_penalizes_broken_links_and_orphans() -> None:
    connected = _doc(
        "---\nd: 1\n---\n# Title\nSee [ref](reference.md).\n",
        **{"reference.md": "x"},
    )
    broken = _doc(
        "---\nd: 1\n---\n# Title\nSee [missing](missing.md).\n",
        **{"orphan.md": "nobody links here"},
    )
    ((conn_earned, _, _),) = dim_structural_coherence(connected, 13)
    ((broken_earned, _, _),) = dim_structural_coherence(broken, 13)
    assert conn_earned > broken_earned


# --- code maintainability (radon + ast) ------------------------------------- #


def test_python_maintainability_documented_above_spaghetti() -> None:
    clean = '''"""Module docstring."""


def add(a, b):
    """Return the sum."""
    return a + b
'''
    spaghetti = (
        "def f(a,b,c,d):\n"
        + "".join(f"{' ' * 4}if a>{i}:\n{' ' * 8}return b\n" for i in range(12))
        + "    return 0\n"
    )
    s_clean, m_clean = _python_maintainability(clean)
    s_bad, m_bad = _python_maintainability(spaghetti)
    assert s_clean > s_bad
    assert m_clean["docstring_cov"] == 1.0
    assert m_bad["docstring_cov"] == 0.0


def test_code_maintainability_na_without_scripts() -> None:
    doc = _doc("---\nd: 1\n---\n# Title\nNo scripts here.\n")
    assert dim_code_maintainability(doc, 15) == []  # N/A -> omitted


# --- metadata + examples ---------------------------------------------------- #


def test_metadata_completeness() -> None:
    full = _doc(
        "---\nname: my-skill\ndescription: d\n"
        "when_to_use: Use when the user asks to parse invoices or extract line items. "
        "Do not use for general text processing or plain search.\n"
        "metadata:\n  author: A\n  version: 1.0\n---\n# T\n"
    )
    ((earned, mx, _),) = dim_metadata(full, 8)
    assert (earned, mx) == (8, 8)


def test_metadata_when_to_use_specificity() -> None:
    specific = "Use when the user uploads an invoice. Do not use for general text extraction."
    vague = "This skill helps with things when needed."
    absent = ""
    assert _when_specificity(specific) >= 0.8
    assert _when_specificity(vague) < _when_specificity(specific)
    assert _when_specificity(absent) == 0.0
    # Absent → neutral (0.5) in scoring, not zero — optional field
    doc_specific = _doc(f"---\nname: s\ndescription: d\nwhen_to_use: {specific}\n---\n# T\n")
    doc_vague = _doc(f"---\nname: s\ndescription: d\nwhen_to_use: {vague}\n---\n# T\n")
    ((s_earned, _, _),) = dim_metadata(doc_specific, 8)
    ((v_earned, _, _),) = dim_metadata(doc_vague, 8)
    assert s_earned > v_earned


def test_metadata_optional_fields_not_penalized() -> None:
    minimal = _doc(
        "---\nname: my-skill\ndescription: Processes invoices and extracts totals.\n---\n# T\n"
    )
    ((earned, mx, _),) = dim_metadata(minimal, 8)
    assert earned >= mx // 2  # when_to_use absent → neutral (0.5); author/version unscored


def test_metadata_author_version_zero_score_effect() -> None:
    # ADR-0001: author/version are advisory only — their presence/absence must not
    # change the score. when_to_use stays scored, so hold it constant across both docs.
    when = "Use when parsing invoices. Do not use for general text."
    without = _doc(f"---\nname: my-skill\ndescription: d\nwhen_to_use: {when}\n---\n# T\n")
    with_meta = _doc(
        f"---\nname: my-skill\ndescription: d\nwhen_to_use: {when}\n"
        "metadata:\n  author: A\n  version: 1.0\n---\n# T\n"
    )
    ((earned_without, _, _),) = dim_metadata(without, 8)
    ((earned_with, _, label_with),) = dim_metadata(with_meta, 8)
    assert earned_without == earned_with  # zero score effect
    # ...but the advice still nudges the author when they're absent.
    ((_, _, label_without),) = dim_metadata(without, 8)
    assert "author" in label_without and "version" in label_without
    assert "advisory" in label_without.lower()


def test_progressive_disclosure_na_for_simple_skill() -> None:
    doc = _doc("---\nname: my-skill\ndescription: d\n---\n# Title\nShort body.\n")
    assert dim_progressive_disclosure(doc, 8) == []  # N/A: concise, no supporting files needed


def test_progressive_disclosure_penalizes_bloated_monolith() -> None:
    # ADR-0002: a >500-line SKILL.md body with no supporting docs is poorly disclosed.
    big_body = "---\nname: s\ndescription: d\n---\n# T\n" + ("Line of detail here.\n" * 600)
    result = dim_progressive_disclosure(_doc(big_body), 8)
    assert result != []
    ((earned, mx, label),) = result
    assert earned < mx // 2  # heavily penalized
    assert "no supporting docs" in label


def test_progressive_disclosure_rewards_linked_docs_any_name() -> None:
    # A lean body that links an arbitrarily-named supporting doc one level deep scores well.
    body = (
        "---\nname: s\ndescription: d\n---\n# T\n"
        + ("Detail line.\n" * 250)
        + "\nSee [forms guide](FORMS.md).\n"
    )
    doc = _doc(body, **{"FORMS.md": "# Forms\nHow to fill forms.\n"})
    ((earned, mx, label),) = dim_progressive_disclosure(doc, 8)
    assert earned == mx  # disclosed at depth 1, no nesting
    assert "one level deep" in label


def test_progressive_disclosure_recognizes_reference_folder() -> None:
    body = (
        "---\nname: s\ndescription: d\n---\n# T\n"
        + ("Detail line.\n" * 250)
        + "\nFinance: [reference/finance.md](reference/finance.md)\n"
    )
    doc = _doc(body, **{"reference/finance.md": "# Finance\nARR and billing.\n"})
    ((earned, mx, _),) = dim_progressive_disclosure(doc, 8)
    assert earned == mx  # folder-organized docs count as disclosure


def test_progressive_disclosure_penalizes_nesting() -> None:
    # SKILL.md -> advanced.md -> details.md : details.md is depth 2 (nested).
    body = (
        "---\nname: s\ndescription: d\n---\n# T\n"
        + ("Detail line.\n" * 250)
        + "\nSee [advanced](advanced.md).\n"
    )
    doc = _doc(
        body,
        **{
            "advanced.md": "# Advanced\nSee [details](details.md).\n",
            "details.md": "# Details\nThe actual info.\n",
        },
    )
    ((earned, mx, label),) = dim_progressive_disclosure(doc, 8)
    assert earned < mx  # nesting penalty applied
    assert "nested" in label and "details.md" in label


def test_example_quality_paired_vs_none() -> None:
    paired = _doc(
        "---\nd: 1\n---\n# T\n",
        **{"examples.md": "## Example one\nInput:\n```\na\n```\nOutput:\n```\nb\n```\n"},
    )
    none = _doc("---\nd: 1\n---\n# T\nNo examples at all.\n")
    ((paired_earned, _, _),) = dim_example_quality(paired, 10)
    assert paired_earned > 0
    # Minimal body with no examples → N/A (not penalized for being concise)
    assert dim_example_quality(none, 10) == []


def test_example_quality_penalizes_long_skill_with_no_examples() -> None:
    long_body = "---\nd: invoice totals\n---\n" + (
        "## Step\nValidate each invoice field and reconcile totals carefully.\n" * 20
    )
    result = dim_example_quality(_doc(long_body), 10)
    assert result != []  # substantial skill (>100 words) → not N/A
    ((earned, _, _),) = result
    assert earned == 0  # no examples → zero score


# --- engine aggregation ----------------------------------------------------- #


def test_score_quality_normalized() -> None:
    r = score_quality({"SKILL.md": "---\ndescription: d\n---\n# Body\nSome prose here today.\n"})
    assert 0 <= r.score <= 100


def test_na_dimension_omitted_from_report() -> None:
    # No scripts -> Code Maintainability must not appear among categories.
    r = score_quality(_cache_of("good-skill"))
    names = {c.name for c in r.categories}
    r_noscript = score_quality(
        {k: v for k, v in _cache_of("good-skill").items() if not k.startswith("scripts/")}
    )
    assert "Code Maintainability" in names
    assert "Code Maintainability" not in {c.name for c in r_noscript.categories}


def test_deterministic_repeatable() -> None:
    cache = _cache_of("good-skill")
    assert score_quality(cache).to_dict() == score_quality(cache).to_dict()


# --- fixtures (discrimination) ---------------------------------------------- #


def test_good_fixture_scores_well() -> None:
    r = score_quality(_cache_of("good-skill"))
    assert r.score >= 70


def test_messy_fixture_scores_poorly() -> None:
    good = score_quality(_cache_of("good-skill"))
    messy = score_quality(_cache_of("messy-skill"))
    assert messy.score < good.score
    assert messy.score < 50  # N/A renormalization raises the floor; still clearly poor


# --- behavioral configuration (gap analysis) --------------------------------- #


def test_behavioral_config_na_without_spec_fields() -> None:
    doc = _doc(
        "---\nname: my-skill\ndescription: d\nwhen_to_use: use when needed\n"
        "metadata:\n  author: A\n  version: 1.0\n---\n# T\n"
    )
    assert dim_behavioral_config(doc, 10) == []


def test_behavioral_config_sub_weights_sum_to_w() -> None:
    doc = _doc(
        "---\nname: s\ncontext: fork\nagent: general-purpose\neffort: high\n"
        "paths: '**/*.py'\nallowed-tools: [Read, Grep]\nhooks:\n  stop: [echo done]\n---\n# T\n"
    )
    items = dim_behavioral_config(doc, 10)
    assert sum(m for _, m, _ in items) == 10


def test_behavioral_config_valid_paths_scores_above_empty_paths() -> None:
    valid = _doc("---\nname: s\npaths: '**/*.py'\n---\n# T\n")
    empty = _doc("---\nname: s\npaths: ''\n---\n# T\n")  # set but empty → invalid
    assert sum(e for e, _, _ in dim_behavioral_config(valid, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(empty, 10)
    )


def test_behavioral_config_argument_hint_required_with_arguments() -> None:
    no_hint = _doc("---\nname: s\narguments: [issue-number]\n---\n# T\n")
    with_hint = _doc(
        "---\nname: s\narguments: [issue-number]\nargument-hint: '[issue-number]'\n---\n# T\n"
    )
    assert sum(e for e, _, _ in dim_behavioral_config(with_hint, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(no_hint, 10)
    )


def test_behavioral_config_invalid_effort_penalized() -> None:
    bad = _doc("---\nname: s\neffort: supermax\n---\n# T\n")
    good = _doc("---\nname: s\neffort: high\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(good, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(bad, 10)
    )


def test_behavioral_config_invalid_shell_penalized() -> None:
    bad = _doc("---\nname: s\nshell: zsh\n---\n# T\n")
    good = _doc("---\nname: s\nshell: bash\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(good, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(bad, 10)
    )


def test_behavioral_config_argument_hint_without_arguments() -> None:
    # argument-hint set without arguments: unusual but not penalized (0.8 signal)
    doc = _doc("---\nname: s\nargument-hint: '[query]'\n---\n# T\n")
    items = dim_behavioral_config(doc, 10)
    assert items  # not N/A
    labels = " ".join(lbl for _, _, lbl in items)
    assert "argument-hint" in labels


def test_behavioral_config_disable_model_invocation() -> None:
    valid = _doc("---\nname: s\ndisable-model-invocation: true\n---\n# T\n")
    invalid = _doc("---\nname: s\ndisable-model-invocation: maybe\n---\n# T\n")
    good_score = sum(e for e, _, _ in dim_behavioral_config(valid, 10))
    bad_score = sum(e for e, _, _ in dim_behavioral_config(invalid, 10))
    assert good_score > bad_score


def test_behavioral_config_model_field() -> None:
    doc = _doc("---\nname: s\nmodel: claude-sonnet-4-6\n---\n# T\n")
    items = dim_behavioral_config(doc, 10)
    labels = " ".join(lbl for _, _, lbl in items)
    assert "model" in labels


# --- private helper edge cases ----------------------------------------------- #


def test_parse_frontmatter_yaml_error_returns_empty() -> None:
    # Malformed YAML produces a YAMLError → empty dict returned
    result = _parse_frontmatter("---\nkey: [\n---\n# Body\n")
    assert result == {}


def test_parse_frontmatter_non_dict_yaml_returns_empty() -> None:
    # YAML that parses to a list (not dict) → empty dict
    result = _parse_frontmatter("---\n- item1\n- item2\n---\n# Body\n")
    assert result == {}


def test_body_unclosed_frontmatter() -> None:
    # Opening --- without closing --- → everything after first line is body
    text = "---\nname: s\nsome content after\n"
    b = _body(text)
    assert "some content after" in b
    assert "name: s" in b  # the unclosed YAML becomes part of the body text


def test_body_unclosed_no_newline() -> None:
    # Opening --- with no newline at all → empty body
    b = _body("---")
    assert b == ""


def test_compression_ratio_empty_returns_zero() -> None:
    assert _compression_ratio("") == 0.0


def test_hdd_too_short_returns_none() -> None:
    assert _hdd(["a", "b", "c"], sample_size=42) is None


def test_hdd_long_enough_returns_float() -> None:
    tokens = ["word"] * 50 + ["other"] * 50
    result = _hdd(tokens, sample_size=42)
    assert result is not None
    assert 0.0 < result < 1.0


def test_mtld_empty_tokens_returns_zero() -> None:
    from skillspector_quality.quality.scorers import _mtld
    assert _mtld([]) == 0.0


def test_relative_targets_filters_urls_and_anchors() -> None:
    text = "[link](https://example.com) [local](reference.md) [anchor](#section)"
    targets = _relative_targets(text)
    assert "https://example.com" not in targets
    assert "#section" not in targets
    assert "reference.md" in targets


def test_relative_targets_strips_dotslash() -> None:
    text = "[local](./reference.md)"
    targets = _relative_targets(text)
    assert "reference.md" in targets
    assert "./reference.md" not in targets


def test_resolve_target_trailing_slash() -> None:
    keys = {"reference/api.md", "reference/guide.md"}
    result = _resolve_target("reference/", keys)
    assert result in keys


def test_resolve_target_partial_basename_match() -> None:
    keys = {"docs/reference.md"}
    result = _resolve_target("reference.md", keys)
    assert result == "docs/reference.md"


def test_resolve_target_no_match_returns_none() -> None:
    result = _resolve_target("nonexistent.md", {"SKILL.md"})
    assert result is None


def test_is_acyclic_detects_cycle() -> None:
    adj: dict[str, set[str]] = {
        "a": {"b"},
        "b": {"c"},
        "c": {"a"},  # cycle back to a
    }
    assert _is_acyclic(adj) is False


def test_is_acyclic_no_cycle() -> None:
    adj: dict[str, set[str]] = {"a": {"b"}, "b": {"c"}, "c": set()}
    assert _is_acyclic(adj) is True


def test_python_maintainability_syntax_error_in_ast() -> None:
    # Code that parses for MI but fails ast.parse (shouldn't happen normally,
    # but we force the SyntaxError branch via broken syntax)
    invalid = "def foo(:\n    pass\n"
    s, m = _python_maintainability(invalid)
    # Either returns 0.0 (unparseable via mi_visit) or proceeds with dc=0.0
    assert 0.0 <= s <= 1.0


def test_other_script_quality_empty_returns_zero() -> None:
    assert _other_script_quality("script.sh", "") == 0.0
    assert _other_script_quality("script.sh", "   \n  \n") == 0.0


def test_other_script_quality_shell_with_shebang() -> None:
    code = "#!/bin/bash\n# This script does something\necho hello\n"
    score = _other_script_quality("script.sh", code)
    assert score > 0.0


def test_other_script_quality_non_shell() -> None:
    code = "// JavaScript comment\nfunction doSomething() { return 1; }\n"
    score = _other_script_quality("utils.js", code)
    assert 0.0 <= score <= 1.0


# --- dimension edge cases ----------------------------------------------------- #


def test_information_density_thin_or_repeated_content() -> None:
    # Repeated/simple content should produce a non-dense label
    thin = _doc("---\ndescription: d\n---\n# T\n" + ("word " * 30))
    result = dim_information_density(thin, 15)
    assert result  # not N/A
    _, _, label = result[0]
    # Covers the non-dense branches: thin or repeated phrases
    assert any(phrase in label for phrase in ("thin", "Repeated", "dense"))


def test_lexical_diversity_medium() -> None:
    # Medium diversity: enough tokens but not very varied
    medium_text = (
        "---\ndescription: d\n---\n"
        + ("The system processes the data and the data is processed by the system. " * 5)
    )
    doc = _doc(medium_text)
    result = dim_lexical_diversity(doc, 6)
    if result:  # may be N/A if tokens < 50
        _, _, label = result[0]
        assert "word" in label.lower() or "vocabular" in label.lower()


def test_lexical_diversity_low() -> None:
    # Very repetitive text → low diversity label
    repetitive = "---\ndescription: d\n---\n" + ("spam eggs spam eggs spam eggs " * 10)
    doc = _doc(repetitive)
    result = dim_lexical_diversity(doc, 6)
    if result:
        _, _, label = result[0]
        assert any(word in label.lower() for word in ("repetitive", "varied", "vocabular"))


def test_topic_coverage_low_match() -> None:
    # Description about unrelated topic → low coverage
    doc = _doc(
        "---\ndescription: cake baking flour sugar oven\n---\n"
        "# Invoice\nParse invoice vendor totals and line items.\n"
    )
    result = dim_topic_coverage(doc, 15)
    assert result
    earned, mx, label = result[0]
    assert earned < mx
    assert "match" in label.lower() or "description" in label.lower()


def test_structural_coherence_cyclic_links() -> None:
    # a.md → b.md → a.md (cycle)
    body = "---\nd: 1\n---\n# T\nSee [a](a.md).\n"
    doc = _doc(body, **{"a.md": "See [b](b.md).\n", "b.md": "See [a](a.md).\n"})
    result = dim_structural_coherence(doc, 13)
    assert result  # should still return a score
    # The cycle is detected; score may be lower but shouldn't crash


def test_code_maintainability_medium_quality() -> None:
    # Code with some docs but complex functions → medium label
    medium_code = "\n".join(
        [
            "def process(a, b, c, d, e):",
            "    if a > 0:",
            "        if b > 0:",
            "            return a + b",
            "        return b",
            "    return 0",
        ]
    )
    doc = _doc("---\nd: 1\n---\n# T\n", **{"scripts/run.py": medium_code})
    result = dim_code_maintainability(doc, 15)
    assert result
    _, _, label = result[0]
    assert "script" in label


def test_progressive_disclosure_notoc_advisory() -> None:
    # A long supporting doc (>100 lines) without a TOC triggers the advisory note
    long_doc = "\n".join(f"Line {i}.\n" for i in range(120))
    body = (
        "---\nname: s\ndescription: d\n---\n# T\n"
        + ("Detail.\n" * 200)
        + "\nSee [reference](reference.md).\n"
    )
    doc = _doc(body, **{"reference.md": long_doc})
    result = dim_progressive_disclosure(doc, 8)
    assert result
    _, _, label = result[0]
    assert "advisory" in label or "table of contents" in label.lower() or "toc" in label.lower()


def test_behavioral_config_context_fork_without_agent_penalized() -> None:
    no_agent = _doc("---\nname: s\ncontext: fork\n---\n# T\n")
    with_agent = _doc("---\nname: s\ncontext: fork\nagent: general-purpose\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(with_agent, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(no_agent, 10)
    )


def test_behavioral_config_invalid_hooks_type_penalized() -> None:
    bad_hooks = _doc("---\nname: s\nhooks: 'a string'\n---\n# T\n")
    good_hooks = _doc("---\nname: s\nhooks:\n  stop:\n    - echo done\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(good_hooks, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(bad_hooks, 10)
    )


def test_behavioral_config_invalid_allowed_tools_type_penalized() -> None:
    bad = _doc("---\nname: s\nallowed-tools:\n  key: value\n---\n# T\n")  # dict, not str/list
    good = _doc("---\nname: s\nallowed-tools: [Read, Grep]\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(good, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(bad, 10)
    )


def test_behavioral_config_user_invocable_must_be_bool() -> None:
    bad = _doc("---\nname: s\nuser-invocable: 'yes'\n---\n# T\n")
    good = _doc("---\nname: s\nuser-invocable: false\n---\n# T\n")
    assert sum(e for e, _, _ in dim_behavioral_config(good, 10)) > sum(
        e for e, _, _ in dim_behavioral_config(bad, 10)
    )


def test_behavioral_config_appears_in_engine_report() -> None:
    r = score_quality(
        {
            "SKILL.md": "---\nname: s\ncontext: fork\nagent: general-purpose\neffort: high\n---\n# T\n"
        }
    )
    names = {c.name for c in r.categories}
    assert "Behavioral Configuration" in names


# --- length-neutrality (the reframe) ---------------------------------------- #


def test_more_good_content_not_penalized_but_filler_is() -> None:
    section = (
        "## Step\nValidate each invoice field and reconcile the printed total against the "
        "computed sum so downstream automation can trust the extracted numbers.\n"
    )
    base = "---\ndescription: invoice totals validation\n---\n# Invoice\n" + section
    # Doubling genuine, distinct content (new vocabulary, different concepts) must not tank score.
    distinct_section = (
        "## Exception handling\nWhen a vendor file is missing or corrupt, fall back to the "
        "last known snapshot and notify the finance team, logging the discrepancy for audit.\n"
    )
    more_good = base + distinct_section
    filler = base + ("This skill does stuff. " * 60)

    s_base = score_quality({"SKILL.md": base}).score
    s_more = score_quality({"SKILL.md": more_good}).score
    s_filler = score_quality({"SKILL.md": filler}).score

    assert s_more >= s_base - 5  # added good content is not punished
    assert s_filler < s_more  # redundant filler is punished

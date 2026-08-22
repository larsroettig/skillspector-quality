"""Exact-value correctness tests for the math-heavy helpers in ``quality/scorers.py``.

Unlike ``test_scorers.py``/``test_scorers_extra.py`` (which mostly assert relational
properties such as "A > B" or "does not crash"), these tests hand-compute the expected
numeric output from the *documented* formula/algorithm and assert exact (or near-exact,
floating point) equality against the implementation. They also assert the end-to-end
score-aggregation formula from the README (``round(100 * sum(earned) / sum(max))`` with
N/A-dimension renormalization) and add property-based invariants with ``hypothesis``.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from skillspector_quality import quality as quality_pkg
from skillspector_quality.config import ScoringConfig
from skillspector_quality.quality import score_quality
from skillspector_quality.quality.scorers import (
    _build_idf,
    _compression_ratio,
    _cosine,
    _count_syllables,
    _hdd,
    _mtld,
    _mtld_one_pass,
    _ngram_dup,
    _python_maintainability,
    _readability_grades,
    _tf,
    _tfidf_vec,
    clamp01,
)

# --------------------------------------------------------------------------- #
# _count_syllables: cheap vowel-group estimator (see docstring), traced by hand
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("cat", 1),  # one vowel group "a"
        ("apple", 1),  # groups "a","e" -> 2, ends in "e" and n>1 -> 1
        ("table", 1),  # groups "a","e" -> 2, ends in "e" and n>1 -> 1
        ("queue", 1),  # single contiguous vowel run "ueue" -> 1, no decrement (n not >1)
        ("banana", 3),  # groups "a","a","a" -> 3, does not end in "e"
        ("every", 3),  # groups "e","e","y" -> 3 (y counts as a vowel)
        ("syllable", 2),  # groups "y","a","e" -> 3, ends in "e" and n>1 -> 2
        ("strengths", 1),  # single vowel group "e" -> 1
        ("b", 1),  # no vowel groups -> floor of 1 (max(1, 0))
    ],
)
def test_count_syllables_matches_hand_trace(word: str, expected: int) -> None:
    assert _count_syllables(word) == expected


# --------------------------------------------------------------------------- #
# _readability_grades: ensemble formula, cross-checked against manual recompute
# --------------------------------------------------------------------------- #


def test_readability_grades_matches_manual_formula() -> None:
    import re

    text = (
        "The quick brown fox jumps over the lazy dog. " * 3
        + "This sentence introduces additional complexity using multisyllabic vocabulary. " * 2
    )
    grades, word_count = _readability_grades(text)

    words = re.findall(r"[A-Za-z]+", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    w = len(words)
    s = max(1, len(sentences))
    syll = [_count_syllables(x) for x in words]
    total_syll = sum(syll)
    complex_words = sum(1 for c in syll if c >= 3)
    letters = sum(len(x) for x in words)
    wps = w / s
    spw = total_syll / w

    expected_fk = 0.39 * wps + 11.8 * spw - 15.59
    expected_fog = 0.4 * (wps + 100 * complex_words / w)
    expected_smog = 1.0430 * math.sqrt(complex_words * (30 / s)) + 3.1291
    expected_ari = 4.71 * (letters / w) + 0.5 * wps - 21.43
    expected_cl = 0.0588 * (letters / w * 100) - 0.296 * (s / w * 100) - 15.8

    assert word_count == w
    fk, fog, smog, ari, cl = grades
    assert fk == pytest.approx(expected_fk)
    assert fog == pytest.approx(expected_fog)
    assert smog == pytest.approx(expected_smog)
    assert ari == pytest.approx(expected_ari)
    assert cl == pytest.approx(expected_cl)


def test_readability_grades_below_word_threshold_is_empty() -> None:
    grades, words = _readability_grades("Too short.")
    assert grades == []
    assert words < 30


# --------------------------------------------------------------------------- #
# _mtld / _mtld_one_pass: hand-traced factor counting (Malvern/Richardson MTLD)
# --------------------------------------------------------------------------- #


def test_mtld_one_pass_hand_traced_factor_count() -> None:
    # threshold=0.5: TTR drops to exactly 0.5 every 2 tokens of a new type pair,
    # producing 3 complete factors and no partial factor.
    tokens = ["a", "a", "b", "b", "c", "c"]
    assert _mtld_one_pass(tokens, 0.5) == pytest.approx(6 / 3)


def test_mtld_one_pass_zero_factors_falls_back_to_token_count() -> None:
    # threshold=0.72 (default): "a","b","c" never drops the running TTR to <=0.72
    # (TTR stays 1.0 the whole way), so there are zero complete factors and the
    # trailing partial-factor contribution (1 - ttr) / (1 - threshold) is also 0
    # since ttr=1.0. With factors==0, the implementation falls back to len(tokens).
    tokens = ["a", "b", "c"]
    ttr = 1.0  # 3 unique / 3 tokens
    partial_factor = (1 - ttr) / (1 - 0.72)
    assert partial_factor == 0.0
    expected = float(len(tokens))
    assert _mtld_one_pass(tokens, 0.72) == pytest.approx(expected)


def test_mtld_one_pass_genuine_partial_factor() -> None:
    # threshold=0.72: no complete factor is ever triggered (TTR never drops to <=0.72
    # mid-stream), but the trailing TTR (3 types / 4 tokens = 0.75) yields a genuine
    # non-zero partial factor: factors = (1 - 0.75) / (1 - 0.72).
    tokens = ["a", "b", "c", "c"]
    ttr = 3 / 4
    partial_factor = (1 - ttr) / (1 - 0.72)
    assert partial_factor != 0.0
    expected = len(tokens) / partial_factor
    assert _mtld_one_pass(tokens, 0.72) == pytest.approx(expected)


def test_mtld_is_bidirectional_mean_of_one_pass() -> None:
    tokens = ["a", "a", "b", "b", "c", "d", "a", "b"]
    fwd = _mtld_one_pass(tokens, 0.72)
    bwd = _mtld_one_pass(list(reversed(tokens)), 0.72)
    assert _mtld(tokens, 0.72) == pytest.approx((fwd + bwd) / 2)


def test_mtld_all_unique_tokens_returns_length() -> None:
    # TTR never drops (always 1.0), so factors=0 -> _mtld_one_pass falls back to len(tokens).
    tokens = [str(i) for i in range(10)]
    assert _mtld_one_pass(tokens, 0.72) == 10.0


# --------------------------------------------------------------------------- #
# _hdd: HD-D per McCarthy & Jarvis, cross-checked against the hypergeometric formula
# --------------------------------------------------------------------------- #


def test_hdd_matches_hypergeometric_closed_form() -> None:
    tokens = ["a", "a", "b", "b", "c", "c"]  # n=6, each type count=2
    sample_size = 3
    result = _hdd(tokens, sample_size=sample_size)

    n = len(tokens)
    denom = math.comb(n, sample_size)
    expected = 0.0
    for cnt in (2, 2, 2):
        p_absent = math.comb(n - cnt, sample_size) / denom if n - cnt >= sample_size else 0.0
        expected += (1 - p_absent) * (1 / sample_size)

    assert result == pytest.approx(expected)
    assert expected == pytest.approx(0.8)


def test_hdd_uneven_frequencies_matches_hypergeometric() -> None:
    tokens = ["a"] * 4 + ["b"] * 2 + ["c"] * 1  # n=7
    sample_size = 4
    result = _hdd(tokens, sample_size=sample_size)

    n = len(tokens)
    denom = math.comb(n, sample_size)
    expected = 0.0
    for cnt in (4, 2, 1):
        p_absent = math.comb(n - cnt, sample_size) / denom if n - cnt >= sample_size else 0.0
        expected += (1 - p_absent) * (1 / sample_size)

    assert result == pytest.approx(expected)


def test_hdd_none_when_shorter_than_sample() -> None:
    assert _hdd(["a", "b", "c"], sample_size=42) is None


# --------------------------------------------------------------------------- #
# TF-IDF + cosine: hand-computed on a tiny 2-document corpus
# --------------------------------------------------------------------------- #


def test_tf_is_relative_frequency() -> None:
    terms = ["cat", "dog", "cat"]
    tf = _tf(terms)
    assert tf == {"cat": pytest.approx(2 / 3), "dog": pytest.approx(1 / 3)}


def test_build_idf_matches_smoothed_formula() -> None:
    doc_a = ["cat", "dog", "cat"]
    doc_b = ["cat", "bird"]
    idf = _build_idf([doc_a, doc_b])

    n = 2
    assert idf["cat"] == pytest.approx(math.log((1 + n) / (1 + 2)) + 1)  # df=2
    assert idf["dog"] == pytest.approx(math.log((1 + n) / (1 + 1)) + 1)  # df=1
    assert idf["bird"] == pytest.approx(math.log((1 + n) / (1 + 1)) + 1)  # df=1


def test_tfidf_and_cosine_hand_computed() -> None:
    doc_a = ["cat", "dog", "cat"]
    doc_b = ["cat", "bird"]
    idf = _build_idf([doc_a, doc_b])
    vec_a = _tfidf_vec(doc_a, idf)
    vec_b = _tfidf_vec(doc_b, idf)

    # Hand-computed raw (tf*idf) vectors, before L2 normalization:
    raw_a = {"cat": (2 / 3) * idf["cat"], "dog": (1 / 3) * idf["dog"]}
    raw_b = {"cat": (1 / 2) * idf["cat"], "bird": (1 / 2) * idf["bird"]}
    norm_a = math.sqrt(sum(v * v for v in raw_a.values()))
    norm_b = math.sqrt(sum(v * v for v in raw_b.values()))
    expected_vec_a = {k: v / norm_a for k, v in raw_a.items()}
    expected_vec_b = {k: v / norm_b for k, v in raw_b.items()}

    assert vec_a == pytest.approx(expected_vec_a)
    assert vec_b == pytest.approx(expected_vec_b)

    expected_cosine = sum(expected_vec_a.get(t, 0.0) * expected_vec_b.get(t, 0.0) for t in ("cat",))
    assert _cosine(vec_a, vec_b) == pytest.approx(expected_cosine)


def test_cosine_identical_vectors_is_one() -> None:
    idf = _build_idf([["a", "b", "a"], ["a", "c"]])
    vec = _tfidf_vec(["a", "b", "a"], idf)
    assert _cosine(vec, vec) == pytest.approx(1.0)


def test_cosine_empty_vector_is_zero() -> None:
    assert _cosine({}, {"a": 1.0}) == 0.0
    assert _cosine({"a": 1.0}, {}) == 0.0


# --------------------------------------------------------------------------- #
# _compression_ratio / _ngram_dup: analytically predictable edge cases
# --------------------------------------------------------------------------- #


def test_ngram_dup_fully_repeating_pattern() -> None:
    # tokens = ("a","b","c") repeated twice -> shingles of n=3: (a,b,c),(b,c,a),(c,a,b),(a,b,c)
    # total=4, unique=3 -> dup = 1 - 3/4 = 0.25
    tokens = ["a", "b", "c", "a", "b", "c"]
    assert _ngram_dup(tokens, n=3) == pytest.approx(0.25)


def test_ngram_dup_all_unique_is_zero() -> None:
    tokens = [str(i) for i in range(10)]
    assert _ngram_dup(tokens, n=3) == 0.0


def test_ngram_dup_too_short_returns_zero() -> None:
    assert _ngram_dup(["a", "b"], n=5) == 0.0


def test_compression_ratio_empty_is_zero() -> None:
    assert _compression_ratio("") == 0.0


def test_compression_ratio_highly_redundant_below_dense() -> None:
    redundant = "the same sentence repeats. " * 200
    dense = " ".join(f"unique{i}token{i}entry{i}" for i in range(200))
    assert _compression_ratio(redundant) < _compression_ratio(dense)


def test_compression_ratio_bounded_for_long_inputs() -> None:
    # zlib header/footer overhead makes the ratio exceed 1.0 for very short inputs, but
    # for long-enough text the compressed form is always no larger than the raw bytes.
    for text in ("a" * 1000, "abcdefghij" * 100):
        r = _compression_ratio(text)
        assert 0.0 < r <= 1.0


# --------------------------------------------------------------------------- #
# _python_maintainability: sub-metrics cross-checked against radon/ast directly
# --------------------------------------------------------------------------- #


def test_python_maintainability_matches_manual_recompute() -> None:
    radon_metrics = pytest.importorskip("radon.metrics")
    radon_complexity = pytest.importorskip("radon.complexity")
    import ast as ast_mod

    code = (
        '"""Module docstring."""\n\n\n'
        "def add(a, b):\n"
        '    """Add two numbers."""\n'
        "    # simple addition\n"
        "    return a + b\n\n\n"
        "def sub(a, b):\n"
        "    return a - b\n"
    )
    s, metrics = _python_maintainability(code)

    mi = radon_metrics.mi_visit(code, multi=True)
    mi_norm = clamp01(mi / 100)
    blocks = radon_complexity.cc_visit(code)
    avg_cc = sum(b.complexity for b in blocks) / len(blocks) if blocks else 1.0
    cc_norm = clamp01((15 - avg_cc) / 14)

    tree = ast_mod.parse(code)
    units = 1
    documented = 1 if ast_mod.get_docstring(tree) else 0
    for node in ast_mod.walk(tree):
        if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef, ast_mod.ClassDef)):
            units += 1
            if ast_mod.get_docstring(node):
                documented += 1
    dc = documented / units

    lines = code.splitlines()
    comment_lines = sum(
        1 for ln in lines if ln.lstrip().startswith("#") and not ln.lstrip().startswith("#!")
    )
    code_lines = sum(1 for ln in lines if ln.strip() and not ln.lstrip().startswith("#"))
    cd = comment_lines / code_lines if code_lines else 0.0
    cd_norm = clamp01(cd / 0.10)

    expected_s = 0.40 * mi_norm + 0.25 * cc_norm + 0.20 * dc + 0.15 * cd_norm

    assert s == pytest.approx(expected_s)
    assert metrics["mi"] == pytest.approx(round(mi, 1))
    assert metrics["avg_cc"] == pytest.approx(round(avg_cc, 1))
    assert metrics["docstring_cov"] == pytest.approx(round(dc, 2))
    assert metrics["comment_density"] == pytest.approx(round(cd, 2))


def test_python_maintainability_unparseable_returns_zero() -> None:
    pytest.importorskip("radon.metrics")
    s, metrics = _python_maintainability("def broken(:\n")
    assert s == 0.0
    assert metrics.get("error") == "unparseable"


# --------------------------------------------------------------------------- #
# End-to-end aggregation: final_score = round(100 * sum(earned) / sum(max))
# --------------------------------------------------------------------------- #


def test_score_quality_aggregation_matches_readme_formula(monkeypatch) -> None:
    def scorer_a(doc, config):
        return [(3, 8, "a")]

    def scorer_b(doc, config):
        return [(9, 15, "b1"), (1, 5, "b2")]

    def scorer_na(doc, config):
        return []  # N/A dimension: must not affect numerator or denominator

    monkeypatch.setattr(
        quality_pkg,
        "CATEGORY_SCORERS",
        [("A", scorer_a), ("B", scorer_b), ("NA", scorer_na)],
    )

    report = score_quality({"SKILL.md": "---\ndescription: d\n---\n# Body\ntext\n"})

    total_earned = 3 + 9 + 1
    total_max = 8 + 15 + 5
    expected_score = round(100 * total_earned / total_max)

    assert report.score == expected_score
    assert {c.name for c in report.categories} == {"A", "B"}
    assert sum(c.earned for c in report.categories) == total_earned
    assert sum(c.max for c in report.categories) == total_max


def test_score_quality_all_na_dimensions_scores_zero(monkeypatch) -> None:
    def scorer_na(doc, config):
        return []

    monkeypatch.setattr(quality_pkg, "CATEGORY_SCORERS", [("NA", scorer_na)])
    report = score_quality({"SKILL.md": "---\ndescription: d\n---\n# Body\n"})
    assert report.score == 0
    assert report.categories == []


def test_score_quality_disabled_dimension_renormalizes(monkeypatch) -> None:
    def scorer_a(doc, config):
        return [(5, 10, "a")]

    def scorer_b(doc, config):
        return [(1, 10, "b")]

    monkeypatch.setattr(quality_pkg, "CATEGORY_SCORERS", [("A", scorer_a), ("B", scorer_b)])

    full = score_quality({"SKILL.md": "x"}, config=ScoringConfig())
    assert full.score == round(100 * (5 + 1) / (10 + 10))

    only_a = score_quality(
        {"SKILL.md": "x"}, config=ScoringConfig.from_lists(disable=["B"], strict=[])
    )
    assert only_a.score == round(100 * 5 / 10)
    assert {c.name for c in only_a.categories} == {"A"}


# --------------------------------------------------------------------------- #
# Property-based invariants (hypothesis)
# --------------------------------------------------------------------------- #


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_clamp01_always_in_unit_interval(x: float) -> None:
    result = clamp01(x)
    assert 0.0 <= result <= 1.0


@given(st.lists(st.sampled_from("abcdefgh"), min_size=1, max_size=200))
def test_mtld_is_permutation_independent_of_being_finite(tokens: list[str]) -> None:
    result = _mtld(tokens)
    assert result >= 0.0
    assert math.isfinite(result)


@given(
    st.lists(st.sampled_from("abcdef"), min_size=50, max_size=200),
)
def test_hdd_is_probability_when_defined(tokens: list[str]) -> None:
    result = _hdd(tokens, sample_size=10)
    if result is not None:
        assert 0.0 <= result <= 1.0


@given(st.text(min_size=0, max_size=500))
def test_compression_ratio_in_valid_range(text: str) -> None:
    # Short/incompressible inputs can exceed 1.0 due to zlib's fixed header/footer
    # overhead; the ratio must still be finite and non-negative for any input.
    r = _compression_ratio(text)
    if text == "":
        assert r == 0.0
    else:
        assert r > 0.0
        assert math.isfinite(r)


@given(
    st.lists(st.sampled_from(["cat", "dog", "bird", "fish"]), min_size=1, max_size=30),
    st.lists(st.sampled_from(["cat", "dog", "bird", "fish"]), min_size=1, max_size=30),
)
def test_cosine_similarity_bounded_for_nonnegative_tfidf(
    terms_a: list[str], terms_b: list[str]
) -> None:
    idf = _build_idf([terms_a, terms_b])
    vec_a = _tfidf_vec(terms_a, idf)
    vec_b = _tfidf_vec(terms_b, idf)
    sim = _cosine(vec_a, vec_b)
    # TF-IDF weights here are non-negative, so cosine similarity is in [0, 1].
    assert -1e-9 <= sim <= 1.0 + 1e-9


@given(st.integers(min_value=0, max_value=100), st.integers(min_value=1, max_value=100))
def test_final_score_formula_bounded(earned: int, cap: int) -> None:
    earned = min(earned, cap)

    def scorer(doc, config):
        return [(earned, cap, "item")]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(quality_pkg, "CATEGORY_SCORERS", [("A", scorer)])
        report = score_quality({"SKILL.md": "x"})

    assert report.score == round(100 * earned / cap)
    assert 0 <= report.score <= 100

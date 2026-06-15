# Examples

Annotated scoring runs that show how the quality dimensions interact in practice.

## Example: well-documented skill (EXCELLENT tier)

A skill with complete frontmatter, specific trigger conditions, dense and varied prose, paired examples, and both `reference.md` and `examples.md` linked from the body.

Input:

```bash
python -m skillspector_quality scan tests/fixtures/good-skill --no-llm
```

Output:

```
┌─────────────────────────────────────────────────────┐
│  Skill: invoice-parsing          Quality Score: 83   │
└─────────────────────────────────────────────────────┘

 Dimension               Earned  Max   Label
 ─────────────────────── ──────  ───   ───────────────────────────────────────────
 Metadata & Discovery       7     8   All fields complete
 Information Density       14    15   Content is dense and non-repetitive
 Lexical Diversity          8     9   Vocabulary is rich and varied (412 words)
 Readability                9    10   Reading level: 11th grade
 Topic Coverage            14    15   Description aligns well with skill content
 Structural Coherence      13    13   Heading structure sound; all docs reachable
 Code Maintainability      13    15   3 script(s) — maintainable
 Example Quality            9    10   2 example(s) with clear input/output pairs
 Progressive Disclosure     5     5   Full doc structure: examples.md and reference.md linked
 Behavioral Config          N/A       No behavioral config fields present
```

The score of 83 (GOOD tier) reflects a well-documented skill. The Behavioral Configuration dimension is N/A because no spec-defined frontmatter fields were set — its weight of 10 redistributes to the remaining nine dimensions.

## Example: sparse skill (POOR tier)

A skill with minimal frontmatter, vague description, no supporting docs, and code that scores low on maintainability metrics.

Input:

```bash
python -m skillspector_quality scan tests/fixtures/messy-skill --no-llm
```

Output:

```
┌─────────────────────────────────────────────────────┐
│  Skill: messy-skill              Quality Score: 31   │
└─────────────────────────────────────────────────────┘

 Dimension               Earned  Max   Label
 ─────────────────────── ──────  ───   ───────────────────────────────────────────
 Metadata & Discovery       3     8   Required fields missing: description
 Information Density        6    15   Content is thin — add more concrete, specific detail
 Lexical Diversity          3     9   Vocabulary is repetitive (89 words)
 Readability                5    10   Writing is too simple (5th grade)
 Topic Coverage             4    15   Description doesn't match the skill body
 Structural Coherence       6    13   2 heading level skip(s); orphaned files detected
 Code Maintainability       4    15   1 script(s) — code is hard to maintain
 Example Quality            0    10   No examples found — add ## Example sections
 Progressive Disclosure     0     5   No supporting docs — add examples.md and reference.md
 Behavioral Config          N/A       No behavioral config fields present
```

The score of 31 (CRITICAL tier) identifies every actionable gap directly in the dimension breakdown.

## Example: CI gate usage

Using skillspector-quality as a PR gate that blocks merges below GOOD tier.

Input:

```yaml
# .github/workflows/skill-quality.yml
- name: Check skill quality
  run: |
    python -m skillspector_quality scan . --no-llm --min-score 70
```

Output:

```
Quality score 68 < minimum 70. Gate failed.
```

When the gate fails, the exit code is 1 and the full dimension breakdown is printed so the author knows exactly which dimensions to improve before resubmitting.

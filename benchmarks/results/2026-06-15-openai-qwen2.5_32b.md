# Benchmark Results — 2026-06-15

**Provider:** OpenAI-compatible (http://localhost:11434/v1)  
**Model:** `qwen2.5:32b`  
**Repeats:** 5 per cell  
**Temperature:** 0.3  
**Scenarios:** 5  
**Arms:** Baseline · LowQuality · HighQuality  

## Method

- **Baseline** — generic extraction prompt, no SKILL.md  
- **LowQuality** — SKILL.md with conversational body, no schema, no example  
- **HighQuality** — SKILL.md improved by skillspector-quality recommendations  

Two metrics per cell: `output_tokens` (measurement) + `schema_correct` (gate).  
Reported values: median output tokens across N repeats, correct count out of N.

## Results

| Scenario | Arm | Body score | Output tok (med) | Correct/5 |
|----------|-----|:----------:|:----------------:|:-------:|
| Customer Order Extraction | Baseline | — | 47 | 0/5 |
| Customer Order Extraction | LowQuality | 74 | 357 | 0/5 |
| Customer Order Extraction | HighQuality | 96 | 36 | 5/5 ✓ |
| Meeting Notes Summary | Baseline | — | 107 | 0/5 |
| Meeting Notes Summary | LowQuality | 63 | 274 | 0/5 |
| Meeting Notes Summary | HighQuality | 98 | 59 | 5/5 ✓ |
| Bug Report Triage | Baseline | — | 68 | 0/5 |
| Bug Report Triage | LowQuality | 72 | 645 | 0/5 |
| Bug Report Triage | HighQuality | 96 | 52 | 5/5 ✓ |
| Product Review Analysis | Baseline | — | 57 | 0/5 |
| Product Review Analysis | LowQuality | 83 | 316 | 0/5 |
| Product Review Analysis | HighQuality | 98 | 51 | 5/5 ✓ |
| Incident Report Parser | Baseline | — | 96 | 0/5 |
| Incident Report Parser | LowQuality | 89 | 425 | 0/5 |
| Incident Report Parser | HighQuality | 96 | 42 | 5/5 ✓ |

## Aggregate

| Arm | Avg body score | Output tok (med) | Correct rate |
|-----|:--------------:|:----------------:|:------------:|
| Baseline | — | 68 | 0% |
| LowQuality | ~76 | 357 | 0% |
| HighQuality | ~97 | 51 | 100% |

## Per-run detail

| Scenario | Arm | Run | Output tok | Correct | Reason |
|----------|-----|:---:|:----------:|:-------:|--------|
| Customer Order Extraction | Baseline | 1 | 47 | ✗ | missing keys: ['items'] |
| Customer Order Extraction | Baseline | 2 | 40 | ✗ | missing keys: ['items'] |
| Customer Order Extraction | Baseline | 3 | 47 | ✗ | missing keys: ['items'] |
| Customer Order Extraction | Baseline | 4 | 47 | ✗ | missing keys: ['items'] |
| Customer Order Extraction | Baseline | 5 | 47 | ✗ | missing keys: ['items'] |
| Customer Order Extraction | LowQuality | 1 | 353 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Customer Order Extraction | LowQuality | 2 | 342 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Customer Order Extraction | LowQuality | 3 | 357 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Customer Order Extraction | LowQuality | 4 | 399 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Customer Order Extraction | LowQuality | 5 | 393 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Customer Order Extraction | HighQuality | 1 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 2 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 3 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 4 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 5 | 36 | ✓ |  |
| Meeting Notes Summary | Baseline | 1 | 107 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 2 | 107 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 3 | 107 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 4 | 107 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 5 | 89 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | LowQuality | 1 | 240 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 2 | 277 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 3 | 260 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 4 | 274 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 5 | 297 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | HighQuality | 1 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 2 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 3 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 4 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 5 | 59 | ✓ |  |
| Bug Report Triage | Baseline | 1 | 68 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 2 | 62 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 3 | 75 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 4 | 75 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 5 | 66 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | LowQuality | 1 | 648 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 2 | 641 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 3 | 678 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 4 | 645 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 5 | 639 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | HighQuality | 1 | 52 | ✓ |  |
| Bug Report Triage | HighQuality | 2 | 52 | ✓ |  |
| Bug Report Triage | HighQuality | 3 | 52 | ✓ |  |
| Bug Report Triage | HighQuality | 4 | 52 | ✓ |  |
| Bug Report Triage | HighQuality | 5 | 50 | ✓ |  |
| Product Review Analysis | Baseline | 1 | 57 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 2 | 57 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 3 | 57 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 4 | 57 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 5 | 57 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | LowQuality | 1 | 316 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 2 | 313 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 3 | 329 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 4 | 273 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 5 | 327 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | HighQuality | 1 | 51 | ✓ |  |
| Product Review Analysis | HighQuality | 2 | 51 | ✓ |  |
| Product Review Analysis | HighQuality | 3 | 52 | ✓ |  |
| Product Review Analysis | HighQuality | 4 | 51 | ✓ |  |
| Product Review Analysis | HighQuality | 5 | 49 | ✓ |  |
| Incident Report Parser | Baseline | 1 | 96 | ✗ | missing keys: ['duration_minutes', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 2 | 96 | ✗ | missing keys: ['duration_minutes', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 3 | 89 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 4 | 89 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 5 | 96 | ✗ | missing keys: ['duration_minutes', 'users_affected', 'resolved'] |
| Incident Report Parser | LowQuality | 1 | 431 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 2 | 370 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 3 | 425 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 4 | 370 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 5 | 425 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | HighQuality | 1 | 42 | ✓ |  |
| Incident Report Parser | HighQuality | 2 | 42 | ✓ |  |
| Incident Report Parser | HighQuality | 3 | 42 | ✓ |  |
| Incident Report Parser | HighQuality | 4 | 42 | ✓ |  |
| Incident Report Parser | HighQuality | 5 | 42 | ✓ |  |

*Generated by [skillspector-quality](https://github.com) benchmark runner on 2026-06-15.*

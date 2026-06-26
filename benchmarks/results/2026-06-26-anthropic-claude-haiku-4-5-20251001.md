# Benchmark Results — 2026-06-26

**Provider:** Anthropic  
**Model:** `claude-haiku-4-5-20251001`  
**Repeats:** 10 per cell  
**Temperature:** 0.3  
**Scenarios:** 8  
**Arms:** Baseline · LowQuality · HighQuality  

## Method

- **Baseline** — generic extraction prompt, no SKILL.md  
- **LowQuality** — SKILL.md with conversational body, no schema, no example  
- **HighQuality** — SKILL.md improved by skillspector-quality recommendations  

Two metrics per cell: `output_tokens` (measurement) + `schema_correct` (gate).  
Reported values: median output tokens across N repeats, correct count out of N.

## Results

| Scenario | Arm | Body score | Output tok (med) | Correct/10 |
|----------|-----|:----------:|:----------------:|:-------:|
| Customer Order Extraction | Baseline | — | 66 | 1/10 |
| Customer Order Extraction | LowQuality | 72 | 429 | 0/10 |
| Customer Order Extraction | HighQuality | 96 | 36 | 10/10 ✓ |
| Meeting Notes Summary | Baseline | — | 117 | 0/10 |
| Meeting Notes Summary | LowQuality | 65 | 400 | 0/10 |
| Meeting Notes Summary | HighQuality | 98 | 64 | 10/10 ✓ |
| Bug Report Triage | Baseline | — | 174 | 0/10 |
| Bug Report Triage | LowQuality | 72 | 697 | 0/10 |
| Bug Report Triage | HighQuality | 96 | 47 | 10/10 ✓ |
| Product Review Analysis | Baseline | — | 117 | 0/10 |
| Product Review Analysis | LowQuality | 84 | 347 | 0/10 |
| Product Review Analysis | HighQuality | 98 | 47 | 10/10 ✓ |
| Incident Report Parser | Baseline | — | 118 | 0/10 |
| Incident Report Parser | LowQuality | 89 | 372 | 0/10 |
| Incident Report Parser | HighQuality | 96 | 44 | 10/10 ✓ |
| Support Email Classification | Baseline | — | 85 | 0/10 |
| Support Email Classification | LowQuality | 82 | 292 | 0/10 |
| Support Email Classification | HighQuality | 96 | 38 | 10/10 ✓ |
| Job Posting Parser | Baseline | — | 113 | 0/10 |
| Job Posting Parser | LowQuality | 84 | 360 | 0/10 |
| Job Posting Parser | HighQuality | 96 | 64 | 10/10 ✓ |
| Ambiguous Ticket Routing | Baseline | — | 136 | 0/10 |
| Ambiguous Ticket Routing | LowQuality | 86 | 377 | 0/10 |
| Ambiguous Ticket Routing | HighQuality | 98 | 48 | 10/10 ✓ |

## Aggregate

| Arm | Avg body score | Output tok (med) | Correct rate |
|-----|:--------------:|:----------------:|:------------:|
| Baseline | — | 117 | 1% |
| LowQuality | ~79 | 376 | 0% |
| HighQuality | ~97 | 47 | 100% |

## Per-run detail

| Scenario | Arm | Run | Output tok | Correct | Reason |
|----------|-----|:---:|:----------:|:-------:|--------|
| Customer Order Extraction | Baseline | 1 | 64 | ✓ |  |
| Customer Order Extraction | Baseline | 2 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 3 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 4 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 5 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 6 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 7 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 8 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 9 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 10 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 1 | 466 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 2 | 524 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 3 | 494 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 4 | 406 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 5 | 454 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 6 | 413 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 7 | 418 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 8 | 427 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 9 | 427 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 10 | 431 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | HighQuality | 1 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 2 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 3 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 4 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 5 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 6 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 7 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 8 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 9 | 36 | ✓ |  |
| Customer Order Extraction | HighQuality | 10 | 36 | ✓ |  |
| Meeting Notes Summary | Baseline | 1 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 2 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 3 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 4 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 5 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 6 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 7 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 8 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 9 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 10 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | LowQuality | 1 | 397 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 2 | 402 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 3 | 399 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 4 | 394 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 5 | 422 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 6 | 371 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 7 | 413 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 8 | 400 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 9 | 422 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 10 | 364 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | HighQuality | 1 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 2 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 3 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 4 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 5 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 6 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 7 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 8 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 9 | 64 | ✓ |  |
| Meeting Notes Summary | HighQuality | 10 | 64 | ✓ |  |
| Bug Report Triage | Baseline | 1 | 157 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 2 | 175 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 3 | 129 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 4 | 181 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 5 | 176 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 6 | 164 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 7 | 173 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 8 | 159 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 9 | 183 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 10 | 175 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | LowQuality | 1 | 760 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 2 | 723 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 3 | 631 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 4 | 694 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 5 | 619 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 6 | 762 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 7 | 755 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 8 | 690 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 9 | 700 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 10 | 686 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | HighQuality | 1 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 2 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 3 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 4 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 5 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 6 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 7 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 8 | 50 | ✓ |  |
| Bug Report Triage | HighQuality | 9 | 50 | ✓ |  |
| Bug Report Triage | HighQuality | 10 | 50 | ✓ |  |
| Product Review Analysis | Baseline | 1 | 115 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 2 | 117 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 3 | 118 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 4 | 117 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 5 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 6 | 118 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 7 | 117 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 8 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 9 | 118 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 10 | 116 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | LowQuality | 1 | 344 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 2 | 323 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 3 | 349 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 4 | 337 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 5 | 372 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 6 | 362 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 7 | 339 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 8 | 376 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 9 | 348 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 10 | 346 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | HighQuality | 1 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 2 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 3 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 4 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 5 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 6 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 7 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 8 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 9 | 47 | ✓ |  |
| Product Review Analysis | HighQuality | 10 | 47 | ✓ |  |
| Incident Report Parser | Baseline | 1 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 2 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 3 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 4 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 5 | 120 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 6 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 7 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 8 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 9 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 10 | 118 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | LowQuality | 1 | 371 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 2 | 372 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 3 | 372 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 4 | 355 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 5 | 398 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 6 | 354 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 7 | 408 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 8 | 385 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 9 | 364 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 10 | 385 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | HighQuality | 1 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 2 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 3 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 4 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 5 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 6 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 7 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 8 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 9 | 44 | ✓ |  |
| Incident Report Parser | HighQuality | 10 | 44 | ✓ |  |
| Support Email Classification | Baseline | 1 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 2 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 3 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 4 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 5 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 6 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 7 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 8 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 9 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 10 | 85 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | LowQuality | 1 | 298 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 2 | 291 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 3 | 290 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 4 | 292 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 5 | 311 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 6 | 288 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 7 | 275 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 8 | 280 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 9 | 304 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 10 | 307 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | HighQuality | 1 | 42 | ✓ |  |
| Support Email Classification | HighQuality | 2 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 3 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 4 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 5 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 6 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 7 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 8 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 9 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 10 | 38 | ✓ |  |
| Job Posting Parser | Baseline | 1 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 2 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 3 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 4 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 5 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 6 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 7 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 8 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 9 | 113 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 10 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | LowQuality | 1 | 375 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 2 | 344 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 3 | 361 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 4 | 376 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 5 | 311 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 6 | 284 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 7 | 384 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 8 | 359 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 9 | 381 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 10 | 341 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | HighQuality | 1 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 2 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 3 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 4 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 5 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 6 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 7 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 8 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 9 | 64 | ✓ |  |
| Job Posting Parser | HighQuality | 10 | 64 | ✓ |  |
| Ambiguous Ticket Routing | Baseline | 1 | 127 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 2 | 136 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 3 | 136 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 4 | 156 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 5 | 154 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 6 | 142 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 7 | 135 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 8 | 135 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 9 | 156 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 10 | 125 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | LowQuality | 1 | 370 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 2 | 380 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 3 | 392 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 4 | 391 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 5 | 377 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 6 | 376 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 7 | 389 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 8 | 374 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 9 | 375 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 10 | 377 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | HighQuality | 1 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 2 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 3 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 4 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 5 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 6 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 7 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 8 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 9 | 48 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 10 | 48 | ✓ |  |

*Generated by [skillspector-quality](https://github.com) benchmark runner on 2026-06-26.*

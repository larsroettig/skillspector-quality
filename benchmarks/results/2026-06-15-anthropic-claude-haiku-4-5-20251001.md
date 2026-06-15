# Benchmark Results — 2026-06-15

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
| Customer Order Extraction | Baseline | — | 65 | 3/10 |
| Customer Order Extraction | LowQuality | 74 | 426 | 0/10 |
| Customer Order Extraction | HighQuality | 96 | 36 | 10/10 ✓ |
| Meeting Notes Summary | Baseline | — | 118 | 0/10 |
| Meeting Notes Summary | LowQuality | 63 | 396 | 0/10 |
| Meeting Notes Summary | HighQuality | 98 | 64 | 10/10 ✓ |
| Bug Report Triage | Baseline | — | 103 | 0/10 |
| Bug Report Triage | LowQuality | 72 | 652 | 0/10 |
| Bug Report Triage | HighQuality | 96 | 47 | 10/10 ✓ |
| Product Review Analysis | Baseline | — | 114 | 0/10 |
| Product Review Analysis | LowQuality | 83 | 306 | 0/10 |
| Product Review Analysis | HighQuality | 98 | 47 | 10/10 ✓ |
| Incident Report Parser | Baseline | — | 111 | 0/10 |
| Incident Report Parser | LowQuality | 89 | 340 | 0/10 |
| Incident Report Parser | HighQuality | 96 | 44 | 10/10 ✓ |
| Support Email Classification | Baseline | — | 68 | 0/10 |
| Support Email Classification | LowQuality | 81 | 291 | 0/10 |
| Support Email Classification | HighQuality | 96 | 38 | 10/10 ✓ |
| Job Posting Parser | Baseline | — | 114 | 0/10 |
| Job Posting Parser | LowQuality | 83 | 316 | 0/10 |
| Job Posting Parser | HighQuality | 96 | 64 | 10/10 ✓ |
| Ambiguous Ticket Routing | Baseline | — | 130 | 0/10 |
| Ambiguous Ticket Routing | LowQuality | 85 | 372 | 0/10 |
| Ambiguous Ticket Routing | HighQuality | 98 | 48 | 10/10 ✓ |

## Aggregate

| Arm | Avg body score | Output tok (med) | Correct rate |
|-----|:--------------:|:----------------:|:------------:|
| Baseline | — | 111 | 3% |
| LowQuality | ~79 | 359 | 0% |
| HighQuality | ~97 | 47 | 100% |

## Per-run detail

| Scenario | Arm | Run | Output tok | Correct | Reason |
|----------|-----|:---:|:----------:|:-------:|--------|
| Customer Order Extraction | Baseline | 1 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 2 | 63 | ✓ |  |
| Customer Order Extraction | Baseline | 3 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 4 | 63 | ✓ |  |
| Customer Order Extraction | Baseline | 5 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 6 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 7 | 66 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 8 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | Baseline | 9 | 64 | ✓ |  |
| Customer Order Extraction | Baseline | 10 | 65 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 1 | 397 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 2 | 481 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 3 | 417 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 4 | 384 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 5 | 469 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 6 | 410 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 7 | 436 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 8 | 435 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 9 | 468 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 10 | 374 | ✗ | missing keys: ['name', 'items'] |
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
| Meeting Notes Summary | Baseline | 1 | 119 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 2 | 119 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 3 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 4 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 5 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 6 | 119 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 7 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 8 | 145 | ✗ | missing keys: ['action_items'] |
| Meeting Notes Summary | Baseline | 9 | 117 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | Baseline | 10 | 119 | ✗ | missing keys: ['decisions', 'action_items'] |
| Meeting Notes Summary | LowQuality | 1 | 413 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 2 | 359 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 3 | 395 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 4 | 373 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 5 | 420 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 6 | 443 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 7 | 390 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 8 | 402 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 9 | 345 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 10 | 398 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
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
| Bug Report Triage | Baseline | 1 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 2 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 3 | 147 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 4 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 5 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 6 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 7 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 8 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 9 | 103 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 10 | 132 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | LowQuality | 1 | 738 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 2 | 696 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 3 | 628 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 4 | 716 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 5 | 658 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 6 | 701 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 7 | 450 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 8 | 645 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 9 | 572 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 10 | 450 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | HighQuality | 1 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 2 | 43 | ✓ |  |
| Bug Report Triage | HighQuality | 3 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 4 | 43 | ✓ |  |
| Bug Report Triage | HighQuality | 5 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 6 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 7 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 8 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 9 | 47 | ✓ |  |
| Bug Report Triage | HighQuality | 10 | 47 | ✓ |  |
| Product Review Analysis | Baseline | 1 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 2 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 3 | 115 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 4 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 5 | 118 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 6 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 7 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 8 | 115 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 9 | 116 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 10 | 114 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | LowQuality | 1 | 332 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 2 | 305 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 3 | 298 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 4 | 314 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 5 | 319 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 6 | 299 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 7 | 298 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 8 | 294 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 9 | 322 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 10 | 308 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
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
| Incident Report Parser | Baseline | 1 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 2 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 3 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 4 | 122 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 5 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 6 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 7 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 8 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 9 | 109 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 10 | 111 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | LowQuality | 1 | 369 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 2 | 339 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 3 | 334 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 4 | 338 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 5 | 364 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 6 | 401 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 7 | 341 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 8 | 338 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 9 | 325 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 10 | 355 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
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
| Support Email Classification | Baseline | 1 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 2 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 3 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 4 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 5 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 6 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 7 | 69 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 8 | 71 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 9 | 76 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 10 | 68 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | LowQuality | 1 | 290 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 2 | 322 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 3 | 296 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 4 | 301 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 5 | 284 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 6 | 316 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 7 | 286 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 8 | 287 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 9 | 287 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 10 | 292 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | HighQuality | 1 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 2 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 3 | 42 | ✓ |  |
| Support Email Classification | HighQuality | 4 | 42 | ✓ |  |
| Support Email Classification | HighQuality | 5 | 42 | ✓ |  |
| Support Email Classification | HighQuality | 6 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 7 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 8 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 9 | 38 | ✓ |  |
| Support Email Classification | HighQuality | 10 | 42 | ✓ |  |
| Job Posting Parser | Baseline | 1 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 2 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 3 | 109 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 4 | 114 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 5 | 109 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 6 | 109 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 7 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 8 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 9 | 115 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 10 | 109 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | LowQuality | 1 | 317 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 2 | 294 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 3 | 334 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 4 | 324 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 5 | 307 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 6 | 315 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 7 | 371 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 8 | 250 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 9 | 361 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 10 | 306 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
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
| Ambiguous Ticket Routing | Baseline | 1 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 2 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 3 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 4 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 5 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 6 | 143 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 7 | 131 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 8 | 119 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 9 | 133 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 10 | 130 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | LowQuality | 1 | 338 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 2 | 387 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 3 | 374 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 4 | 337 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 5 | 371 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 6 | 391 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 7 | 386 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 8 | 359 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 9 | 347 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 10 | 395 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
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

*Generated by [skillspector-quality](https://github.com) benchmark runner on 2026-06-15.*

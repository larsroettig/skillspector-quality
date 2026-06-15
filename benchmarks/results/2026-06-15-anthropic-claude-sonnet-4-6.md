# Benchmark Results — 2026-06-15

**Provider:** Anthropic  
**Model:** `claude-sonnet-4-6`  
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
| Customer Order Extraction | Baseline | — | 51 | 10/10 ✓ |
| Customer Order Extraction | LowQuality | 74 | 398 | 0/10 |
| Customer Order Extraction | HighQuality | 96 | 31 | 10/10 ✓ |
| Meeting Notes Summary | Baseline | — | 122 | 10/10 ✓ |
| Meeting Notes Summary | LowQuality | 63 | 426 | 0/10 |
| Meeting Notes Summary | HighQuality | 98 | 59 | 10/10 ✓ |
| Bug Report Triage | Baseline | — | 126 | 0/10 |
| Bug Report Triage | LowQuality | 72 | 1024 | 0/10 |
| Bug Report Triage | HighQuality | 96 | 38 | 10/10 ✓ |
| Product Review Analysis | Baseline | — | 91 | 0/10 |
| Product Review Analysis | LowQuality | 83 | 305 | 0/10 |
| Product Review Analysis | HighQuality | 98 | 43 | 10/10 ✓ |
| Incident Report Parser | Baseline | — | 119 | 0/10 |
| Incident Report Parser | LowQuality | 89 | 757 | 0/10 |
| Incident Report Parser | HighQuality | 96 | 39 | 10/10 ✓ |
| Support Email Classification | Baseline | — | 110 | 0/10 |
| Support Email Classification | LowQuality | 81 | 340 | 0/10 |
| Support Email Classification | HighQuality | 96 | 37 | 10/10 ✓ |
| Job Posting Parser | Baseline | — | 93 | 0/10 |
| Job Posting Parser | LowQuality | 83 | 522 | 0/10 |
| Job Posting Parser | HighQuality | 96 | 59 | 10/10 ✓ |
| Ambiguous Ticket Routing | Baseline | — | 149 | 0/10 |
| Ambiguous Ticket Routing | LowQuality | 85 | 402 | 0/10 |
| Ambiguous Ticket Routing | HighQuality | 98 | 47 | 10/10 ✓ |

## Aggregate

| Arm | Avg body score | Output tok (med) | Correct rate |
|-----|:--------------:|:----------------:|:------------:|
| Baseline | — | 114 | 25% |
| LowQuality | ~79 | 428 | 0% |
| HighQuality | ~97 | 41 | 100% |

## Per-run detail

| Scenario | Arm | Run | Output tok | Correct | Reason |
|----------|-----|:---:|:----------:|:-------:|--------|
| Customer Order Extraction | Baseline | 1 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 2 | 40 | ✓ |  |
| Customer Order Extraction | Baseline | 3 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 4 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 5 | 40 | ✓ |  |
| Customer Order Extraction | Baseline | 6 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 7 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 8 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 9 | 51 | ✓ |  |
| Customer Order Extraction | Baseline | 10 | 51 | ✓ |  |
| Customer Order Extraction | LowQuality | 1 | 513 | ✗ | missing keys: ['name', 'order_number', 'items'] |
| Customer Order Extraction | LowQuality | 2 | 379 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 3 | 360 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 4 | 361 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 5 | 457 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 6 | 445 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 7 | 411 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 8 | 352 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 9 | 403 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | LowQuality | 10 | 393 | ✗ | missing keys: ['name', 'items'] |
| Customer Order Extraction | HighQuality | 1 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 2 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 3 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 4 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 5 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 6 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 7 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 8 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 9 | 31 | ✓ |  |
| Customer Order Extraction | HighQuality | 10 | 31 | ✓ |  |
| Meeting Notes Summary | Baseline | 1 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 2 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 3 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 4 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 5 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 6 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 7 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 8 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 9 | 122 | ✓ |  |
| Meeting Notes Summary | Baseline | 10 | 122 | ✓ |  |
| Meeting Notes Summary | LowQuality | 1 | 454 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 2 | 436 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 3 | 411 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 4 | 386 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 5 | 385 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 6 | 422 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 7 | 450 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 8 | 392 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 9 | 447 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 10 | 430 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | HighQuality | 1 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 2 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 3 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 4 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 5 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 6 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 7 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 8 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 9 | 59 | ✓ |  |
| Meeting Notes Summary | HighQuality | 10 | 59 | ✓ |  |
| Bug Report Triage | Baseline | 1 | 116 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 2 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 3 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 4 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 5 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 6 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 7 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 8 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 9 | 128 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 10 | 126 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | LowQuality | 1 | 1006 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 2 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 3 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 4 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 5 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 6 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 7 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 8 | 991 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 9 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 10 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | HighQuality | 1 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 2 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 3 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 4 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 5 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 6 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 7 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 8 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 9 | 38 | ✓ |  |
| Bug Report Triage | HighQuality | 10 | 38 | ✓ |  |
| Product Review Analysis | Baseline | 1 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 2 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 3 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 4 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 5 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 6 | 90 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 7 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 8 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 9 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 10 | 91 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | LowQuality | 1 | 345 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 2 | 302 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 3 | 303 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 4 | 318 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 5 | 327 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 6 | 305 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 7 | 300 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 8 | 290 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 9 | 305 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 10 | 314 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | HighQuality | 1 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 2 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 3 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 4 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 5 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 6 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 7 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 8 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 9 | 43 | ✓ |  |
| Product Review Analysis | HighQuality | 10 | 43 | ✓ |  |
| Incident Report Parser | Baseline | 1 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 2 | 121 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 3 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 4 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 5 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 6 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 7 | 121 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 8 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 9 | 118 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 10 | 119 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | LowQuality | 1 | 779 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 2 | 756 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 3 | 734 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 4 | 772 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 5 | 690 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 6 | 758 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 7 | 758 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 8 | 807 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 9 | 585 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 10 | 723 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | HighQuality | 1 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 2 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 3 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 4 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 5 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 6 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 7 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 8 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 9 | 39 | ✓ |  |
| Incident Report Parser | HighQuality | 10 | 39 | ✓ |  |
| Support Email Classification | Baseline | 1 | 100 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 2 | 110 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 3 | 109 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 4 | 101 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 5 | 110 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 6 | 99 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 7 | 110 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 8 | 101 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 9 | 112 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 10 | 110 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | LowQuality | 1 | 317 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 2 | 321 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 3 | 334 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 4 | 347 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 5 | 354 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 6 | 337 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 7 | 342 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 8 | 343 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 9 | 328 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 10 | 351 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | HighQuality | 1 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 2 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 3 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 4 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 5 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 6 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 7 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 8 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 9 | 37 | ✓ |  |
| Support Email Classification | HighQuality | 10 | 37 | ✓ |  |
| Job Posting Parser | Baseline | 1 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 2 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 3 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 4 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 5 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 6 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 7 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 8 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 9 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 10 | 93 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | LowQuality | 1 | 478 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 2 | 528 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 3 | 532 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 4 | 747 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 5 | 457 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 6 | 459 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 7 | 743 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 8 | 504 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 9 | 517 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 10 | 556 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | HighQuality | 1 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 2 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 3 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 4 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 5 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 6 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 7 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 8 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 9 | 59 | ✓ |  |
| Job Posting Parser | HighQuality | 10 | 59 | ✓ |  |
| Ambiguous Ticket Routing | Baseline | 1 | 156 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 2 | 137 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 3 | 149 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 4 | 158 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 5 | 149 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 6 | 137 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 7 | 137 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 8 | 151 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 9 | 149 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 10 | 137 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | LowQuality | 1 | 426 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 2 | 388 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 3 | 469 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 4 | 379 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 5 | 384 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 6 | 434 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 7 | 393 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 8 | 427 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 9 | 366 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 10 | 412 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | HighQuality | 1 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 2 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 3 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 4 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 5 | 46 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 6 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 7 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 8 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 9 | 47 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 10 | 47 | ✓ |  |

*Generated by [skillspector-quality](https://github.com) benchmark runner on 2026-06-15.*

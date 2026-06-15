# Benchmark Results — 2026-06-15

**Provider:** Anthropic  
**Model:** `claude-opus-4-8`  
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
| Customer Order Extraction | Baseline | — | 73 | 10/10 ✓ |
| Customer Order Extraction | LowQuality | 74 | 793 | 0/10 |
| Customer Order Extraction | HighQuality | 96 | 42 | 10/10 ✓ |
| Meeting Notes Summary | Baseline | — | 163 | 10/10 ✓ |
| Meeting Notes Summary | LowQuality | 63 | 459 | 0/10 |
| Meeting Notes Summary | HighQuality | 98 | 82 | 10/10 ✓ |
| Bug Report Triage | Baseline | — | 164 | 0/10 |
| Bug Report Triage | LowQuality | 72 | 1024 | 0/10 |
| Bug Report Triage | HighQuality | 96 | 68 | 10/10 ✓ |
| Product Review Analysis | Baseline | — | 125 | 0/10 |
| Product Review Analysis | LowQuality | 83 | 631 | 0/10 |
| Product Review Analysis | HighQuality | 98 | 72 | 10/10 ✓ |
| Incident Report Parser | Baseline | — | 138 | 0/10 |
| Incident Report Parser | LowQuality | 89 | 982 | 0/10 |
| Incident Report Parser | HighQuality | 96 | 52 | 10/10 ✓ |
| Support Email Classification | Baseline | — | 168 | 0/10 |
| Support Email Classification | LowQuality | 81 | 664 | 0/10 |
| Support Email Classification | HighQuality | 96 | 50 | 10/10 ✓ |
| Job Posting Parser | Baseline | — | 123 | 0/10 |
| Job Posting Parser | LowQuality | 83 | 757 | 0/10 |
| Job Posting Parser | HighQuality | 96 | 83 | 10/10 ✓ |
| Ambiguous Ticket Routing | Baseline | — | 180 | 0/10 |
| Ambiguous Ticket Routing | LowQuality | 85 | 867 | 0/10 |
| Ambiguous Ticket Routing | HighQuality | 98 | 58 | 10/10 ✓ |

## Aggregate

| Arm | Avg body score | Output tok (med) | Correct rate |
|-----|:--------------:|:----------------:|:------------:|
| Baseline | — | 145 | 25% |
| LowQuality | ~79 | 778 | 0% |
| HighQuality | ~97 | 63 | 100% |

## Per-run detail

| Scenario | Arm | Run | Output tok | Correct | Reason |
|----------|-----|:---:|:----------:|:-------:|--------|
| Customer Order Extraction | Baseline | 1 | 66 | ✓ |  |
| Customer Order Extraction | Baseline | 2 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 3 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 4 | 56 | ✓ |  |
| Customer Order Extraction | Baseline | 5 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 6 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 7 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 8 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 9 | 73 | ✓ |  |
| Customer Order Extraction | Baseline | 10 | 74 | ✓ |  |
| Customer Order Extraction | LowQuality | 1 | 679 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 2 | 822 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 3 | 572 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 4 | 804 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 5 | 823 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 6 | 829 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 7 | 782 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 8 | 826 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 9 | 773 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | LowQuality | 10 | 752 | ✗ | missing keys: ['name'] |
| Customer Order Extraction | HighQuality | 1 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 2 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 3 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 4 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 5 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 6 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 7 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 8 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 9 | 42 | ✓ |  |
| Customer Order Extraction | HighQuality | 10 | 42 | ✓ |  |
| Meeting Notes Summary | Baseline | 1 | 163 | ✓ |  |
| Meeting Notes Summary | Baseline | 2 | 160 | ✓ |  |
| Meeting Notes Summary | Baseline | 3 | 180 | ✓ |  |
| Meeting Notes Summary | Baseline | 4 | 159 | ✓ |  |
| Meeting Notes Summary | Baseline | 5 | 180 | ✓ |  |
| Meeting Notes Summary | Baseline | 6 | 159 | ✓ |  |
| Meeting Notes Summary | Baseline | 7 | 163 | ✓ |  |
| Meeting Notes Summary | Baseline | 8 | 180 | ✓ |  |
| Meeting Notes Summary | Baseline | 9 | 176 | ✓ |  |
| Meeting Notes Summary | Baseline | 10 | 160 | ✓ |  |
| Meeting Notes Summary | LowQuality | 1 | 431 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 2 | 447 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 3 | 509 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 4 | 505 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 5 | 450 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 6 | 448 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 7 | 515 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 8 | 468 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 9 | 509 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | LowQuality | 10 | 439 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Meeting Notes Summary | HighQuality | 1 | 81 | ✓ |  |
| Meeting Notes Summary | HighQuality | 2 | 83 | ✓ |  |
| Meeting Notes Summary | HighQuality | 3 | 81 | ✓ |  |
| Meeting Notes Summary | HighQuality | 4 | 82 | ✓ |  |
| Meeting Notes Summary | HighQuality | 5 | 81 | ✓ |  |
| Meeting Notes Summary | HighQuality | 6 | 82 | ✓ |  |
| Meeting Notes Summary | HighQuality | 7 | 82 | ✓ |  |
| Meeting Notes Summary | HighQuality | 8 | 85 | ✓ |  |
| Meeting Notes Summary | HighQuality | 9 | 83 | ✓ |  |
| Meeting Notes Summary | HighQuality | 10 | 82 | ✓ |  |
| Bug Report Triage | Baseline | 1 | 163 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 2 | 159 | ✗ | missing keys: ['component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 3 | 172 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 4 | 166 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 5 | 150 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 6 | 164 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 7 | 159 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 8 | 163 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 9 | 187 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | Baseline | 10 | 194 | ✗ | missing keys: ['severity', 'component', 'summary', 'regression'] |
| Bug Report Triage | LowQuality | 1 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 2 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 3 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 4 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 5 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 6 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 7 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 8 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 9 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | LowQuality | 10 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Bug Report Triage | HighQuality | 1 | 66 | ✓ |  |
| Bug Report Triage | HighQuality | 2 | 73 | ✓ |  |
| Bug Report Triage | HighQuality | 3 | 69 | ✓ |  |
| Bug Report Triage | HighQuality | 4 | 66 | ✓ |  |
| Bug Report Triage | HighQuality | 5 | 70 | ✓ |  |
| Bug Report Triage | HighQuality | 6 | 65 | ✓ |  |
| Bug Report Triage | HighQuality | 7 | 66 | ✓ |  |
| Bug Report Triage | HighQuality | 8 | 69 | ✓ |  |
| Bug Report Triage | HighQuality | 9 | 78 | ✓ |  |
| Bug Report Triage | HighQuality | 10 | 66 | ✓ |  |
| Product Review Analysis | Baseline | 1 | 124 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 2 | 125 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 3 | 125 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 4 | 124 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 5 | 125 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 6 | 213 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 7 | 124 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 8 | 125 | ✗ | missing keys: ['rating', 'pros', 'cons', 'recommend'] |
| Product Review Analysis | Baseline | 9 | 127 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | Baseline | 10 | 124 | ✗ | missing keys: ['rating', 'recommend'] |
| Product Review Analysis | LowQuality | 1 | 617 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 2 | 628 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 3 | 623 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 4 | 565 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 5 | 647 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 6 | 670 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 7 | 634 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 8 | 686 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 9 | 667 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | LowQuality | 10 | 594 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Product Review Analysis | HighQuality | 1 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 2 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 3 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 4 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 5 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 6 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 7 | 69 | ✓ |  |
| Product Review Analysis | HighQuality | 8 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 9 | 72 | ✓ |  |
| Product Review Analysis | HighQuality | 10 | 72 | ✓ |  |
| Incident Report Parser | Baseline | 1 | 136 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 2 | 136 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 3 | 136 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 4 | 145 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 5 | 136 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 6 | 141 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 7 | 141 | ✗ | missing keys: ['resolved'] |
| Incident Report Parser | Baseline | 8 | 136 | ✗ | missing keys: ['users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 9 | 145 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | Baseline | 10 | 145 | ✗ | missing keys: ['duration_minutes', 'root_cause', 'users_affected', 'resolved'] |
| Incident Report Parser | LowQuality | 1 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 2 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 3 | 986 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 4 | 906 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 5 | 912 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 6 | 922 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 7 | 942 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 8 | 977 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 9 | 991 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | LowQuality | 10 | 1024 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Incident Report Parser | HighQuality | 1 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 2 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 3 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 4 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 5 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 6 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 7 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 8 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 9 | 52 | ✓ |  |
| Incident Report Parser | HighQuality | 10 | 52 | ✓ |  |
| Support Email Classification | Baseline | 1 | 162 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 2 | 179 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 3 | 145 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 4 | 188 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 5 | 145 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 6 | 198 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | Baseline | 7 | 174 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 8 | 220 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 9 | 150 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Support Email Classification | Baseline | 10 | 131 | ✗ | missing keys: ['category', 'subject_summary'] |
| Support Email Classification | LowQuality | 1 | 660 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 2 | 613 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 3 | 773 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 4 | 668 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 5 | 774 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 6 | 638 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 7 | 647 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 8 | 739 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 9 | 670 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | LowQuality | 10 | 649 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Support Email Classification | HighQuality | 1 | 49 | ✓ |  |
| Support Email Classification | HighQuality | 2 | 50 | ✓ |  |
| Support Email Classification | HighQuality | 3 | 56 | ✓ |  |
| Support Email Classification | HighQuality | 4 | 49 | ✓ |  |
| Support Email Classification | HighQuality | 5 | 53 | ✓ |  |
| Support Email Classification | HighQuality | 6 | 54 | ✓ |  |
| Support Email Classification | HighQuality | 7 | 53 | ✓ |  |
| Support Email Classification | HighQuality | 8 | 49 | ✓ |  |
| Support Email Classification | HighQuality | 9 | 49 | ✓ |  |
| Support Email Classification | HighQuality | 10 | 51 | ✓ |  |
| Job Posting Parser | Baseline | 1 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 2 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 3 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 4 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 5 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 6 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 7 | 129 | ✗ | missing keys: ['title', 'employment_type', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 8 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 9 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | Baseline | 10 | 123 | ✗ | missing keys: ['title', 'years_experience', 'skills'] |
| Job Posting Parser | LowQuality | 1 | 590 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 2 | 868 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 3 | 754 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 4 | 760 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 5 | 791 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 6 | 754 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 7 | 749 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 8 | 601 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 9 | 826 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | LowQuality | 10 | 831 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Job Posting Parser | HighQuality | 1 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 2 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 3 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 4 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 5 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 6 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 7 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 8 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 9 | 83 | ✓ |  |
| Job Posting Parser | HighQuality | 10 | 83 | ✓ |  |
| Ambiguous Ticket Routing | Baseline | 1 | 192 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 2 | 192 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 3 | 167 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 4 | 199 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 5 | 182 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 6 | 168 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 7 | 159 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 8 | 189 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 9 | 129 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | Baseline | 10 | 177 | ✗ | missing keys: ['category', 'urgency', 'subject_summary'] |
| Ambiguous Ticket Routing | LowQuality | 1 | 839 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 2 | 849 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 3 | 855 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 4 | 952 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 5 | 852 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 6 | 861 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 7 | 873 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 8 | 906 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 9 | 894 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | LowQuality | 10 | 983 | ✗ | invalid JSON: Expecting value: line 1 column 1 (char 0) |
| Ambiguous Ticket Routing | HighQuality | 1 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 2 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 3 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 4 | 59 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 5 | 59 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 6 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 7 | 61 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 8 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 9 | 58 | ✓ |  |
| Ambiguous Ticket Routing | HighQuality | 10 | 58 | ✓ |  |

*Generated by [skillspector-quality](https://github.com) benchmark runner on 2026-06-15.*

"""3-arm benchmark scenarios: Baseline · LowQuality · HighQuality.

Each scenario has three arms:
  Baseline    — No SKILL.md. Generic "extract JSON" instruction with no schema hints.
                Shows what you get with zero investment in skill design.
  LowQuality  — Bad SKILL.md body (conversational persona, chain-of-thought, no schema).
                Represents common first-draft quality.
  HighQuality — Good SKILL.md body (strict JSON schema, concise task description, example).
                Represents skills improved using skillspector-quality recommendations.

Comparing Baseline → LowQuality → HighQuality proves the library adds measurable value
over both "nothing" and "any SKILL.md".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Arm:
    name: str             # "Baseline" | "LowQuality" | "HighQuality"
    skill_md: str | None  # None for Baseline; SKILL.md full text for others


@dataclass
class Scenario:
    name: str
    test_input: str
    required_keys: list[str]
    # Deterministic values to check for exact equality (bool/int/str).
    # A list value [] acts as a marker: check that the actual value is a non-empty list.
    expected: dict[str, Any]
    # Valid string values for enum-typed fields (checked case-insensitively).
    enum_fields: dict[str, list[str]]
    arms: list[Arm]  # always [Baseline, LowQuality, HighQuality]


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 1 — Customer Order Data Extraction
# ─────────────────────────────────────────────────────────────────────────────

_LOW_CUSTOMER = """\
---
name: Customer_Data_Helper
description: document formatter and validator
---

You are a super helpful and friendly AI assistant who is great at helping users \
with all kinds of tasks. I need you to carefully look at the text below and try to \
find the customer's name, their order number, and everything that they bought. It \
would be super great if you could format this information nicely as JSON for me so \
I can parse it later in my application. Please try not to make mistakes because \
this is very important! Also, please explain in detail why you picked the items \
that you did and describe your complete reasoning step by step so I can understand \
your complete thought process and verify your work. The output is very important to \
get right because it will be used for automated data processing in production. Make \
sure you are thorough and comprehensive in your response.

Text: {input}
"""

_HIGH_CUSTOMER = """\
---
name: customer-data-extraction
description: Extract customer name, order number, and purchased items from support messages into structured JSON output.
when_to_use: |
  Use when processing customer support messages to extract structured order data.
  Invoke for CRM pipelines and order management systems that require machine-readable
  customer records. Do not use for general text extraction, non-customer documents,
  or when unstructured output is acceptable.
user-invocable: false
allowed-tools: []
---

# Customer Data Extraction

Extract structured order data from customer support messages.

## Task

Parse the input message and return ONLY valid JSON — no markdown code blocks,
no explanations, no conversational text.

Required schema: `{"name": string, "order_number": string, "items": list[string]}`

Input: {input}

## Example

Input:

```text
Hi, I'm Alex Kim. My order #77341 includes a laptop stand and an HDMI cable.
```

Output:

```json
{"name": "Alex Kim", "order_number": "77341", "items": ["laptop stand", "HDMI cable"]}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 2 — Meeting Notes Summarisation
# ─────────────────────────────────────────────────────────────────────────────

_LOW_MEETING = """\
---
name: Meeting Notes Summarizer
description: text analysis utility
---

Please summarize these meeting notes for me in a helpful and friendly way. It would \
be really great if you could capture all the key discussion points that came up \
during the meeting, and also any decisions that were made during the meeting, and \
also all the important action items that were assigned to people during the meeting. \
Also feel free to format it however you think looks best and works well for you! It \
would also be super helpful if you shared your general thoughts on how the meeting \
went overall and what improvements could have been made to the meeting. Please also \
note who said what if that information is available and seems relevant to include in \
your comprehensive summary. Try to be thorough and include everything that seems \
important to capture from the meeting discussion.

Meeting notes:
{input}
"""

_HIGH_MEETING = """\
---
name: meeting-notes-summarizer
description: Summarize meeting transcripts and notes into structured JSON capturing decisions and action items.
when_to_use: |
  Use when extracting structured outcomes from meeting transcripts or written notes.
  Invoke for project management integrations and sprint planning tools that require
  machine-readable meeting summaries. Do not use for real-time note-taking,
  non-meeting documents, or when a prose summary is explicitly requested.
user-invocable: false
allowed-tools: []
---

# Meeting Notes Summarizer

Extract structured decisions and action items from meeting notes.

## Task

Parse the meeting notes and return ONLY valid JSON — no markdown code blocks,
no prose explanation, no conversational text.

Required schema:
`{"decisions": list[string], "action_items": [{"owner": string, "task": string}]}`

Notes: {input}

## Example

Input:

```text
Team agreed to adopt trunk-based development. Alice will set up branch protection
rules by Thursday. Bob will update the CI pipeline configuration before next sprint.
```

Output:

```json
{"decisions": ["adopt trunk-based development"], "action_items": [{"owner": "Alice", "task": "set up branch protection rules"}, {"owner": "Bob", "task": "update CI pipeline"}]}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 3 — Bug Report Triage
# ─────────────────────────────────────────────────────────────────────────────

_LOW_BUG = """\
---
name: BugHelper
description: helpful assistant for software bugs
---

You are a very helpful and experienced software quality assurance engineer who has \
been working with bugs and issue tracking systems for many years. I need you to look \
at the bug report below and give me a structured analysis of it. Please read through \
all the details carefully and tell me what you think about the severity of this bug, \
which component or part of the system it seems to affect, a brief description of \
what the problem is, and whether this appears to be a regression from previous \
behavior. It would be very helpful if you could also explain your reasoning and \
thinking about why you made those determinations so I can understand your analysis.

Bug report: {input}
"""

_HIGH_BUG = """\
---
name: bug-report-triage
description: Triage bug reports by extracting severity, component, summary, and regression status into structured JSON.
when_to_use: |
  Use when processing incoming bug reports to extract structured triage data.
  Invoke for issue tracking integrations and automated triage pipelines.
  Do not use for general code review, feature requests, or non-bug-report text.
user-invocable: false
allowed-tools: []
---

# Bug Report Triage

Extract structured triage data from bug reports.

## Task

Parse the bug report and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"severity": "critical"|"high"|"medium"|"low", "component": string, "summary": string, "regression": boolean}`

Bug report: {input}

## Example

Input:

```text
Login button unresponsive after v2.3.1 update. Users cannot authenticate. Was working before the update.
```

Output:

```json
{"severity": "critical", "component": "authentication", "summary": "Login button unresponsive after v2.3.1 update", "regression": true}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 4 — Product Review Analysis
# ─────────────────────────────────────────────────────────────────────────────

_LOW_REVIEW = """\
---
name: ReviewAnalyzer
description: review tool
---

I need you to be a helpful review analysis assistant. Please read this product \
review carefully and analyze the sentiment to tell me if the reviewer liked the \
product or not. Also try to identify any good points they mentioned about the \
product as well as any negative aspects or complaints they brought up. Finally, \
tell me whether you think they would recommend this product to others based on \
what they wrote. Please share your reasoning and any relevant observations about \
the reviewer's tone and overall impression of the product.

Review: {input}
"""

_HIGH_REVIEW = """\
---
name: product-review-analysis
description: Analyze product reviews and extract rating, pros, cons, and recommendation into structured JSON.
when_to_use: |
  Use when processing product reviews to extract sentiment and structured feedback.
  Invoke for product feedback pipelines and review aggregation tools.
  Do not use for service reviews, employee feedback, or non-product text.
user-invocable: false
allowed-tools: []
---

# Product Review Analysis

Extract structured sentiment data from product reviews.

## Task

Parse the review and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"rating": "positive"|"neutral"|"negative", "pros": list[string], "cons": list[string], "recommend": boolean}`

Review: {input}

## Example

Input:

```text
Great headphones! Sound quality is excellent and battery lasts 30 hours. A bit heavy for long sessions though. Would recommend.
```

Output:

```json
{"rating": "positive", "pros": ["excellent sound quality", "30 hour battery"], "cons": ["heavy for long sessions"], "recommend": true}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 5 — Incident Report Parser
# ─────────────────────────────────────────────────────────────────────────────

_LOW_INCIDENT = """\
---
name: IncidentParser
description: tool for incidents
---

You are an experienced site reliability engineer. Please help me parse this \
incident report to extract the key information. I need to know how long the \
incident lasted in minutes, what caused it, how many users were affected, and \
whether it has been resolved. Please analyze the report carefully and provide this \
information in a clear and comprehensive way. Feel free to include any additional \
context or observations that might be useful for the post-mortem process.

Incident report: {input}
"""

_HIGH_INCIDENT = """\
---
name: incident-report-parser
description: Parse incident reports to extract duration, root cause, user impact, and resolution status into structured JSON.
when_to_use: |
  Use when processing incident reports to extract structured operational data.
  Invoke for SRE dashboards, post-mortem automation, and incident tracking integrations.
  Do not use for change requests, deployment notes, or general operational documentation.
user-invocable: false
allowed-tools: []
---

# Incident Report Parser

Extract structured data from incident reports.

## Task

Parse the incident report and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"duration_minutes": integer, "root_cause": string, "users_affected": integer, "resolved": boolean}`

Report: {input}

## Example

Input:

```text
INCIDENT: Service unavailable for 45 minutes. Cause: Redis OOM. 800 users impacted. Resolved: Yes.
```

Output:

```json
{"duration_minutes": 45, "root_cause": "Redis out of memory", "users_affected": 800, "resolved": true}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 6 — Support Email Classification
# ─────────────────────────────────────────────────────────────────────────────

_LOW_EMAIL = """\
---
name: EmailHelper
description: email tool
---

You are a friendly and helpful customer support AI. Please read this email from \
a customer carefully and tell me what type of email it is — like billing, technical \
support, or something else. Also tell me how urgent you think it is and give me a \
brief summary of what the email is about. It would be great if you could explain \
your thinking and reasoning so I can understand your analysis better.

Email: {input}
"""

_HIGH_EMAIL = """\
---
name: support-email-classifier
description: Classify inbound support emails by category and urgency into structured JSON.
when_to_use: |
  Use when routing inbound customer support emails to the correct team queue.
  Invoke for helpdesk integrations and support triage workflows.
  Do not use for internal emails, marketing messages, or non-support correspondence.
user-invocable: false
allowed-tools: []
---

# Support Email Classifier

Classify inbound support emails into structured routing data.

## Task

Parse the email and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"category": "billing"|"technical"|"general"|"cancellation", "urgency": "high"|"medium"|"low", "subject_summary": string}`

Email: {input}

## Example

Input:

```text
My account was charged twice this month. I need this fixed immediately, I'm really frustrated.
```

Output:

```json
{"category": "billing", "urgency": "high", "subject_summary": "duplicate charge on account"}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 7 — Job Posting Parser
# ─────────────────────────────────────────────────────────────────────────────

_LOW_JOB = """\
---
name: JobParser
description: job posting tool
---

You are an experienced HR professional and talent acquisition specialist. Please \
read this job posting carefully and extract the key details for me. I need to know \
the job title, the company name, the type of employment, the required years of \
experience, and a list of required skills or technologies. Please be thorough and \
comprehensive in your extraction and explain any ambiguities you encounter.

Job posting: {input}
"""

_HIGH_JOB = """\
---
name: job-posting-parser
description: Parse job postings to extract title, company, employment type, experience, and required skills into structured JSON.
when_to_use: |
  Use when ingesting job postings into an ATS or job aggregation platform.
  Invoke for resume matching pipelines and talent search tools that require
  machine-readable job requirements. Do not use for internship postings,
  freelance gigs, or non-job-related documents.
user-invocable: false
allowed-tools: []
---

# Job Posting Parser

Extract structured data from job postings.

## Task

Parse the job posting and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"title": string, "company": string, "employment_type": "full-time"|"part-time"|"contract", "years_experience": integer, "skills": list[string]}`

Job posting: {input}

## Example

Input:

```text
Senior Backend Engineer at Acme Corp. Full-time. 5+ years required. Must know Python, PostgreSQL, and Docker.
```

Output:

```json
{"title": "Senior Backend Engineer", "company": "Acme Corp", "employment_type": "full-time", "years_experience": 5, "skills": ["Python", "PostgreSQL", "Docker"]}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Scenario 8 — Ambiguous Ticket Routing (boundary robustness)
#
# Input deliberately straddles two valid categories (billing + technical).
# Deterministic assertion: urgency=high only.  Category is validated against
# the enum but NOT pinned — both "billing" and "technical" are acceptable.
# Purpose: verify HighQuality produces consistent valid JSON even when the
# correct semantic answer is ambiguous.
# ─────────────────────────────────────────────────────────────────────────────

_LOW_AMBIGUOUS = """\
---
name: TicketRouter
description: ticket routing assistant
---

You are a helpful customer support specialist. Please read this support ticket carefully \
and help me understand what type of issue this is and how urgent it seems. \
Also give me a brief summary of the main problem. \
Please explain your thinking about how you classified it, and note any uncertainties — \
it's important to get this right because the category decides which team handles it.

Ticket: {input}
"""

_HIGH_AMBIGUOUS = """\
---
name: support-ticket-router
description: Route support tickets by category and urgency into structured JSON, choosing the dominant issue type when multiple concerns are present.
when_to_use: |
  Use when routing inbound support tickets to the correct team queue.
  Invoke for helpdesk integrations and support triage workflows.
  Do not use for internal tickets, feature requests, or non-support correspondence.
user-invocable: false
allowed-tools: []
---

# Support Ticket Router

Classify inbound support tickets into structured routing data.

## Task

Parse the ticket and return ONLY valid JSON — no markdown, no explanation.

Required schema:
`{"category": "billing"|"technical"|"general"|"cancellation", "urgency": "high"|"medium"|"low", "subject_summary": string}`

When a ticket touches multiple categories, choose the **dominant** one — the issue that must be resolved first for the customer to make progress.

Ticket: {input}

## Example

Input:

```text
I was charged $9.99 but my account still shows the free tier. I tried updating my plan
settings but the page throws a 500 error every time I save.
```

Output:

```json
{"category": "billing", "urgency": "high", "subject_summary": "charged for upgrade but account not updated; settings page erroring"}
```
"""


# ─────────────────────────────────────────────────────────────────────────────
# Exported dataset
# ─────────────────────────────────────────────────────────────────────────────

SCENARIOS: list[Scenario] = [
    Scenario(
        name="Customer Order Extraction",
        test_input=(
            "Hey there, my name is Sarah Connor. I'm calling about my order #88492. "
            "I bought a pair of running shoes and a water bottle, but they haven't arrived yet."
        ),
        required_keys=["name", "order_number", "items"],
        expected={"order_number": "88492", "items": []},
        enum_fields={},
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_CUSTOMER),
            Arm(name="HighQuality", skill_md=_HIGH_CUSTOMER),
        ],
    ),
    Scenario(
        name="Meeting Notes Summary",
        test_input=(
            "John: Let's go with the new UI design. Mary: Agreed. "
            "John: Mary, can you finalise the mockups? Mary: Sure, I'll have them ready by Friday. "
            "Tom: I'll handle the API integration by end of month."
        ),
        required_keys=["decisions", "action_items"],
        expected={"decisions": [], "action_items": []},
        enum_fields={},
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_MEETING),
            Arm(name="HighQuality", skill_md=_HIGH_MEETING),
        ],
    ),
    Scenario(
        name="Bug Report Triage",
        test_input=(
            "When I click Submit on the checkout page it shows a blank screen. "
            "Started after last Tuesday's deploy. Worse on mobile. "
            "Error in console: TypeError: Cannot read property 'total' of undefined. "
            "This broke 3 weeks ago and was working fine before."
        ),
        required_keys=["severity", "component", "summary", "regression"],
        expected={"regression": True},
        enum_fields={"severity": ["critical", "high", "medium", "low"]},
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_BUG),
            Arm(name="HighQuality", skill_md=_HIGH_BUG),
        ],
    ),
    Scenario(
        name="Product Review Analysis",
        test_input=(
            "I bought this laptop 3 months ago. Battery lasts 12 hours easily. "
            "Keyboard is fantastic. However the fan gets quite loud during video processing. "
            "Display is gorgeous. Would definitely buy again."
        ),
        required_keys=["rating", "pros", "cons", "recommend"],
        expected={"recommend": True, "pros": [], "cons": []},
        enum_fields={"rating": ["positive", "neutral", "negative"]},
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_REVIEW),
            Arm(name="HighQuality", skill_md=_HIGH_REVIEW),
        ],
    ),
    Scenario(
        name="Incident Report Parser",
        test_input=(
            "INCIDENT: Production API down for 23 minutes starting 14:32 UTC. "
            "Root cause: database connection pool exhausted after deploy. "
            "Impact: 1200 users affected. "
            "Resolution: rolled back deploy, increased pool size. "
            "Owner: @sre-team. Status: Resolved."
        ),
        required_keys=["duration_minutes", "root_cause", "users_affected", "resolved"],
        expected={"duration_minutes": 23, "users_affected": 1200, "resolved": True},
        enum_fields={},
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_INCIDENT),
            Arm(name="HighQuality", skill_md=_HIGH_INCIDENT),
        ],
    ),
    Scenario(
        name="Support Email Classification",
        test_input=(
            "Hi, I've been trying to cancel my subscription for two weeks now. "
            "Every time I click the cancel button nothing happens. "
            "I've already been charged for next month. Please help me cancel and get a refund!"
        ),
        required_keys=["category", "urgency", "subject_summary"],
        expected={"category": "cancellation"},
        enum_fields={
            "category": ["billing", "technical", "general", "cancellation"],
            "urgency": ["high", "medium", "low"],
        },
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_EMAIL),
            Arm(name="HighQuality", skill_md=_HIGH_EMAIL),
        ],
    ),
    Scenario(
        name="Job Posting Parser",
        test_input=(
            "We're hiring a Staff Data Engineer at DataFlow Inc. "
            "This is a full-time position requiring 7+ years of experience. "
            "Required skills: Apache Spark, Kafka, Python, and AWS Glue. "
            "Join our team building large-scale data pipelines."
        ),
        required_keys=["title", "company", "employment_type", "years_experience", "skills"],
        expected={"company": "DataFlow Inc", "years_experience": 7, "skills": []},
        enum_fields={
            "employment_type": ["full-time", "part-time", "contract"],
        },
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_JOB),
            Arm(name="HighQuality", skill_md=_HIGH_JOB),
        ],
    ),
    Scenario(
        name="Ambiguous Ticket Routing",
        test_input=(
            "My invoice shows a $49.99 charge for Enterprise that I never requested. "
            "I've been a Basic plan customer for years. "
            "I tried to downgrade back but the plan selection page just spins forever without saving. "
            "Either this is a billing error or something's wrong with the upgrade system — I can't tell which."
        ),
        required_keys=["category", "urgency", "subject_summary"],
        # urgency is unambiguous (frustrated user + unexpected charge); category is NOT asserted
        # because both "billing" and "technical" are valid interpretations.
        expected={"urgency": "high"},
        enum_fields={
            "category": ["billing", "technical", "general", "cancellation"],
            "urgency": ["high", "medium", "low"],
        },
        arms=[
            Arm(name="Baseline", skill_md=None),
            Arm(name="LowQuality", skill_md=_LOW_AMBIGUOUS),
            Arm(name="HighQuality", skill_md=_HIGH_AMBIGUOUS),
        ],
    ),
]

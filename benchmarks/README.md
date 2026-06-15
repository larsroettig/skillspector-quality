# skillspector-quality Benchmark

Proves that the skillspector-quality library adds measurable value — not just a
higher score, but fewer output tokens and more reliable structured output — across
8 diverse extraction tasks including one deliberately ambiguous boundary case.

## Design

### Three arms

| Arm | What it is | SKILL.md |
|-----|-----------|---------|
| **Baseline** | Generic "extract JSON" prompt, no SKILL.md at all | None |
| **LowQuality** | Conversational body, no schema, no example | Bad first draft |
| **HighQuality** | Concise task + strict schema + example, all recommendations applied | Improved by this library |

Comparing **Baseline → LowQuality → HighQuality** answers two questions:
1. Does having *any* SKILL.md help over nothing?
2. Does following skillspector-quality's recommendations add further value?

### Two metrics

| Metric | Type | What it measures |
|--------|------|-----------------|
| **output_tokens** | Measurement | Always recorded — how verbose is the response? |
| **schema_correct** | Gate | Pass/fail — did the LLM return the right structure with the right values? |

Separating these prevents gaming: a short-but-wrong answer doesn't count as efficient.

### Eight scenarios

| # | Scenario | Key required fields | Notes |
|---|----------|---------------------|-------|
| 1 | Customer Order Extraction | `name`, `order_number`, `items` | |
| 2 | Meeting Notes Summary | `decisions`, `action_items[{owner, task}]` | |
| 3 | Bug Report Triage | `severity`, `component`, `summary`, `regression` | deterministic check |
| 4 | Product Review Analysis | `rating`, `pros`, `cons`, `recommend` | enum + bool check |
| 5 | Incident Report Parser | `duration_minutes`, `root_cause`, `users_affected`, `resolved` | deterministic check |
| 6 | Support Email Classification | `category`, `urgency`, `subject_summary` | enum check |
| 7 | Job Posting Parser | `title`, `company`, `employment_type`, `years_experience`, `skills` | deterministic check |
| 8 | **Ambiguous Ticket Routing** | `category`, `urgency`, `subject_summary` | **boundary case** — input deliberately straddles two categories; only `urgency` is asserted |

Scenario 8 tests robustness: the input is a billing/technical hybrid where both category values
are defensible. Correctness requires producing valid JSON with a valid enum value — not picking
the "right" category (there isn't one). This verifies that HighQuality prompts stay consistent
under genuine semantic ambiguity.

### Statistical design

- `N = 10` repeats per cell (3 arms × 8 scenarios = 240 LLM calls)
- `temperature = 0.3` — enough variance to stress-test, stable enough for extraction
- **Median** output tokens reported (robust to outlier runs)
- Correct count reported as `n/N`
- Each call receives a unique nonce appended to the prompt to prevent provider-side
  exact-match caching and KV cache warmth from flattening latency measurements

## Running

```bash
# Dry-run: quality scores only, no LLM calls
python benchmarks/run_benchmark.py --dry-run

# Full run — single model from env (default: gpt-4o-mini, N=10)
export OPENAI_API_KEY=sk-...
python benchmarks/run_benchmark.py

# Override repeat count (short or long form)
python benchmarks/run_benchmark.py -n 3
python benchmarks/run_benchmark.py --repeats 3

# Anthropic — single model
export SKILLSPECTOR_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python benchmarks/run_benchmark.py

# Anthropic — specific models (cross-model comparison table printed at end)
python benchmarks/run_benchmark.py --models claude-haiku-4-5-20251001,claude-sonnet-4-6

# Anthropic — all three models (haiku · sonnet · opus)
python benchmarks/run_benchmark.py --anthropic-all

# Anthropic — all three models, fewer repeats
python benchmarks/run_benchmark.py --anthropic-all -n 5

# NVIDIA build.nvidia.com
export SKILLSPECTOR_PROVIDER=nv_build
export NVIDIA_INFERENCE_KEY=nvapi-...
python benchmarks/run_benchmark.py

# Local Ollama — single model
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export SKILLSPECTOR_MODEL=llama3.1:8b
python benchmarks/run_benchmark.py

# Local Ollama — all pulled models (N=5 per model)
python benchmarks/run_benchmark.py --ollama-all

# Pin a reference model for the multi-model comparison table
SKILLSPECTOR_BENCHMARK_MODEL=llama3.1:8b python benchmarks/run_benchmark.py --ollama-all
```

### CLI reference

```
usage: python benchmarks/run_benchmark.py [-h] [-n N] [--dry-run]
       [--models MODEL[,MODEL,...]] [--anthropic-all] [--ollama-all]

options:
  -h, --help               show this help message and exit
  -n N, --repeats N        repeats per cell (default: 10 single/--models,
                           10 --anthropic-all, 5 --ollama-all)
  --dry-run                print quality scores only — no LLM calls
  --models MODEL[,...]     comma-separated list of models to run against the
                           current provider; prints a cross-model comparison
                           table when done
  --anthropic-all          run all Anthropic models: claude-haiku-4-5-20251001,
                           claude-sonnet-4-6, claude-opus-4-8
  --ollama-all             discover and benchmark every pulled Ollama model
```

Provider, model, and API key are set via environment variables:

| Variable | Default | Notes |
|----------|---------|-------|
| `SKILLSPECTOR_PROVIDER` | `openai` | `openai` \| `anthropic` \| `nv_build` |
| `SKILLSPECTOR_MODEL` | provider default | overrides the default model for the provider |
| `SKILLSPECTOR_TEMPERATURE` | `0.3` | applied to all calls |
| `OPENAI_API_KEY` | — | required for OpenAI and Ollama |
| `ANTHROPIC_API_KEY` | — | required for Anthropic |
| `NVIDIA_INFERENCE_KEY` | — | required for NVIDIA build.nvidia.com |
| `OPENAI_BASE_URL` | — | set to `http://localhost:11434/v1` for Ollama |
| `SKILLSPECTOR_BENCHMARK_MODEL` | first discovered | reference model for `--ollama-all` table |

## Output

Terminal output during the run shows per-cell progress:

```
  ── Customer Order Extraction
     Baseline       run 1/10   66 out-tok  1.2s  ✗  baseline
     Baseline       run 2/10   66 out-tok  1.1s  ✗  baseline
     ...
     HighQuality    run 10/10  31 out-tok  0.9s  ✓  body=96
```

After all runs, a comparison table is printed and two result files are saved to
`benchmarks/results/YYYY-MM-DD-{provider}-{model}.{md,json}`.

When `--models` or `--anthropic-all` or `--ollama-all` is used, a cross-model
comparison table is printed after all models complete.

## Files

```
benchmarks/
  scenarios.py     — 3-arm Scenario dataclass + 8 scenario instances
  validators.py    — validate(output, required_keys, expected, enum_fields) → (bool, reason)
                     includes JSON-from-prose extraction for LowQuality outputs
  run_benchmark.py — runner: 3-arm × N-repeat × 8 scenarios, markdown + JSON output
  README.md        — this file
  results/         — result files (gitignored except .gitkeep)
```

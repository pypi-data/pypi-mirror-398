# LLMScorecard

Regression-based LLM benchmark ratings + publication-ready scorecards.

## Title and one-line promise

LLMScorecard turns raw LLM evaluation results into defensible ratings (with uncertainty) and an offline HTML scorecard report.

## Overview

LLMScorecard is **not** an eval runner. It does not prompt models, execute tasks, or manage datasets.

It is the “score modeling + reporting” layer you put downstream of your existing evaluation harness to:
- validate inputs (schema-first)
- fit research-based score models (regression with controls/interactions)
- quantify uncertainty (bootstrap and/or cluster-robust)
- emit reproducible artifacts you can publish and archive

Outputs are designed for org adoption: deterministic seeds, embedded config, schema versions, offline HTML, no phone-home.

Typical artifacts:
- `results.json` + `fitted_model.json`
- `ratings.csv` (leaderboard + intervals)
- `report.html` (shareable, offline)

## Features

- Single-command report generation: `llmscorecard report results.csv --out report.html`
- Schema-first: validate + summarize
- Research-based ratings: fixed effects + interactions (LLM, category, task)
- Uncertainty: bootstrap and/or cluster-robust
- Reproducibility: config embedded, seed, schema version
- Exports: `ratings.csv`, `tables.csv`, plots
- Extensible adapters (future): `lm-eval-harness`, `lighteval`

## Install

Requires Python >= 3.9.

```bash
pip install llmscorecard
```

Optional extras (future-proof; may be thin in early versions):

```bash
pip install "llmscorecard[report]"
pip install "llmscorecard[stats]"
```

## Quickstart (CLI)

Create `examples/results.csv` with the required columns:

```csv
llm,category,task,item_id,score
gpt-4o-mini,math,arithmetic,1,0.92
gpt-4o-mini,math,arithmetic,2,0.88
llama-3.1-8b-instruct,math,arithmetic,1,0.74
llama-3.1-8b-instruct,math,arithmetic,2,0.70
gpt-4o-mini,code,unit_tests,3,0.81
llama-3.1-8b-instruct,code,unit_tests,3,0.63
```

Validate:

```bash
llmscorecard validate examples/results.csv
```

Generate an offline HTML scorecard:

```bash
llmscorecard report examples/results.csv --out report.html
```

This produces `report.html` (and, depending on your config/version, sidecar artifacts like `ratings.csv`).

## Quickstart (Python)

Target API (stable intent; may evolve early on):

```python
from llmscorecard import Scorecard

sc = Scorecard.from_csv("examples/results.csv")

sc.fit(
		model="fe_interaction_task",
		ci="bootstrap",
		n_boot=400,
		seed=123,
)

sc.report("report.html")
```

## Example output

`llmscorecard report …` emits a CI-friendly summary and writes the HTML report:

```text
report:
	leaderboard (overall):
		1) gpt-4o-mini              0.000  [ -0.042,  0.041]
		2) llama-3.1-8b-instruct   -0.138  [ -0.191, -0.087]

	top categories (mean effect):
		math                        +0.021
		code                        -0.017

	model card:
		model: fe_interaction_task
		formula: score ~ C(llm) + C(category) + C(task) + C(llm):C(category)
		ci: bootstrap (by item_id), n=400, seed=123
		n_rows: 6
		n_items: 3
		schema_version: 0.1
		artifacts: results.json, fitted_model.json, ratings.csv, report.html
```

## Results schema

LLMScorecard expects long-form results (one row per item × model, optionally with weights).

Required:
- `llm` (string)
- `category` (string)
- `task` (string)
- `item_id` (string|int)
- `score` (float; higher is better)

Optional:
- `metric` (string; if you store multiple metrics in one file)
- `weight` (float; defaults to 1.0)
- `meta` (JSON; per-row metadata)

Canonical JSON:
- `results.json` includes `schema_version: "0.1"` and normalized fields.
- `llmscorecard validate` is the gatekeeper (fail fast, actionable errors).

## Rating models

Current models:
- `fe_interaction_task` (default): `score ~ C(llm) + C(category) + C(task) + C(llm):C(category)`
- `fe_interaction`: `score ~ C(llm) + C(category) + C(llm):C(category)`
- `pairwise_bt` (future/experimental): Bradley–Terry for A/B preferences

Uncertainty:
- Bootstrap by `item_id` (clustered resampling) for CIs and stability checks.
- Cluster-robust SEs clustered by `item_id` (when aligned with your modeling assumptions).

## Configuration

Example `scorecard.yaml`:

```yaml
metric: score
model: fe_interaction_task
ci:
	method: bootstrap
	n: 400
	seed: 123
	cluster: item_id
filters:
	llms: ["gpt-4o-mini", "llama-3.1-8b-instruct"]
	categories: ["math", "code"]
```

Usage:

```bash
llmscorecard report results.json --config scorecard.yaml --out report.html
```

## CLI usage

```text
llmscorecard validate <results.(csv|json)>
llmscorecard summarize <results.(csv|json)>
llmscorecard ingest <results.csv> --out results.json
llmscorecard report <results.(csv|json)> --out report.html [--config scorecard.yaml]
```

Exit codes:
- `validate`: `0` ok, `2` invalid input
- `summarize`: `0` ok, `2` invalid input
- `ingest`: `0` ok, `2` invalid input
- `report`: `0` ok (warnings print to stderr but do not fail CI by default)

## Development

```bash
git clone https://github.com/<user>/llmscorecard
cd llmscorecard
pip install -e .
pip install -e ".[dev]"
pytest
ruff check .
```

Build:

```bash
python -m build
```

## Roadmap

- v0.0.3 schema validation + summarize
- v0.0.4 HTML report
- v0.0.5 regression ratings
- v0.0.6 uncertainty + P(A>B)
- v0.0.7 results.json artifacts
- v0.0.8 config
- v0.0.9 exports
- v0.1.0 stable schema + docs
- Future: adapters (`lm-eval-harness`, `lighteval`), mixed effects, IRT, hosted leaderboard generator

## Contributing

Small, reviewable PRs win. Please include tests where they fit.

```bash
pytest
ruff check .
```

If you’re changing schemas or rating models, include a minimal fixture and expected artifacts.

## License

MIT. See `LICENSE`.
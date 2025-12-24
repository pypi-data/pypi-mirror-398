# praevisio

**AI governance through verifiable promises** — a Python CLI that turns governance requirements into repeatable checks, CI gates, and replayable audit artifacts.

Praevisio evaluates a **promise** (a claim about your system) using deterministic **evidence** (today: `pytest` + `semgrep`), computes **credence** via ABDUCTIO, and emits an **audit trail** you can replay.

- White paper (source of truth): `docs/white-paper.md` (rendered by Sphinx)
- Tutorials (learn‑by‑doing): `docs/tutorials/`
- Sandbox / governed repo to experiment with: https://github.com/Promise-Foundation/praevisio-lab

---

## Choose your path

- **Developer (Tier 1):** “Will this commit be blocked, and what do I fix?”
  - Start with: Tutorials 1–3 (`docs/tutorials/01-logging-basics.md`, `02-static-analysis.md`, `03-branch-policy.md`)
- **Governance engineer / compliance (Tier 2):** “What promise are we enforcing, and what evidence supports it?”
  - Focus: promise files + `.praevisio.yaml` + CI artifacts (`.praevisio/runs/**`)
- **Power user / auditor (Tier 3):** “Can I replay the decision later and inspect integrity?”
  - Focus: `audit.json`, `manifest.json`, `praevisio replay-audit`

---

## What is a “verifiable promise”?

A **promise** is a machine‑checkable claim defined in your repo:

- `governance/promises/<promise_id>.yaml`

Praevisio evaluates that promise by collecting evidence and producing artifacts:

```
repo/
├─ governance/promises/<promise_id>.yaml     # the claim
├─ tests/                                   # procedural evidence (pytest)
├─ governance/evidence/semgrep_rules.yaml   # observational evidence (semgrep)
└─ .praevisio/runs/<run_id>/                 # audit bundle (generated)
   ├─ evidence/pytest.json
   ├─ evidence/semgrep.json
   ├─ audit.json
   └─ manifest.json                         # artifacts + SHA-256 hashes + metadata
```

Key terms:

- **Evidence:** artifacts produced by deterministic tools (pytest + semgrep today).
- **Credence:** probability‑like support that the promise holds given evidence.
- **Audit:** replayable trace of how credence was computed.
- **Manifest:** inventory of artifacts with SHA‑256 hashes for integrity review.
- **Gate:** a policy decision (pass/fail) based on credence + thresholds.

---

## Requirements (current release)

Praevisio is repo‑local: it runs against *your governed repository* and shells out to tools there.

- Python (recommended: 3.11+)
- `pytest` available in the governed repo (if you set `pytest_targets`)
- `semgrep` CLI available on `PATH` (if you set `semgrep_rules_path`)

Tutorials 4+ use optional tooling (e.g., Promptfoo) **inside pytest**. Those are not base requirements; they’re tutorial‑specific patterns.

---

## Install (PyPI)

```bash
pip install praevisio
```

Verify:

```bash
praevisio version
```

---

## 10‑minute quickstart (use the sandbox repo)

If you want a ready‑made governed repository, use:
https://github.com/Promise-Foundation/praevisio-lab

Typical flow inside a governed repo:

1) Add a promise file: `governance/promises/<id>.yaml`  
2) Add evidence: tests + (optionally) Semgrep rules  
3) Add config: `.praevisio.yaml`  
4) Run:

```bash
praevisio evaluate-commit . --config .praevisio.yaml --json
```

You’ll get:

- credence + verdict
- artifact paths for `audit.json` and `manifest.json`
- evidence summaries and stable references (`pytest:sha256:…`, `semgrep:sha256:…`)

---

## Quickstart: scaffold config

Create a default `.praevisio.yaml`:

```bash
praevisio install --config-path .praevisio.yaml
```

This writes a starter configuration you can customize.

---

## CI quickstart (GitHub Actions)

This is a minimal CI gate that:

- runs Praevisio
- writes a JSON report
- uploads audit artifacts for review

```yaml
name: Praevisio Governance Gate

on:
  pull_request:
    branches: [main]

jobs:
  governance-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # If you use Semgrep evidence, ensure Semgrep is installed on the runner.
      # - run: pip install semgrep

      - name: Install Praevisio
        run: |
          python -m pip install --upgrade pip
          pip install praevisio

      - name: Run governance gate
        run: |
          praevisio ci-gate . \
            --severity high \
            --fail-on-violation \
            --output logs/ci-gate-report.json \
            --config .praevisio.yaml

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: praevisio-run
          path: |
            logs/ci-gate-report.json
            .praevisio/runs/**
```

---

## What the CI report contains

`logs/ci-gate-report.json` contains (at minimum):

- promise id, credence, verdict
- threshold + severity
- artifact paths + hashes (audit + manifest)

This is designed so reviewers can:

- inspect evidence artifacts
- replay the audit deterministically

---

## Local workflows

Evaluate a repo (JSON output):

```bash
praevisio evaluate-commit . --config .praevisio.yaml --json
```

Replay the most recent audit:

```bash
praevisio replay-audit --latest --json
```

Show a stored run (manifest + artifacts):

```bash
praevisio show-run <run_id> --runs-dir .praevisio/runs
```

Install a pre‑commit gate:

```bash
praevisio install-hooks
```

This writes `.git/hooks/pre-commit` to invoke `praevisio pre-commit`.

---

## Configuration: .praevisio.yaml

The configuration binds a promise to evidence sources and gate policy.

Minimal example:

```yaml
evaluation:
  promise_id: llm-input-logging
  threshold: 0.95
  severity: high

  pytest_targets:
    - tests/test_logging.py

  semgrep_rules_path: governance/evidence/semgrep_rules.yaml
  semgrep_callsite_rule_id: llm-call-site
  semgrep_violation_rule_id: llm-call-must-log

  run_dir: .praevisio/runs

  thresholds:
    high: 0.95
    medium: 0.90

hooks: []
```

Notes:

- Severity selects the threshold from `evaluation.thresholds[severity]` when present.
- If `pytest_targets` is empty, tests are considered skipped and credence is penalized (see Tutorial 1).
- If Semgrep is configured but the rules file is missing or invalid, evaluation can return error.

---

## Promise files: governance/promises/*.yaml

Example:

```yaml
id: llm-input-logging
version: 0.1.0
domain: /llm/observability
statement: All LLM API calls must log input prompts.
critical: true
success_criteria:
  credence_threshold: 0.95
  evidence_types:
    - procedural
    - pattern
parameters: {}
stake:
  credits: 0
```

Conventions:

- The promise describes what must be true.
- Thresholds / severity belong in `.praevisio.yaml` (policy), not in promise YAML.

---

## Evidence and audit artifacts

Each run produces a directory under `.praevisio/runs/<run_id>/` with:

- `evidence/pytest.json` — pytest targets, args, exit code, errors
- `evidence/semgrep.json` — rule ids, coverage metrics, violations, findings
- `audit.json` — ABDUCTIO audit trace for deterministic replay
- `manifest.json` — artifacts + SHA‑256 hashes + run metadata (versions, UTC timestamp, ABDUCTIO config)

These artifacts are intended to be uploaded from CI and reviewed like any other governance record.

---

## Security & data handling

Praevisio writes governance artifacts to disk. Treat them as audit records.

Do not store secrets in `.praevisio.yaml` or promise YAML files.

Evidence artifacts may include:

- file paths, rule ids, and snippets depending on tool output (e.g., Semgrep findings)
- test metadata and errors

If your organization logs prompts as part of governance:

- redact before writing, and keep raw prompts out of CI artifacts unless explicitly approved

Praevisio provides tamper‑evidence (hashes in a manifest), not hardware‑backed attestation.

---

## Tutorials (canonical learning path)

All tutorials live under `docs/tutorials/`:

- Logging & credence (ABDUCTIO) — end‑to‑end evaluation + replay
- Static analysis that scales — Semgrep coverage/violations as evidence
- CI gate & branch policy — enforce thresholds in CI + artifact upload
- Red‑teaming via pytest — run tools (Promptfoo) inside pytest, gate on policy
- Prompt injection defenses — enforce boundary wiring + effectiveness in tests
- Privacy protection — PII redaction tests and gating
- Third‑party risk — enforce approvals/expiry via repo‑local registry + tests

If you want a guided sandbox, start with:
https://github.com/Promise-Foundation/praevisio-lab

---

## Architecture (short)

Praevisio is layered:

- Domain: core concepts (Promise, EvaluationResult, ports)
- Application: orchestration (evaluation + gates)
- Infrastructure: adapters (Semgrep, subprocess pytest, YAML loaders, evidence store)
- Presentation: Typer CLI (praevisio)

The CLI is intentionally thin: commands map to application services so the engine can be embedded later.

---

## Development

### Quickstart (uv)

Install uv: https://docs.astral.sh/uv/

Create venv + install dependencies:

```bash
uv venv
uv sync --all-groups
```

Build docs:

```bash
uv run sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html`.

### Alternative (pip/venv)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
make -C docs html
```

### BDD (Behave)

```bash
uv sync --group dev
uv run behave -f progress
```

---

## Roadmap (planned)

- Multi‑promise evaluation and per‑promise gating
- Collector plugins beyond pytest/semgrep (structured evidence ingestion)
- Calibrated evidence weighting and tuning guides
- Stronger integrity primitives (signing / provenance bindings)

---

## Contributing

- Keep changes small and outcome‑focused.
- Update docs alongside code changes.
- Prefer tests that exercise the CLI surface area.

---

## License

TBD by the repository owner.

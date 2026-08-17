# Contributing

Thanks for taking a look. This is a personal portfolio project, but the workflow
below is what I follow and what CI enforces.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
make install
pre-commit install   # optional but recommended
```

## Before opening a PR

```bash
make fmt          # ruff format + autofix
make lint         # ruff check
make cov          # unit tests + coverage
make tf-fmt       # terraform fmt -check
make tf-validate  # terraform validate
```

CI (`.github/workflows/ci.yml`) runs lint + unit tests, `terraform fmt/validate`,
and a security stage (gitleaks secret scan, `pip-audit`, `tfsec`). All must pass.

## Conventions

- **Python**: ruff-formatted, 100-col lines, typed where it helps. Keep the
  AWS/LLM imports lazy (inside functions) so modules stay importable in tests
  without the full stack installed — see the pattern in `src/agent/athena.py`.
- **Terraform**: one concern per module under `infra/modules/`. Keep resources
  least-privilege; never widen an IAM policy to `*` without a comment saying why.
- **Secrets**: never commit real credentials or resource endpoints. `.env` is
  gitignored; `.env.example` documents the variables.
- **Tests**: cover the risky, deterministic parts (the SQL read-only guard, the
  chunker, normalization, schema validation). AWS-touching paths go under
  `tests/integration/` and are allowed to require deployed infra.

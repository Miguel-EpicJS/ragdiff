# Release and rollback

## Build the release artifact

```bash
uv sync --locked --extra dev
uv build
```

The `dist/` directory contains the Python wheel and source archive. The Docker image must be built from the same Git tag and published with an immutable digest:

```bash
docker build --tag ragdiff:0.1.0 .
```

## Deploying the AWS topology

1. Review `infra/aws/staging.tfvars.example` and provide an approved immutable image URI.
2. Run Terraform from `infra/aws` with an account-specific backend and credentials.
3. Run `terraform plan` and review network, ECS, RDS, secret, and IAM changes.
4. Apply only after cost and account approval.
5. Smoke test the `health_url` output.

The repository does not contain AWS credentials or a shared state backend. The staging configuration creates a private database and encrypted storage, but the generated database secret and Terraform state require organizational secret handling.

## Rollback

- Application: redeploy the previous immutable ECS task-definition image and verify `/health` and the comparison API.
- Evaluation policy: keep the previous release artifact available; deployment gates fail closed when reports are incomplete.
- Terraform: inspect the plan before reverting; use `terraform apply` for a reviewed rollback, not state deletion.
- Database: take a snapshot before destructive schema changes. Existing migrations are forward-only in the MVP; restore from snapshot for a destructive rollback.

## Release checklist

- [ ] quality checks pass (`ruff`, `mypy`, `pytest`);
- [ ] case-study and benchmark run from a clean environment;
- [ ] Docker health and non-root checks pass;
- [ ] Terraform `fmt`, `init -backend=false`, and `validate` pass;
- [ ] image vulnerability scan reviewed and findings documented;
- [ ] no credentials or private data appear in artifacts;
- [ ] release notes and known limitations are updated.

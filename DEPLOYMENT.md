# Deployment

## Local MVP deployment

1. Start with mock model (no GPU required): `docker compose up -d --build mock-model api`.
2. Verify `/health` and `/ready`.
3. Build and run VS Code extension.

## AWS deployment: single instance (default path)

No Terraform, no ECR, no CodeBuild, no multi-instance networking required. See [scripts/aws/README.md](scripts/aws/README.md) for full steps.

1. Launch one EC2 instance using AMI `Deep Learning Base AMI with Single CUDA (Ubuntu 24.04)`.
2. Connect via Session Manager, clone the repo, run [scripts/aws/bootstrap_single_instance.sh](scripts/aws/bootstrap_single_instance.sh).
3. Validate with mock model first, then switch to the real model:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml --profile gpu up -d --build vllm api
   ```
4. Keep the instance private; use SSM for all access instead of public inbound rules.

## Scaling up (only if actually needed)

- Split API and vLLM onto separate instances once GPU cost or independent scaling matters.
- Add ECR + a build pipeline once you need repeatable rebuilds without re-cloning on the box.
- Add a load balancer / IaC only once managing more than one instance by hand becomes painful.

## Release checklist

- Run API tests and lint.
- Verify extension compile.
- Verify health/ready endpoints.
- Verify sample task end-to-end.
- Confirm no public inbound rules beyond what's required for your test client.


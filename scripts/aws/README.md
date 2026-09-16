# AWS One-Click EC2 Deployment Scripts

These scripts support a near one-click deployment flow for the API + vLLM stack on a GPU EC2 instance.

## Files

- `one_click.env.example`: configuration template.
- `one_click.env`: ready-to-edit local config file.
- `build_and_push_ecr.sh`: builds and pushes API + vLLM images to ECR.
- `render_user_data.sh`: renders a concrete EC2 user-data script from env values.
- `user-data/bootstrap_gpu_agent.tpl.sh`: user-data template executed on first boot.

## Quick Start

1. Edit env file:

```bash
nano scripts/aws/one_click.env
```

Set `AWS_ACCOUNT_ID` to a 12-digit value before running scripts.

2. Build and push images:

```bash
bash scripts/aws/build_and_push_ecr.sh
```

3. Render user-data script:

```bash
bash scripts/aws/render_user_data.sh
```

4. Create/update an EC2 Launch Template:

- Use a GPU-ready AMI (Deep Learning AMI preferred)
- Use g4dn.2xlarge or larger
- Attach IAM instance profile with:
  - AmazonEC2ContainerRegistryReadOnly
  - AmazonSSMManagedInstanceCore
- Paste `scripts/aws/user-data/bootstrap_gpu_agent.sh` into User data

5. Launch instance from template and verify:

```bash
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/ready
```

## Notes

- vLLM is bound to localhost by default (`127.0.0.1`).
- API is exposed on host port from `API_PORT`.
- SQLite is used for simple startup; no external Postgres/Redis required for first run.

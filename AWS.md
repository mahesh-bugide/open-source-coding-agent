# AWS Deployment Notes

## Architecture (minimal, single instance)

One EC2 instance runs `mock-model` + `api` via Docker Compose. For real inference, the same instance (GPU type) also runs `vllm`. No ECS, ALB, RDS, ElastiCache, or Terraform required for this path.

```
Developer -> API (EC2, Docker Compose) -> vLLM (same EC2, GPU)
```

- API persists to SQLite (file-backed, no external DB needed).
- Cache falls back to in-memory automatically if Redis isn't present.
- vLLM has no public ingress — only reachable on `localhost` from the API container/process.

## One-time setup

- Launch instance from AMI `Deep Learning Base AMI with Single CUDA (Ubuntu 24.04)` — driver/CUDA/Docker/NVIDIA Container Toolkit preinstalled.
- IAM role: `AmazonSSMManagedInstanceCore` only.
- Security group: no public inbound rules; use Session Manager for access.

## Deployment steps

See [scripts/aws/README.md](scripts/aws/README.md) for the full step-by-step, including [scripts/aws/bootstrap_single_instance.sh](scripts/aws/bootstrap_single_instance.sh).

## Scaling beyond one instance (only when actually needed)

- **Two instances**: split API (CPU, e.g. `t3.large`) from vLLM (GPU, e.g. `g4dn.2xlarge`). Requires a security group rule allowing the API instance to reach the LLM instance's port privately.
- **Repeatable builds**: add ECR + a build pipeline (e.g. CodeBuild) once rebuilding directly on the instance each time becomes inconvenient.
- **Multiple instances / HA**: add a load balancer and infrastructure-as-code once managing hosts by hand becomes error-prone.

## Cost-heavy resources

- GPU instance (`g4dn.xlarge`/`g4dn.2xlarge`) — the only significant recurring cost in this minimal setup.


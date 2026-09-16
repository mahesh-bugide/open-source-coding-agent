# AWS Infrastructure Notes

Terraform root: [infrastructure/terraform](infrastructure/terraform)

## Resources included

- VPC, public/private subnets
- Security groups with restricted east-west traffic
- ALB
- ECS cluster + services
- ECR repositories
- Private GPU EC2 autoscaling group for vLLM
- RDS PostgreSQL
- ElastiCache Redis
- S3 artifacts bucket
- CloudWatch log groups
- Secrets Manager secrets

## Traffic policy

- VS Code/clients -> ALB (public)
- ALB -> API (private)
- API -> Agent (private)
- Agent -> vLLM (private)
- API/Agent -> RDS/Redis (private)

vLLM has no public ingress.

## Cost-heavy resources

- GPU instance (`g6e.2xlarge`) for inference
- RDS instance and storage
- NAT/data transfer if enabled in future revisions
- CloudWatch log retention growth

## Terraform usage

```bash
cd infrastructure/terraform
terraform init
terraform validate
terraform plan -var-file=environments/dev/terraform.tfvars
```

Do not commit real secrets in tfvars.

## One-click EC2 path

For an admin-light deployment path that avoids Terraform changes, use [scripts/aws/README.md](scripts/aws/README.md).

Required one-time setup:

- ECR repositories for API and vLLM images
- EC2 instance profile with `AmazonEC2ContainerRegistryReadOnly` and `AmazonSSMManagedInstanceCore`
- GPU-ready AMI for stable NVIDIA runtime bootstrapping

Operational flow:

1. Push images with [scripts/aws/build_and_push_ecr.sh](scripts/aws/build_and_push_ecr.sh).
2. Render user-data from [scripts/aws/user-data/bootstrap_gpu_agent.tpl.sh](scripts/aws/user-data/bootstrap_gpu_agent.tpl.sh) using [scripts/aws/render_user_data.sh](scripts/aws/render_user_data.sh).
3. Paste the rendered script into a Launch Template and launch a new instance.

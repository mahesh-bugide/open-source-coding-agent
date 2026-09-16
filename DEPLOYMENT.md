# Deployment

## Local MVP deployment

1. Start PostgreSQL, Redis, mock model.
2. Start API service with `MODEL_MODE=mock`.
3. Build and run VS Code extension.

## AWS deployment approach

1. Build and push images to ECR.
2. Apply Terraform in [infrastructure/terraform](infrastructure/terraform).
3. Deploy ECS services (API + agent) in private subnets.
4. Deploy vLLM on private GPU EC2 capacity.
5. Expose only ALB publicly; keep vLLM private.

## AWS one-click EC2 deployment (no Terraform changes)

Use the scripts in [scripts/aws/README.md](scripts/aws/README.md) to prepare images and launch a GPU EC2 host from a Launch Template.

1. Edit [scripts/aws/one_click.env](scripts/aws/one_click.env) (or copy from [scripts/aws/one_click.env.example](scripts/aws/one_click.env.example)) and set values.
2. Run `bash scripts/aws/build_and_push_ecr.sh`.
3. Run `bash scripts/aws/render_user_data.sh`.
4. Paste [scripts/aws/user-data/bootstrap_gpu_agent.sh](scripts/aws/user-data/bootstrap_gpu_agent.sh) into Launch Template user data.
5. Launch an instance from that template.

This path is useful when network primitives are pre-existing and cannot be changed quickly.

## Release checklist

- Run API tests and lint.
- Verify extension compile.
- Verify health/ready endpoints.
- Verify sample task end-to-end.
- Validate security groups and secret injection.

output "alb_dns_name" {
  value = aws_lb.api.dns_name
}

output "api_ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "agent_ecr_repository_url" {
  value = aws_ecr_repository.agent.repository_url
}

output "vllm_ecr_repository_url" {
  value = aws_ecr_repository.vllm.repository_url
}

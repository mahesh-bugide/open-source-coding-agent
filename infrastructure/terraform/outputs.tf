output "alb_dns_name" {
  value = module.compute.alb_dns_name
}

output "api_ecr_repository_url" {
  value = module.compute.api_ecr_repository_url
}

output "agent_ecr_repository_url" {
  value = module.compute.agent_ecr_repository_url
}

output "vllm_ecr_repository_url" {
  value = module.compute.vllm_ecr_repository_url
}

output "s3_bucket_name" {
  value = module.data.s3_bucket_name
}

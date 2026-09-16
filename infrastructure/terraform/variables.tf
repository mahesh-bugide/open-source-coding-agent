variable "project_name" {
  type    = string
  default = "enterprise-ai-coding-agent"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "api_image" {
  type    = string
  default = "REPLACE_WITH_ECR_API_IMAGE"
}

variable "agent_image" {
  type    = string
  default = "REPLACE_WITH_ECR_AGENT_IMAGE"
}

variable "vllm_image" {
  type    = string
  default = "REPLACE_WITH_ECR_VLLM_IMAGE"
}

variable "db_username" {
  type    = string
  default = "agent"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "dev_api_key" {
  type      = string
  sensitive = true
}

variable "gpu_instance_type" {
  type    = string
  default = "g6e.2xlarge"
}

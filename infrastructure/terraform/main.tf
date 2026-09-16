locals {
  name_prefix = "${var.project_name}-${var.environment}"
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

module "network" {
  source             = "./modules/network"
  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  tags               = local.tags
}

module "security" {
  source            = "./modules/security"
  name_prefix       = local.name_prefix
  vpc_id            = module.network.vpc_id
  vpc_cidr          = var.vpc_cidr
  private_subnet_ids = module.network.private_subnet_ids
  tags              = local.tags
}

module "data" {
  source             = "./modules/data"
  name_prefix        = local.name_prefix
  private_subnet_ids = module.network.private_subnet_ids
  rds_sg_id          = module.security.rds_sg_id
  redis_sg_id        = module.security.redis_sg_id
  db_username        = var.db_username
  db_password        = var.db_password
  tags               = local.tags
}

module "compute" {
  source               = "./modules/compute"
  name_prefix          = local.name_prefix
  vpc_id               = module.network.vpc_id
  public_subnet_ids    = module.network.public_subnet_ids
  private_subnet_ids   = module.network.private_subnet_ids
  alb_sg_id            = module.security.alb_sg_id
  api_sg_id            = module.security.api_sg_id
  agent_sg_id          = module.security.agent_sg_id
  vllm_sg_id           = module.security.vllm_sg_id
  api_image            = var.api_image
  agent_image          = var.agent_image
  vllm_image           = var.vllm_image
  gpu_instance_type    = var.gpu_instance_type
  redis_url            = module.data.redis_url
  postgres_dsn         = module.data.postgres_dsn
  model_base_url       = "http://vllm.internal:8001/v1"
  model_name           = "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
  dev_api_key          = var.dev_api_key
  tags                 = local.tags
}

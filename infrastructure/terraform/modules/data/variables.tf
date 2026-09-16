variable "name_prefix" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "rds_sg_id" { type = string }
variable "redis_sg_id" { type = string }
variable "db_username" { type = string }
variable "db_password" { type = string }
variable "tags" { type = map(string) }

output "s3_bucket_name" {
  value = aws_s3_bucket.artifacts.bucket
}

output "postgres_dsn" {
  value = "postgresql+psycopg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.address}:5432/agentdb"
}

output "redis_url" {
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
}

output "api_url" {
  description = "Public URL for the RAGDiff API."
  value       = "http://${aws_lb.api.dns_name}"
}

output "health_url" {
  description = "Health endpoint for smoke tests."
  value       = "http://${aws_lb.api.dns_name}/health"
}

output "database_endpoint" {
  description = "Private PostgreSQL endpoint for operational diagnostics."
  value       = aws_db_instance.main.address
}

output "cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

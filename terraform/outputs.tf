# Output values
output "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "website_url" {
  description = "Website URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_lambda_function_name" {
  description = "Name of the API Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_reader_endpoint" {
  description = "RDS PostgreSQL read replica endpoint"
  value       = aws_db_instance.replica.endpoint
  sensitive   = true
}

# Parameter Store outputs
output "db_parameter_prefix" {
  description = "Parameter Store prefix for database credentials"
  value       = "/${var.project_name}/database"
}

output "db_username_parameter" {
  description = "Parameter Store name for database username"
  value       = aws_ssm_parameter.db_username.name
}

output "db_password_parameter" {
  description = "Parameter Store name for database password"
  value       = aws_ssm_parameter.db_password.name
  sensitive   = true
}

output "db_host_parameter" {
  description = "Parameter Store name for database host"
  value       = aws_ssm_parameter.db_host.name
}

output "db_port_parameter" {
  description = "Parameter Store name for database port"
  value       = aws_ssm_parameter.db_port.name
}

output "db_name_parameter" {
  description = "Parameter Store name for database name"
  value       = aws_ssm_parameter.db_name.name
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}

output "rotation_lambda_function_name" {
  description = "Name of the password rotation Lambda function"
  value       = aws_lambda_function.db_rotation.function_name
}

# Cost monitoring outputs
output "cost_monitoring_dashboard_url" {
  description = "CloudWatch dashboard URL for cost monitoring"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cost_monitoring.dashboard_name}"
}

output "monthly_budget_name" {
  description = "Name of the monthly budget for cost monitoring"
  value       = aws_budgets_budget.monthly_budget.name
}

output "cost_alert_topic_arn" {
  description = "SNS topic ARN for cost alerts"
  value       = aws_sns_topic.cost_alerts.arn
}

output "nat_type" {
  description = "Type of NAT solution being used (gateway or fck-nat)"
  value       = var.use_fck_nat ? "fck-nat EC2 instance" : "NAT Gateway"
}

output "fck_nat_instance_ip" {
  description = "Public IP of fck-nat instance (if used)"
  value       = var.use_fck_nat ? aws_eip.fck_nat[0].public_ip : null
}
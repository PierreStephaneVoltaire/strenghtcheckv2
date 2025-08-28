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
  value       = aws_api_gateway_deployment.main.invoke_url
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
  description = "RDS PostgreSQL read replica endpoint (if exists)"
  value       = length(aws_db_instance.replica) > 0 ? aws_db_instance.replica[0].endpoint : aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}
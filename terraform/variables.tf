# Core variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ca-central-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "powerlifting-analytics"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

# Database variables
variable "db_master_username" {
  description = "Master username for the Database cluster"
  type        = string
  default     = "powerlifting_admin"
}

variable "password_rotation_days" {
  description = "Number of days between password rotations"
  type        = number
  default     = 30
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "powerlifting"
}



# RDS configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"  # Free tier eligible
}

variable "db_allocated_storage" {
  description = "Initial storage allocation in GB"
  type        = number
  default     = 20  # Free tier: 20GB
}

variable "db_max_allocated_storage" {
  description = "Maximum storage allocation in GB (0 = no autoscaling)"
  type        = number
  default     = 100
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights for RDS"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Number of days to retain backups (0 = no backups)"
  type        = number
  default     = 0  # No backups for cost savings
}


# Lambda configuration
variable "lambda_memory_size" {
  description = "Memory size for Lambda function (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (seconds)"
  type        = number
  default     = 30
}

variable "rotation_lambda_timeout" {
  description = "Timeout for password rotation Lambda function (seconds)"
  type        = number
  default     = 300
}

# Cost monitoring variables
variable "use_fck_nat" {
  description = "Use fck-nat EC2 instance instead of NAT Gateway for cost savings"
  type        = bool
  default     = true
}

variable "fck_nat_instance_type" {
  description = "Instance type for fck-nat (t3.nano, t3.micro, t3.small)"
  type        = string
  default     = "t3.micro"
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "engineering"
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD for cost alerts"
  type        = number
  default     = 50
}

variable "cost_alert_emails" {
  description = "List of email addresses for cost alerts"
  type        = list(string)
  default     = []
}
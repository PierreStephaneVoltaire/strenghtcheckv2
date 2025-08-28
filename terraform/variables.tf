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
  description = "Master username for the Aurora cluster"
  type        = string
  default     = "powerlifting_admin"
}

variable "db_master_password" {
  description = "Master password for the Aurora cluster"
  type        = string
  sensitive   = true
  validation {
    condition     = length(var.db_master_password) >= 8
    error_message = "Database password must be at least 8 characters long."
  }
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "powerlifting"
}

# Network variables
variable "vpc_id" {
  description = "VPC ID for resources"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for RDS"
  type        = list(string)
  default     = []
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for Lambda (if needed)"
  type        = list(string)
  default     = []
}

# Create VPC if not provided
variable "create_vpc" {
  description = "Whether to create a new VPC"
  type        = bool
  default     = true
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

variable "create_read_replica" {
  description = "Create a read replica for the database"
  type        = bool
  default     = false
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
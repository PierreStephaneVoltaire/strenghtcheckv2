# Security Group for RDS PostgreSQL
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Security group for RDS PostgreSQL instance"
  vpc_id      = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "Allow Lambda to connect to RDS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-rds-sg"
  })
}

# DB Subnet Group for RDS
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-subnet-group"
  subnet_ids = local.private_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-subnet-group"
  })
}

# Random password for RDS master user
resource "random_password" "db_password" {
  count   = var.db_master_password == "" ? 1 : 0
  length  = 16
  special = true
}

# AWS Secrets Manager secret for database credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}-db-credentials"
  description = "Database credentials for Aurora cluster"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_master_username
    password = var.db_master_password != "" ? var.db_master_password : random_password.db_password[0].result
    host     = aws_db_instance.main.endpoint
    port     = 5432
    database = var.db_name
  })
}

# RDS Parameter Group for PostgreSQL
resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${var.project_name}-postgres-pg"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # Log queries taking longer than 1 second
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = local.common_tags
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-postgres"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class
  
  # Database configuration
  db_name  = var.db_name
  username = var.db_master_username
  password = var.db_master_password != "" ? var.db_master_password : random_password.db_password[0].result
  
  # Storage configuration - optimized for cost
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type         = "gp2"  # Cheaper than gp3
  storage_encrypted    = false  # Disable encryption to reduce cost
  
  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  
  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name
  
  # Cost optimization settings
  backup_retention_period = var.backup_retention_period
  backup_window          = "03:00-04:00"  # Low traffic time
  maintenance_window     = "sun:04:00-sun:05:00"  # Low traffic time
  skip_final_snapshot    = true
  deletion_protection    = false
  
  # Performance and monitoring
  performance_insights_enabled          = var.enable_performance_insights
  performance_insights_retention_period = var.enable_performance_insights ? 7 : 0
  monitoring_interval                   = 0  # Disable enhanced monitoring for cost
  enabled_cloudwatch_logs_exports       = var.environment == "prod" ? ["postgresql"] : []

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-postgres"
  })

  depends_on = [
    aws_cloudwatch_log_group.rds_logs
  ]
}

# Optional Read Replica for production (only if needed)
resource "aws_db_instance" "replica" {
  count = var.environment == "prod" && var.create_read_replica ? 1 : 0
  
  identifier = "${var.project_name}-postgres-replica"
  
  # Read replica configuration
  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = var.db_instance_class
  
  # Network configuration  
  publicly_accessible = false
  
  # Performance monitoring
  performance_insights_enabled = false  # Keep cost low
  monitoring_interval          = 0
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-postgres-replica"
    Type = "Read Replica"
  })
}

# CloudWatch Log Groups for RDS (only if needed)
resource "aws_cloudwatch_log_group" "rds_logs" {
  count             = var.environment == "prod" ? 1 : 0
  name              = "/aws/rds/instance/${var.project_name}-postgres/postgresql"
  retention_in_days = 7

  tags = local.common_tags
}
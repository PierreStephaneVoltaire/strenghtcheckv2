# Security Group for RDS PostgreSQL
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg-${local.resource_suffix}"
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
  name       = "${var.project_name}-subnet-group-${local.resource_suffix}"
  subnet_ids = local.private_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-subnet-group"
  })
}

# Random password for RDS master user
resource "random_password" "db_password" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store database credentials in Parameter Store
resource "aws_ssm_parameter" "db_username" {
  name  = "/${var.project_name}/database/username"
  type  = "String"
  value = var.db_master_username

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/database/password"
  type  = "SecureString"
  value = random_password.db_password.result

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_host" {
  name  = "/${var.project_name}/database/host"
  type  = "String"
  value = aws_db_instance.main.endpoint

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_port" {
  name  = "/${var.project_name}/database/port"
  type  = "String"
  value = "5432"

  tags = local.common_tags
}

resource "aws_ssm_parameter" "db_name" {
  name  = "/${var.project_name}/database/name"
  type  = "String"
  value = var.db_name

  tags = local.common_tags
}

# Secrets Manager secret for rotation (required by RDS)
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}-db-credentials-${local.resource_suffix}"
  description = "Database credentials for automatic rotation"
  
  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_master_username
    password = random_password.db_password.result
    engine   = "postgres"
    host     = aws_db_instance.main.endpoint
    port     = 5432
    dbname   = var.db_name
    dbInstanceIdentifier = aws_db_instance.main.identifier
  })
}

# RDS Parameter Group for PostgreSQL
resource "aws_db_parameter_group" "main" {
  family = "postgres17"
  name   = "${var.project_name}-postgres-pg-${local.resource_suffix}"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000" # Log queries taking longer than 1 second
  }

  tags = local.common_tags
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-postgres-${local.resource_suffix}"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "17.6"
  instance_class = var.db_instance_class
  
  # Database configuration
  db_name  = var.db_name
  username = var.db_master_username
  password = random_password.db_password.result
  
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
  enabled_cloudwatch_logs_exports       = ["postgresql"]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-postgres"
  })

  depends_on = [
    aws_cloudwatch_log_group.rds_logs
  ]
}

# Read Replica for production
resource "aws_db_instance" "replica" {
  
  identifier = "${var.project_name}-postgres-replica-${local.resource_suffix}"
  
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

# CloudWatch Log Groups for RDS
resource "aws_cloudwatch_log_group" "rds_logs" {
  name              = "/aws/rds/instance/${var.project_name}-postgres-${local.resource_suffix}/postgresql"
  retention_in_days = 7

  tags = local.common_tags
}

# CloudWatch Log Group for Lambda rotation function
resource "aws_cloudwatch_log_group" "rotation_lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-db-rotation-${local.resource_suffix}"
  retention_in_days = 14

  tags = local.common_tags
}

# IAM role for Lambda rotation function
resource "aws_iam_role" "rotation_lambda_role" {
  name = "${var.project_name}-db-rotation-lambda-role-${local.resource_suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for Lambda rotation function
resource "aws_iam_role_policy" "rotation_lambda_policy" {
  name = "${var.project_name}-db-rotation-lambda-policy-${local.resource_suffix}"
  role = aws_iam_role.rotation_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = aws_secretsmanager_secret.db_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:PutParameter"
        ]
        Resource = [
          aws_ssm_parameter.db_password.arn,
          aws_ssm_parameter.db_username.arn,
          aws_ssm_parameter.db_host.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:ModifyDBInstance",
          "rds:DescribeDBInstances"
        ]
        Resource = aws_db_instance.main.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda layer for psycopg2
resource "aws_lambda_layer_version" "psycopg2_layer" {
  filename   = "psycopg2_layer.zip"
  layer_name = "${var.project_name}-psycopg2-layer-${local.resource_suffix}"

  compatible_runtimes = ["python3.11"]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# Create psycopg2 layer package

# Lambda function for password rotation
resource "aws_lambda_function" "db_rotation" {
  filename      = "rotation_lambda.zip"
  function_name = "${var.project_name}-db-rotation-${local.resource_suffix}"
  role          = aws_iam_role.rotation_lambda_role.arn
  handler       = "index.lambda_handler"
  runtime       = "python3.11"
  timeout       = var.rotation_lambda_timeout
  
  layers = [aws_lambda_layer_version.psycopg2_layer.arn]

  vpc_config {
    subnet_ids         = local.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${var.aws_region}.amazonaws.com"
      SSM_PARAMETER_PREFIX     = "/${var.project_name}/database"
      RDS_INSTANCE_IDENTIFIER  = aws_db_instance.main.identifier
    }
  }

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  tags = local.common_tags
}


# Permission for Secrets Manager to invoke Lambda
resource "aws_lambda_permission" "allow_secretsmanager" {
  statement_id  = "AllowExecutionFromSecretsManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.db_rotation.function_name
  principal     = "secretsmanager.amazonaws.com"
}

# Automatic rotation configuration
resource "aws_secretsmanager_secret_rotation" "db_rotation" {
  secret_id           = aws_secretsmanager_secret.db_credentials.id
  rotation_lambda_arn = aws_lambda_function.db_rotation.arn
  
  rotation_rules {
    automatically_after_days = var.password_rotation_days
  }

  depends_on = [aws_lambda_permission.allow_secretsmanager]
}
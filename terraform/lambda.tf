# Security Group for Lambda
resource "aws_security_group" "lambda" {
  name        = "${var.project_name}-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = local.vpc_id

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.selected.cidr_block]
    description = "Allow connection to RDS"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS outbound"
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP outbound"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-lambda-sg"
  })
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"
  tags = local.common_tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# IAM policy for Lambda function
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

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
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AttachNetworkInterface",
          "ec2:DetachNetworkInterface"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.db_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBClusters",
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Layer for psycopg2 and numpy
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "lambda-layer-dependencies.zip"
  layer_name          = "${var.project_name}-dependencies"
  compatible_runtimes = ["python3.9"]
  description         = "Dependencies layer for psycopg2 and numpy"

  # This would be created by your CI/CD pipeline
  lifecycle {
    create_before_destroy = true
  }
}

# Lambda function for API
resource "aws_lambda_function" "api" {
  filename         = "api-function.zip"
  function_name    = "${var.project_name}-api"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  layers = [aws_lambda_layer_version.dependencies.arn]

  vpc_config {
    subnet_ids         = local.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      WRITE_DB_HOST     = aws_db_instance.main.endpoint
      READ_DB_HOST      = length(aws_db_instance.replica) > 0 ? aws_db_instance.replica[0].endpoint : aws_db_instance.main.endpoint
      DB_NAME           = var.db_name
      DB_USER           = var.db_master_username
      DB_SECRET_ARN     = aws_secretsmanager_secret.db_credentials.arn
      ALLOWED_ORIGIN    = aws_cloudfront_distribution.main.domain_name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = local.common_tags

  # This assumes you have a zip file ready - you would need to create this
  # In practice, you would build and upload this as part of your CI/CD pipeline
}

# CloudWatch Log Group for API Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-api"
  retention_in_days = 7
  tags              = local.common_tags
}

# Data sources for VPC info
data "aws_vpc" "selected" {
  id = local.vpc_id
}
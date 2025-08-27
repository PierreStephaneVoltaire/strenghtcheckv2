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
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.data.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
        ]
      }
    ]
  })
}

# Lambda function for data processing
resource "aws_lambda_function" "data_processor" {
  filename         = "data_processor.zip"
  function_name    = "${var.project_name}-data-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900 # 15 minutes
  memory_size     = 2048

  environment {
    variables = {
      DATA_BUCKET = aws_s3_bucket.data.bucket
    }
  }

  tags = local.common_tags

  # This assumes you have a zip file ready - you would need to create this
  # In practice, you would build and upload this as part of your CI/CD pipeline
}

# EventBridge rule for scheduled data updates
resource "aws_cloudwatch_event_rule" "data_update_schedule" {
  name                = "${var.project_name}-data-update"
  description         = "Schedule for updating powerlifting data"
  schedule_expression = "cron(0 6 * * ? *)" # Daily at 6 AM UTC
  tags                = local.common_tags
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.data_update_schedule.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.data_processor.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.data_update_schedule.arn
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.data_processor.function_name}"
  retention_in_days = 30
  tags              = local.common_tags
}
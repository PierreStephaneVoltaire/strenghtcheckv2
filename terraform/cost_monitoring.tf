# Cost and Billing Monitoring

# SNS Topic for cost alerts
resource "aws_sns_topic" "cost_alerts" {
  name = "${var.project_name}-cost-alerts-${local.resource_suffix}"
  tags = local.common_tags
}

# SNS subscriptions for cost alert emails
resource "aws_sns_topic_subscription" "cost_alert_emails" {
  count     = length(var.cost_alert_emails)
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.cost_alert_emails[count.index]
}

# Budget for cost monitoring
resource "aws_budgets_budget" "monthly_budget" {
  name         = "${var.project_name}-monthly-budget-${local.resource_suffix}"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_limit)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  time_period_start = formatdate("YYYY-MM-01_00:00", timestamp())

  cost_filter {
    name   = "TagKey"
    values = ["Project"]
  }
  
  cost_filter {
    name   = "TagValue"
    values = [var.project_name]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.cost_alert_emails
    subscriber_sns_topic_arns   = [aws_sns_topic.cost_alerts.arn]
  }

  notification {
    comparison_operator        = "GREATER_THAN" 
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.cost_alert_emails
    subscriber_sns_topic_arns   = [aws_sns_topic.cost_alerts.arn]
  }

  tags = local.common_tags
}

# Note: Cost Anomaly Detection requires AWS CLI/API or manual setup
# These resources are not available in standard Terraform AWS provider

# CloudWatch Dashboard for Cost Monitoring
resource "aws_cloudwatch_dashboard" "cost_monitoring" {
  dashboard_name = "${var.project_name}-cost-monitoring-${local.resource_suffix}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            [ "AWS/Billing", "EstimatedCharges", "Currency", "USD" ]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Estimated Monthly Charges"
          period  = 86400
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 6
        height = 6

        properties = {
          metrics = [
            [ "AWS/EC2", "RunningInstances" ],
            [ "AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "powerlifting-analytics-postgres-${local.resource_suffix}" ]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Resource Usage"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 6  
        width  = 6
        height = 6

        properties = {
          metrics = [
            [ "AWS/Lambda", "Invocations", "FunctionName", "powerlifting-analytics-api-${local.resource_suffix}" ],
            [ "AWS/Lambda", "Duration", "FunctionName", "powerlifting-analytics-api-${local.resource_suffix}" ]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Metrics"
          period  = 300
        }
      }
    ]
  })

  # CloudWatch dashboards don't support tags
}

# Cost allocation tags (automatically applied to all resources)
resource "aws_ce_cost_category" "project_cost_category" {
  name         = "${var.project_name}-costs-${local.resource_suffix}"
  rule_version = "CostCategoryExpression.v1"

  rule {
    value = "Infrastructure"
    rule {
      dimension {
        key           = "SERVICE"
        values        = ["Amazon Elastic Compute Cloud - Compute", "Amazon Virtual Private Cloud"]
        match_options = ["EQUALS"]
      }
    }
  }

  rule {
    value = "Database" 
    rule {
      dimension {
        key           = "SERVICE"
        values        = ["Amazon Relational Database Service"]
        match_options = ["EQUALS"]
      }
    }
  }

  rule {
    value = "Storage"
    rule {
      dimension {
        key           = "SERVICE"
        values        = ["Amazon Simple Storage Service"]
        match_options = ["EQUALS"]
      }
    }
  }

  rule {
    value = "Compute"
    rule {
      dimension {
        key           = "SERVICE"  
        values        = ["AWS Lambda"]
        match_options = ["EQUALS"]
      }
    }
  }

  tags = local.common_tags
}
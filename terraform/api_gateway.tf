# API Gateway for REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api"
  description = "API Gateway for powerlifting analytics"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# API Gateway Resource for /api
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "api"
}

# API Gateway Resource for /api/metadata
resource "aws_api_gateway_resource" "metadata" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "metadata"
}

# API Gateway Resource for /api/percentiles  
resource "aws_api_gateway_resource" "percentiles" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "percentiles"
}

# API Gateway Resource for /api/distribution
resource "aws_api_gateway_resource" "distribution" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "distribution"
}

# GET method for /api/metadata
resource "aws_api_gateway_method" "metadata_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.metadata.id
  http_method   = "GET"
  authorization = "NONE"
}

# GET method for /api/percentiles
resource "aws_api_gateway_method" "percentiles_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.percentiles.id
  http_method   = "GET"
  authorization = "NONE"
}

# GET method for /api/distribution
resource "aws_api_gateway_method" "distribution_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.distribution.id
  http_method   = "GET"
  authorization = "NONE"
}

# OPTIONS methods for CORS
resource "aws_api_gateway_method" "metadata_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.metadata.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "percentiles_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.percentiles.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "distribution_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.distribution.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda integrations
resource "aws_api_gateway_integration" "metadata_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.metadata.id
  http_method = aws_api_gateway_method.metadata_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_integration" "percentiles_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.percentiles.id
  http_method = aws_api_gateway_method.percentiles_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_api_gateway_integration" "distribution_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.distribution.id
  http_method = aws_api_gateway_method.distribution_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# CORS integrations
resource "aws_api_gateway_integration" "metadata_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.metadata.id
  http_method = aws_api_gateway_method.metadata_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "percentiles_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.percentiles.id
  http_method = aws_api_gateway_method.percentiles_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "distribution_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.distribution.id
  http_method = aws_api_gateway_method.distribution_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Method responses for GET methods
resource "aws_api_gateway_method_response" "metadata_get_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.metadata.id
  http_method = aws_api_gateway_method.metadata_get.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "percentiles_get_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.percentiles.id
  http_method = aws_api_gateway_method.percentiles_get.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "distribution_get_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.distribution.id
  http_method = aws_api_gateway_method.distribution_get.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

# Method responses for OPTIONS methods (CORS)
resource "aws_api_gateway_method_response" "metadata_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.metadata.id
  http_method = aws_api_gateway_method.metadata_options.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "percentiles_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.percentiles.id
  http_method = aws_api_gateway_method.percentiles_options.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "distribution_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.distribution.id
  http_method = aws_api_gateway_method.distribution_options.http_method
  status_code = "200"

  response_parameters  = {
    "Access-Control-Allow-Origin"  = true
    "Access-Control-Allow-Headers" = true
    "Access-Control-Allow-Methods" = true
  }
}

# Integration responses
resource "aws_api_gateway_integration_response" "metadata_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.metadata.id
  http_method = aws_api_gateway_method.metadata_options.http_method
  status_code = aws_api_gateway_method_response.metadata_options_200.status_code

  response_parameters  = {
    "Access-Control-Allow-Origin"  = "'*'"
    "Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

resource "aws_api_gateway_integration_response" "percentiles_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.percentiles.id
  http_method = aws_api_gateway_method.percentiles_options.http_method
  status_code = aws_api_gateway_method_response.percentiles_options_200.status_code

  response_parameters  = {
    "Access-Control-Allow-Origin"  = "'*'"
    "Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

resource "aws_api_gateway_integration_response" "distribution_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.distribution.id
  http_method = aws_api_gateway_method.distribution_options.http_method
  status_code = aws_api_gateway_method_response.distribution_options_200.status_code

  response_parameters  = {
    "Access-Control-Allow-Origin"  = "'*'"
    "Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.metadata_get,
    aws_api_gateway_integration.percentiles_get,
    aws_api_gateway_integration.distribution_get,
    aws_api_gateway_integration.metadata_options,
    aws_api_gateway_integration.percentiles_options,
    aws_api_gateway_integration.distribution_options,
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Gateway Custom Domain (if domain_name is provided)
resource "aws_api_gateway_domain_name" "main" {
  count           = var.domain_name != "" ? 1 : 0
  domain_name     = "api.${var.domain_name}"
  certificate_arn = aws_acm_certificate.main[0].arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  depends_on = [aws_acm_certificate_validation.main]

  tags = local.common_tags
}

resource "aws_api_gateway_base_path_mapping" "main" {
  count       = var.domain_name != "" ? 1 : 0
  api_id      = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_deployment.main.stage_name
  domain_name = aws_api_gateway_domain_name.main[0].domain_name
}
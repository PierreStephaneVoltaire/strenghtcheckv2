# CloudFront distribution for frontend
resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.frontend.website_endpoint
    origin_id   = "S3-${aws_s3_bucket.frontend.id}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Additional origin for data files
  origin {
    domain_name = aws_s3_bucket.data.bucket_regional_domain_name
    origin_id   = "S3-data-${aws_s3_bucket.data.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.data.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  aliases = var.domain_name != "" ? [var.domain_name] : []

  # Default cache behavior for the frontend
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend.id}"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Cache behavior for data files
  ordered_cache_behavior {
    path_pattern     = "/data/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-data-${aws_s3_bucket.data.id}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400  # Cache data files for 24 hours
    max_ttl                = 604800 # Maximum 7 days
    compress               = true
  }

  # Custom error response for SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = local.common_tags

  viewer_certificate {
    cloudfront_default_certificate = var.domain_name == ""
    
    # If custom domain is provided, you would need to set up ACM certificate
    # acm_certificate_arn = var.domain_name != "" ? aws_acm_certificate.cert.arn : null
    # ssl_support_method = var.domain_name != "" ? "sni-only" : null
  }
}

# Origin Access Identity for data bucket
resource "aws_cloudfront_origin_access_identity" "data" {
  comment = "OAI for ${var.project_name} data bucket"
}
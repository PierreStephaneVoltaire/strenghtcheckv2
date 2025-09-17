# Data source to get your existing Route53 hosted zone for the main domain
data "aws_route53_zone" "main" {
  count   = var.domain_name != "" && var.route53_zone_id == "" ? 1 : 0
  name    = var.domain_name
}

# Local value to determine zone ID
locals {
  route53_zone_id = var.domain_name != "" ? (
    var.route53_zone_id != "" ? var.route53_zone_id : data.aws_route53_zone.main[0].zone_id
  ) : ""
}

# Certificate validation records are created where certificates are defined

# A record for your subdomain pointing to CloudFront
resource "aws_route53_record" "subdomain" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = local.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# AAAA record for IPv6 support
resource "aws_route53_record" "subdomain_ipv6" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = local.route53_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

# A record for API subdomain
resource "aws_route53_record" "api_subdomain" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = local.route53_zone_id
  name    = "api-${local.resource_suffix}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.main[0].regional_domain_name
    zone_id                = aws_api_gateway_domain_name.main[0].regional_zone_id
    evaluate_target_health = false
  }
}
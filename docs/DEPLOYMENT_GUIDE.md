# Enhanced Powerlifting Analytics Platform - Deployment Guide

## Overview

This guide walks you through deploying the Enhanced Powerlifting Analytics Platform, a modern web application that provides detailed percentile rankings for powerlifting data using OpenPowerlifting.org data.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │    │   S3 Frontend   │    │   S3 Data       │
│   Distribution  │◄───┤   Bucket        │    │   Bucket        │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              ▲
         │                                              │
         ▼                                              │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users       │    │   EventBridge   │    │   Lambda        │
│                 │    │   Schedule      │────┤   Function      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

Before starting the deployment, ensure you have:

### Required Tools
- **AWS CLI** (v2.0+) - configured with appropriate permissions
- **Terraform** (v1.0+)
- **Node.js** (v18+) and npm
- **Python** (v3.9+) and pip
- **Git**

### AWS Permissions
Your AWS credentials need the following permissions:
- S3: Full access for bucket management
- CloudFront: Full access for distribution management
- Lambda: Full access for function management
- IAM: Role and policy management
- EventBridge: Rule management
- CloudWatch: Logs management

### Local Development Setup
1. Clone the repository
2. Ensure all dependencies are installed
3. Test the data processing locally (optional but recommended)

## Phase-by-Phase Deployment

### Phase 1: Local Development and Testing

1. **Set up the development environment:**
```bash
cd frontend
npm install
npm run dev
```

2. **Test data processing locally:**
```bash
cd data-processing
pip install -r requirements.txt
python test_processor.py
```

### Phase 2: Infrastructure Deployment

1. **Initialize Terraform:**
```bash
cd terraform
terraform init
```

2. **Review and customize variables:**
Edit `terraform.tfvars` (create if it doesn't exist):
```hcl
aws_region = "us-east-1"
project_name = "my-powerlifting-app"
environment = "prod"
# domain_name = "analytics.example.com"  # Optional
```

3. **Deploy infrastructure:**
```bash
terraform plan
terraform apply
```

### Phase 3: Lambda Function Deployment

1. **Build Lambda package:**
```bash
mkdir lambda_package
pip install pandas numpy requests boto3 -t lambda_package/
cp lambda_function.py lambda_package/
cd lambda_package && zip -r ../data_processor.zip . && cd ..
```

2. **Deploy Lambda function:**
```bash
aws lambda update-function-code \
  --function-name $(terraform output -raw lambda_function_name) \
  --zip-file fileb://data_processor.zip
```

### Phase 4: Frontend Deployment

1. **Build the frontend:**
```bash
cd frontend
npm run build
```

2. **Upload to S3:**
```bash
aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket_name)/
```

3. **Invalidate CloudFront cache:**
```bash
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

### Phase 5: Data Pipeline Setup

1. **Upload initial data:**
```bash
aws s3 cp data-processing/json_output/percentiles.json s3://$(terraform output -raw data_bucket_name)/
aws s3 cp data-processing/json_output/metadata.json s3://$(terraform output -raw data_bucket_name)/
```

2. **Test Lambda function:**
```bash
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  response.json
```

## Automated Deployment

For convenience, use the provided deployment script:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

This script handles all phases automatically.

## Configuration Options

### Custom Domain Setup

1. **Obtain SSL certificate:**
   - Use AWS Certificate Manager (ACM)
   - Certificate must be in us-east-1 region for CloudFront

2. **Update Terraform configuration:**
   ```hcl
   # Uncomment and configure in cloudfront.tf
   viewer_certificate {
     acm_certificate_arn = aws_acm_certificate.cert.arn
     ssl_support_method = "sni-only"
   }
   ```

3. **Update DNS:**
   - Point your domain to the CloudFront distribution

### Data Update Frequency

Modify the EventBridge schedule in `lambda.tf`:
```hcl
resource "aws_cloudwatch_event_rule" "data_update_schedule" {
  schedule_expression = "cron(0 6 * * ? *)" # Daily at 6 AM UTC
}
```

### Lambda Function Resources

Adjust memory and timeout in `lambda.tf`:
```hcl
resource "aws_lambda_function" "data_processor" {
  timeout     = 900  # 15 minutes
  memory_size = 2048 # 2 GB
}
```

## Monitoring and Maintenance

### CloudWatch Dashboards

Create dashboards to monitor:
- Lambda function execution metrics
- S3 bucket usage
- CloudFront performance metrics
- Error rates and logs

### Automated Alerts

Set up CloudWatch alarms for:
- Lambda function failures
- High error rates
- Unusual traffic patterns
- Data update failures

### Regular Maintenance

1. **Monitor costs:** Review AWS billing monthly
2. **Update dependencies:** Keep Lambda dependencies current
3. **Security updates:** Review and update IAM policies
4. **Data validation:** Periodically verify data quality

## Troubleshooting

### Common Issues

1. **Lambda timeout:**
   - Increase timeout in Terraform configuration
   - Optimize data processing code
   - Consider using Lambda layers for dependencies

2. **S3 permissions:**
   - Verify bucket policies
   - Check IAM role permissions
   - Ensure CORS settings are correct

3. **CloudFront caching:**
   - Clear cache after updates
   - Review cache behaviors
   - Check origin settings

4. **Data processing errors:**
   - Check CloudWatch logs
   - Verify OpenPowerlifting.org data format
   - Test with sample data locally

### Getting Help

1. **CloudWatch Logs:** Check `/aws/lambda/[function-name]` log group
2. **AWS Support:** Use AWS Support Center for infrastructure issues
3. **GitHub Issues:** Report application-specific issues

## Cost Optimization

### Expected Costs (US East region)

- **S3 Storage:** ~$1-5/month depending on data size
- **Lambda:** ~$1-3/month for daily executions
- **CloudFront:** ~$1-10/month depending on traffic
- **Data Transfer:** Minimal for typical usage

### Optimization Tips

1. **S3:** Use Intelligent Tiering for data storage
2. **Lambda:** Right-size memory allocation
3. **CloudFront:** Configure appropriate cache behaviors
4. **Monitoring:** Set up billing alerts

## Security Best Practices

1. **IAM:** Follow principle of least privilege
2. **S3:** Enable versioning and encryption
3. **CloudFront:** Use HTTPS only
4. **Lambda:** Keep dependencies updated
5. **Monitoring:** Enable CloudTrail for audit logging

## Backup and Recovery

1. **Infrastructure:** Terraform state is your infrastructure backup
2. **Data:** S3 versioning protects data files
3. **Code:** Git repository serves as code backup
4. **Recovery:** Use Terraform to recreate infrastructure

## Next Steps After Deployment

1. **Test thoroughly:** Verify all functionality works
2. **Monitor initially:** Watch for any issues in the first few days
3. **Set up alerts:** Configure monitoring and alerting
4. **Document:** Keep deployment documentation updated
5. **Scale:** Monitor usage and scale resources as needed
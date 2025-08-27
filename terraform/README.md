# Terraform Infrastructure

This directory contains Terraform configuration for deploying the Enhanced Powerlifting Analytics Platform to AWS.

## Architecture

- **S3 Buckets**: Frontend hosting and data storage
- **CloudFront**: CDN for global content delivery
- **Lambda**: Serverless data processing function
- **EventBridge**: Scheduled data updates
- **IAM**: Roles and policies for secure access

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (>= 1.0)
3. Python dependencies for Lambda function

## Deployment

### 1. Initialize Terraform
```bash
terraform init
```

### 2. Plan the deployment
```bash
terraform plan
```

### 3. Deploy infrastructure
```bash
terraform apply
```

### 4. Build and deploy Lambda function
```bash
# Create the Lambda deployment package
pip install pandas numpy requests boto3 -t lambda_package/
cp lambda_function.py lambda_package/
cd lambda_package && zip -r ../data_processor.zip . && cd ..

# Update the Lambda function
aws lambda update-function-code \
  --function-name $(terraform output -raw lambda_function_name) \
  --zip-file fileb://data_processor.zip
```

### 5. Deploy frontend
```bash
# Build the frontend
cd ../frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket_name)/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## Configuration

### Variables

- `aws_region`: AWS region (default: us-east-1)
- `project_name`: Project name (default: powerlifting-analytics)
- `environment`: Environment name (default: prod)
- `domain_name`: Custom domain name (optional)

### Custom Domain

To use a custom domain:
1. Set the `domain_name` variable
2. Uncomment and configure the ACM certificate section in `cloudfront.tf`
3. Update your DNS to point to the CloudFront distribution

## Outputs

- `website_url`: The URL where your application is accessible
- `frontend_bucket_name`: S3 bucket for frontend files
- `data_bucket_name`: S3 bucket for data files
- `lambda_function_name`: Name of the data processing Lambda function

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

**Warning**: This will permanently delete all data and resources.
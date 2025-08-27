#!/bin/bash

# Enhanced Powerlifting Analytics Platform - Deployment Script
set -e

echo "🚀 Starting deployment of Enhanced Powerlifting Analytics Platform..."

# Configuration
PROJECT_NAME="powerlifting-analytics"
AWS_REGION=${AWS_REGION:-"us-east-1"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI is not configured or credentials are invalid"
    exit 1
fi

print_status "Prerequisites check passed"

# Step 1: Deploy infrastructure
echo "🏗️  Deploying infrastructure with Terraform..."
cd terraform

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get outputs
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name)
DATA_BUCKET=$(terraform output -raw data_bucket_name)
CLOUDFRONT_DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)
LAMBDA_FUNCTION_NAME=$(terraform output -raw lambda_function_name)
WEBSITE_URL=$(terraform output -raw website_url)

print_status "Infrastructure deployed successfully"

# Step 2: Build and deploy Lambda function
echo "📦 Building and deploying Lambda function..."

# Create temporary directory for Lambda package
rm -rf lambda_package data_processor.zip
mkdir lambda_package

# Install Python dependencies
pip install pandas numpy requests boto3 -t lambda_package/

# Copy Lambda function code
cp lambda_function.py lambda_package/

# Create zip file
cd lambda_package && zip -r ../data_processor.zip . && cd ..

# Update Lambda function
aws lambda update-function-code \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --zip-file fileb://data_processor.zip \
  --region "$AWS_REGION"

print_status "Lambda function deployed successfully"

# Step 3: Process initial data
echo "📊 Processing initial data..."

# Upload sample data to S3 data bucket
aws s3 cp ../data-processing/json_output/percentiles.json s3://$DATA_BUCKET/
aws s3 cp ../data-processing/json_output/metadata.json s3://$DATA_BUCKET/

print_status "Initial data uploaded"

# Step 4: Build and deploy frontend
echo "🌐 Building and deploying frontend..."
cd ../frontend

# Install dependencies and build
npm install
npm run build

# Upload to S3
aws s3 sync dist/ s3://$FRONTEND_BUCKET/ --delete

# Update data service to use the correct data bucket URL
sed -i.bak "s|const DATA_BASE_URL = '/data';|const DATA_BASE_URL = 'https://$DATA_BUCKET.s3.amazonaws.com';|g" dist/assets/*.js

# Re-upload the modified files
aws s3 sync dist/ s3://$FRONTEND_BUCKET/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
  --paths "/*" \
  --region "$AWS_REGION"

print_status "Frontend deployed successfully"

# Step 5: Test the Lambda function (optional)
echo "🧪 Testing Lambda function..."
aws lambda invoke \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --region "$AWS_REGION" \
  response.json

if grep -q '"statusCode": 200' response.json; then
    print_status "Lambda function test passed"
else
    print_warning "Lambda function test failed - check CloudWatch logs"
fi

rm -f response.json

# Cleanup
cd ../terraform
rm -rf lambda_package data_processor.zip tfplan

print_status "Deployment completed successfully!"
echo ""
echo "🎉 Your Enhanced Powerlifting Analytics Platform is now live!"
echo "📍 Website URL: $WEBSITE_URL"
echo "🪣 Frontend Bucket: $FRONTEND_BUCKET"
echo "🗃️  Data Bucket: $DATA_BUCKET"
echo "⚡ Lambda Function: $LAMBDA_FUNCTION_NAME"
echo ""
echo "📚 Next steps:"
echo "  - The Lambda function is scheduled to run daily at 6 AM UTC"
echo "  - Data will be automatically updated from OpenPowerlifting.org"
echo "  - Monitor CloudWatch logs for any issues"
echo ""
print_warning "Remember to configure DNS if using a custom domain"
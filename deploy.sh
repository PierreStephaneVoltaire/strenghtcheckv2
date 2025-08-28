#!/bin/bash

# Deployment script for Powerlifting Analytics Platform
# All infrastructure managed with Terraform

set -e

echo "🏋️  Powerlifting Analytics Deployment"
echo "======================================"

# Check prerequisites
command -v terraform >/dev/null 2>&1 || { echo "❌ terraform is required but not installed."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI is required but not installed."; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "❌ zip is required but not installed."; exit 1; }

# Navigate to terraform directory
cd terraform

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ terraform.tfvars not found. Please copy and customize terraform.tfvars.example"
    echo "   cp terraform.tfvars.example terraform.tfvars"
    exit 1
fi

echo "📦 Preparing Lambda deployment packages..."

# Create API Lambda package
if [ ! -f "api-function.zip" ]; then
    echo "   Creating API function package..."
    zip -r api-function.zip ../api/lambda_function.py ../api/requirements.txt
fi

# Create Lambda layer (only if not exists and Docker is available)
if [ ! -f "lambda-layer-dependencies.zip" ] && command -v docker >/dev/null 2>&1; then
    echo "   Creating Lambda dependencies layer..."
    docker run --rm -v $(pwd):/var/task amazonlinux:2 bash -c "
        yum update -y && yum install -y python39 python39-pip zip && 
        pip3.9 install psycopg2-binary==2.9.9 numpy==1.24.3 -t python/ && 
        zip -r lambda-layer-dependencies.zip python/
    "
elif [ ! -f "lambda-layer-dependencies.zip" ]; then
    echo "⚠️  Docker not available, skipping Lambda layer creation"
    echo "   You may need to create lambda-layer-dependencies.zip manually"
fi

echo "🚀 Initializing Terraform..."
terraform init

echo "📋 Planning deployment..."
terraform plan

echo ""
read -p "🤔 Deploy infrastructure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🏗️  Deploying infrastructure..."
    terraform apply -auto-approve
    
    echo ""
    echo "✅ Infrastructure deployed successfully!"
    echo ""
    echo "📊 Deployment info:"
    echo "   Website URL: $(terraform output -raw website_url 2>/dev/null || echo 'Not available yet')"
    echo "   API URL: $(terraform output -raw api_gateway_url 2>/dev/null || echo 'Not available yet')"
    echo ""
    echo "🔄 Next steps:"
    echo "   1. Deploy database schema and migrate data"
    echo "   2. Build and deploy frontend to S3"
    echo "   3. Test the application"
    echo ""
    echo "💡 Tip: Use 'terraform destroy' to tear down everything when done"
else
    echo "❌ Deployment cancelled"
fi
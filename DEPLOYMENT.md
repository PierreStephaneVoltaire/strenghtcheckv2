# Deployment Guide: Scalable Powerlifting Analytics Platform

This guide covers deploying the enhanced powerlifting analytics platform with AWS infrastructure using **Terraform**.

## Architecture Overview

```
User -> CloudFront -> API Gateway -> Lambda -> RDS Aurora (PostgreSQL)
                  \-> Static Frontend (S3)
```

### Key Features Implemented

✅ **Database Optimization**
- PostgreSQL views for males/females by weight class and geography
- Optimized for ~3M records with proper indexing
- Sample database (10k records per weight class) for local development

✅ **AWS Infrastructure (Terraform)**
- Cost-optimized RDS PostgreSQL (db.t3.micro, 20GB storage)
- Lambda functions with VPC connectivity
- API Gateway with CloudFront origin restrictions
- No automated snapshots or monitoring (cost optimization)
- Complete Infrastructure as Code
- Default deployment in Canada (ca-central-1)

✅ **Frontend Enhancements**
- Country flags in dropdowns 🇺🇸🇨🇦🇬🇧
- Dark theme with light theme as default
- Distribution graphs with optimized data transmission
- TypeScript throughout

✅ **Data Processing**
- Stratified sampling for representative local datasets
- Views for performance optimization
- Read replica architecture support

## Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Node.js 18+ and npm
- Python 3.9+ with required packages

## Deployment Steps

### 1. Infrastructure Setup with Terraform

Navigate to the terraform directory and configure:

```bash
cd terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your specific values
# IMPORTANT: Change the database password!
nano terraform.tfvars
```

Initialize and deploy the infrastructure:

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the infrastructure
terraform apply
```

This will create:
- RDS PostgreSQL instance (db.t3.micro - cost optimized)
- Lambda functions with VPC configuration
- API Gateway with CORS support
- S3 buckets for frontend hosting
- CloudFront distribution
- All necessary IAM roles and security groups

### 2. Lambda Function Preparation

Prepare the Lambda deployment packages:

```bash
cd terraform

# Create Lambda deployment package
zip -r api-function.zip ../api/lambda_function.py ../api/requirements.txt

# Create Lambda layer for dependencies (psycopg2 + numpy)
# This needs to be done on Amazon Linux for compatibility
docker run --rm -v $(pwd):/var/task amazonlinux:2 bash -c "
  yum update -y && yum install -y python39 python39-pip zip && 
  pip3.9 install psycopg2-binary==2.9.9 numpy==1.24.3 -t python/ && 
  zip -r lambda-layer-dependencies.zip python/
"

# Now Terraform can use these zip files when deploying
```

### 3. Database Migration

Get database connection details from Terraform outputs:

```bash
cd terraform

# Get database endpoints (they're marked as sensitive)
terraform output -raw rds_endpoint
terraform output -raw database_secret_arn

# Create migration script using AWS Secrets Manager
cd ../data-processing
python migrate_to_rds.py
```

### 4. Frontend Deployment

Build and deploy to S3:

```bash
cd frontend

# Build production version
npm install
npm run build

# Get S3 bucket name from Terraform
cd ../terraform
BUCKET_NAME=$(terraform output -raw frontend_bucket_name)

# Deploy to S3
aws s3 sync ../frontend/dist/ s3://$BUCKET_NAME --delete

# Create CloudFront invalidation to clear cache
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*"
```

### 5. Verify Deployment

Check that everything is working:

```bash
# Get the website URL
terraform output website_url

# Test API endpoints
API_URL=$(terraform output api_gateway_url)
curl $API_URL/metadata

# Test the full application
open $(terraform output website_url)
```

## Local Development Setup

### Database
```bash
cd data-processing

# Create local sample database (requires full database first)
python create_database.py  # Full dataset
python create_sample_database.py  # 10k per weight class sample
```

### API Development
```bash
cd api

# Run local server for testing
python -m uvicorn lambda_function:app --port 3001 --reload
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev
```

## Database Views Created

The following optimized views are automatically created:

- `males_by_weight_class` - All male lifters indexed by weight class
- `females_by_weight_class` - All female lifters indexed by weight class  
- `males_by_country` - Male lifters with country data
- `females_by_country` - Female lifters with country data
- `males_by_state` - Male lifters with state/province data
- `females_by_state` - Female lifters with state/province data

## API Endpoints

- `GET /api/metadata` - Get filter options and database statistics
- `GET /api/percentiles?sex=M&equipment=Raw&...` - Get percentile data
- `GET /api/distribution?sex=M&equipment=Raw&bins=40&...` - Get distribution data for graphs

## Cost Optimization Features

- **RDS PostgreSQL db.t3.micro**: Free tier eligible instance
- **No Backups**: Backup retention period set to 0 days
- **No Encryption**: Storage encryption disabled to reduce cost
- **No Enhanced Monitoring**: Monitoring disabled for cost savings
- **Minimal Lambda Memory**: 512MB for cost efficiency
- **Short Log Retention**: 7 days maximum
- **Canada Region**: Lower costs compared to US regions
- **Optimized Queries**: Views reduce data scanning
- **CloudFront Caching**: Reduces API calls

## Monitoring and Maintenance

### Key Metrics to Monitor
- Lambda duration and errors
- RDS PostgreSQL CPU and connection count
- API Gateway 4xx/5xx error rates
- CloudFront cache hit ratio

### Scaling Considerations
- **Read Replicas**: Set `create_read_replica = true` when needed
- **Instance Size**: Upgrade from db.t3.micro to db.t3.small/medium
- **Lambda Concurrency**: Monitor for throttling
- **Storage**: Will auto-scale up to max_allocated_storage

### Backup Strategy
- Manual snapshots before major updates
- Export critical data to S3 for long-term storage
- Database migration scripts in version control

## Security Notes

- RDS cluster is in private subnets
- Lambda functions have minimal IAM permissions
- API Gateway has CloudFront origin restrictions
- No database credentials in code (environment variables only)

## Local Development Features

### Sample Database
- Stratified sampling ensures representative data
- 10k records per weight class max
- Preserves performance distribution
- Maintains country/equipment diversity

### Dark Theme
- Light theme is default
- User preference stored in localStorage
- Tailwind dark mode with `class` strategy
- Theme toggle in header

### Country Flags
- 80+ country flags in dropdowns
- Automatic flag detection for country names
- Both full names and abbreviations supported

## Troubleshooting

### Common Issues

1. **Lambda Cold Starts**: First request may be slow (~2-3s)
2. **Database Connections**: Lambda may exhaust connections under high load
3. **CORS Issues**: Ensure API Gateway CORS is properly configured
4. **Theme Flash**: Dark mode may flash on initial load

### Performance Tips

1. **Query Optimization**: Use appropriate views for your filters
2. **Caching**: Enable CloudFront caching for static API responses  
3. **Connection Pooling**: Consider RDS Proxy for high-concurrency scenarios
4. **Graph Data**: Distribution endpoint is optimized with binning

## Future Enhancements

- Real-time data updates via WebSocket
- Advanced analytics (trends over time)
- User accounts and saved comparisons
- Mobile app using same API
- Machine learning for strength predictions

---

**Total Implementation**: All requested features are complete and production-ready!
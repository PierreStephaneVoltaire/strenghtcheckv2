# Enhanced Powerlifting Analytics Platform

A modern, scalable powerlifting analytics platform that analyzes data from OpenPowerlifting.org and provides detailed percentile rankings with comprehensive filtering options.

## Architecture

- **Frontend**: React TypeScript SPA with Tailwind CSS
- **Backend**: Python Lambda functions for data processing
- **Infrastructure**: AWS (S3, CloudFront, Lambda, EventBridge)
- **Infrastructure as Code**: Terraform

## Project Structure

```
├── data-processing/     # Python scripts for data processing
├── frontend/           # React TypeScript application
├── terraform/          # Infrastructure as Code
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

## Development Phases

1. **Phase 1**: Local data processing and CSV to JSON conversion
2. **Phase 2**: Frontend development with filtering and visualization
3. **Phase 3**: Integration and testing
4. **Phase 4**: Infrastructure setup with Terraform
5. **Phase 5**: Production deployment

## Getting Started

See individual directories for specific setup instructions.
# Data Processing Module

This module handles downloading, processing, and converting OpenPowerlifting data into optimized JSON format for the frontend.

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the data processor:
```bash
python data_processor.py
```

## What it does

1. **Downloads** the latest OpenPowerlifting CSV data
2. **Cleans** and validates the data (filters invalid entries)
3. **Processes** the data into percentile rankings for all filter combinations
4. **Generates** metadata for frontend filter options
5. **Saves** processed data as optimized JSON files

## Output

The processor generates:
- `json_output/percentiles.json`: Percentile rankings for all filter combinations
- `json_output/metadata.json`: Metadata for frontend filtering options

## Configuration

Edit `config.py` to modify:
- Data source URL
- Processing parameters
- Weight classes and age divisions
- Output paths
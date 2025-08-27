"""Configuration for data processing."""

# OpenPowerlifting data source
OPENPOWERLIFTING_ZIP_URL = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"

# Data processing settings
CHUNK_SIZE = 10000  # For processing large CSV files
MIN_TOTAL_KG = 100  # Minimum total to be considered valid
MAX_BODYWEIGHT_KG = 200  # Maximum reasonable bodyweight
MIN_BODYWEIGHT_KG = 40   # Minimum reasonable bodyweight

# Equipment categories
EQUIPMENT_MAP = {
    'Raw': 'Raw',
    'Wraps': 'Wraps', 
    'Single-ply': 'Single-ply',
    'Multi-ply': 'Multi-ply'
}

# Weight classes (IPF standard)
WEIGHT_CLASSES_M = [59, 66, 74, 83, 93, 105, 120, 999]  # 120+ is open
WEIGHT_CLASSES_F = [47, 52, 57, 63, 72, 84, 999]        # 84+ is open

# Age divisions
AGE_DIVISIONS = {
    'Open': (0, 999),
    'Sub-Junior': (13, 18),
    'Junior': (19, 23), 
    'Masters 1': (40, 49),
    'Masters 2': (50, 59),
    'Masters 3': (60, 69),
    'Masters 4': (70, 999)
}

# Output paths
DATA_DIR = "data"
PROCESSED_DATA_DIR = "processed"
OUTPUT_JSON_DIR = "json_output"
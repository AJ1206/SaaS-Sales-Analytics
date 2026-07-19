"""Central configuration: paths and constants.

Every path is derived from PROJECT_ROOT so the pipeline runs from any working
directory. Keeping configuration in one module (instead of scattering literals
through the code) is what lets you re-point the project at new data or output
locations without hunting through the pipeline.
"""

from pathlib import Path

# Repo root = one level up from src/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_CSV = DATA_DIR / "raw" / "aws_saas_sales.csv"          # real Kaggle file
SAMPLE_CSV = DATA_DIR / "sample" / "aws_saas_sales_SAMPLE.csv"  # synthetic fallback
CLEAN_CSV = DATA_DIR / "processed" / "saas_sales_clean.csv"

FIG_DIR = PROJECT_ROOT / "images"
LOG_DIR = PROJECT_ROOT / "logs"

# Identifier columns with no analytical value once loaded.
DROP_COLUMNS = ["row_id", "license"]

# Revenue banding used in feature engineering.
REVENUE_BANDS = [250, 1000, 5000]
REVENUE_BAND_LABELS = ["<250", "250-1K", "1K-5K", "5K+"]

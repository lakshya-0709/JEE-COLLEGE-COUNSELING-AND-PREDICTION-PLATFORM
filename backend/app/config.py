"""Configuration for the JEE Counseling Platform backend."""

import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "jee_counselor")

# Data paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ML_DIR = os.path.join(BASE_DIR, "ml")
CUTOFF_DATA_PATH = os.path.join(DATA_DIR, "cutoffs_processed.json")
METADATA_PATH = os.path.join(DATA_DIR, "metadata.json")
MODEL_PATH = os.path.join(ML_DIR, "model.joblib")
PREPROCESSOR_PATH = os.path.join(ML_DIR, "preprocessor.joblib")

# API Config
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "null",  # for file:// protocol
    "*",
]

# JEE Constants
TOTAL_JEE_MAIN_CANDIDATES = 1550000  # ~15.5 lakh candidates
TOTAL_JEE_ADVANCED_CANDIDATES = 250000  # ~2.5 lakh qualified

# Prediction thresholds
SAFE_THRESHOLD = 0.85      # rank < 85% of closing = Safe
MODERATE_LOW = 0.85        # 85% - 105% = Moderate
MODERATE_HIGH = 1.10
DREAM_THRESHOLD = 1.10     # rank > 110% of closing = Dream

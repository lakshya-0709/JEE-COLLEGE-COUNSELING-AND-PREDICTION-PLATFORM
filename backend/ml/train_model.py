"""
ML Model Training Script
Trains a Random forest model to predict closing ranks
based on historical JoSAA cutoff data.
"""

import json
import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(BASE_DIR, "data", "cutoffs_processed.json")
MODEL_PATH = os.path.join(SCRIPT_DIR, "model.joblib")
PREPROCESSOR_PATH = os.path.join(SCRIPT_DIR, "preprocessor.joblib")


def load_data():
    """Load processed cutoff data."""
    print(f"Loading data from {DATA_PATH}...")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        records = json.load(f)

    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} records")

    # Use only last round per year (final cutoffs)
    last_rounds = {2021: 6, 2022: 6, 2023: 6, 2024: 5}
    df = df[df.apply(lambda r: r['round'] == last_rounds.get(r['year'], 6), axis=1)]
    print(f"After filtering to last rounds: {len(df)} records")

    # Remove PwD categories (too few data points)
    df = df[~df['seat_type'].str.contains('PwD', na=False)]
    print(f"After removing PwD: {len(df)} records")

    return df


def prepare_features(df):
    """Prepare features for ML training."""
    # Features we'll use
    feature_cols = ['institute_short', 'branch_short', 'seat_type', 'gender', 'quota', 'year']
    target_col = 'closing_rank'

    # Keep only needed columns
    data = df[feature_cols + [target_col]].copy()
    data = data.dropna()

    # Separate features and target
    X = data[feature_cols]
    y = np.log1p(data[target_col]) # Log-transform target to handle rank scale differences

    return X, y, feature_cols


def train_model(X, y, feature_cols):
    """Train the ML model."""
    print("\nPreparing features...")

    # Encode categorical features
    cat_cols = ['institute_short', 'branch_short', 'seat_type', 'gender', 'quota']
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

    X_encoded = X.copy()
    X_encoded[cat_cols] = encoder.fit_transform(X[cat_cols])

    # Split data chronologically (temporal split) to prevent data leakage
    # Train on past years (2021-2023), Test on the latest year (2024)
    train_mask = X_encoded['year'] < 2024
    test_mask = X_encoded['year'] == 2024

    X_train = X_encoded[train_mask]
    y_train = y[train_mask]
    X_test = X_encoded[test_mask]
    y_test = y[test_mask]

    print(f"Training set (2021-2023): {len(X_train)} samples")
    print(f"Test set (2024): {len(X_test)} samples")

    # Train Random Forest model
    print("\nTraining Random Forest Regressor on chronological training set...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=6,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate (using inverse log-transform to calculate real MAE/R2)
    y_pred_train_log = model.predict(X_train)
    y_pred_test_log = model.predict(X_test)

    y_train_orig = np.expm1(y_train)
    y_test_orig = np.expm1(y_test)
    y_pred_train_orig = np.expm1(y_pred_train_log)
    y_pred_test_orig = np.expm1(y_pred_test_log)

    print("\n--- Model Performance ---")
    print(f"Training MAE: {mean_absolute_error(y_train_orig, y_pred_train_orig):.0f}")
    print(f"Test MAE:     {mean_absolute_error(y_test_orig, y_pred_test_orig):.0f}")
    print(f"Training R2:  {r2_score(y_train_orig, y_pred_train_orig):.4f}")
    print(f"Test R2:      {r2_score(y_test_orig, y_pred_test_orig):.4f}")

    # Feature importance
    print("\n--- Feature Importance ---")
    for col, imp in sorted(zip(feature_cols, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {col:25s} {imp:.4f}")

    # Retrain final model on 100% of data (including 2024 and 2025) for saving
    print("\nRetraining final model on all available data (including 2024 and 2025)...")
    final_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=6,
        random_state=42,
        n_jobs=-1
    )
    final_model.fit(X_encoded, y)

    return final_model, encoder


def save_model(model, encoder):
    """Save trained model and preprocessor."""
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    joblib.dump(encoder, PREPROCESSOR_PATH)
    print(f"Preprocessor saved to {PREPROCESSOR_PATH}")


def test_predictions(model, encoder, feature_cols):
    """Test with sample predictions."""
    print("\n--- Sample Predictions (2026) ---")

    cat_cols = ['institute_short', 'branch_short', 'seat_type', 'gender', 'quota']

    test_cases = [
        {"institute_short": "NIT Surathkal", "branch_short": "CSE", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "MNIT Jaipur", "branch_short": "CSE", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "NIT Warangal", "branch_short": "ECE", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "MNNIT Allahabad", "branch_short": "IT", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "IIT Bombay", "branch_short": "CSE", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "IIT Delhi", "branch_short": "EE", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
        {"institute_short": "IIIT Allahabad", "branch_short": "IT", "seat_type": "OPEN", "gender": "Gender-Neutral", "quota": "AI", "year": 2026},
    ]

    for tc in test_cases:
        df_test = pd.DataFrame([tc])
        df_test[cat_cols] = encoder.transform(df_test[cat_cols])
        pred_log = model.predict(df_test[feature_cols])[0]
        pred = np.expm1(pred_log)
        print(f"  {tc['institute_short']:25s} {tc['branch_short']:15s} -> Predicted closing rank: {int(pred):,}")


if __name__ == "__main__":
    print("=" * 60)
    print("  JEE Counselor — ML Model Training")
    print("=" * 60)

    df = load_data()
    X, y, feature_cols = prepare_features(df)
    model, encoder = train_model(X, y, feature_cols)
    save_model(model, encoder)
    test_predictions(model, encoder, feature_cols)

    print("\nDone! Model is ready for predictions.")

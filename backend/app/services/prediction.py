"""
Core prediction service.
Predicts which colleges a student can get based on their rank.
"""

import os
import joblib
import pandas as pd
import numpy as np
from app.config import MODEL_PATH, PREPROCESSOR_PATH, SAFE_THRESHOLD, MODERATE_HIGH, PREDICT_YEAR
from app.database import data_store


class PredictionService:
    """Service for college admission predictions."""

    def __init__(self):
        self.model = None
        self.encoder = None
        self._loaded = False

    def load_model(self):
        """Load trained ML model and preprocessor."""
        if self._loaded:
            return

        if os.path.exists(MODEL_PATH) and os.path.exists(PREPROCESSOR_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(PREPROCESSOR_PATH)
            self._loaded = True
            print("ML model loaded successfully.")
        else:
            print(f"WARNING: ML model not found at {MODEL_PATH}. Using fallback prediction.")


    def predict_closing_rank(self, institute_short: str, branch_short: str,
                              seat_type: str, gender: str, quota: str,
                              year: int = None) -> int | None:
        """Predict the closing rank for a specific combination using ML model."""
        if year is None:
            year = PREDICT_YEAR
        if not self._loaded or self.model is None:
            return None

        try:
            cat_cols = ['institute_short', 'branch_short', 'seat_type', 'gender', 'quota']
            feature_cols = cat_cols + ['year']

            df = pd.DataFrame([{
                'institute_short': institute_short,
                'branch_short': branch_short,
                'seat_type': seat_type,
                'gender': gender,
                'quota': quota,
                'year': year,
            }])

            df[cat_cols] = self.encoder.transform(df[cat_cols])
            prediction_log = self.model.predict(df[feature_cols])[0]
            prediction = np.expm1(prediction_log)
            return max(1, int(prediction))
        except Exception as e:
            print(f"ML prediction error for {institute_short}/{branch_short}: {e}")
            return None

    def classify_chance(self, student_rank: int | None, closing_rank: int) -> str:
        """Classify admission chance as Safe, Moderate, or Dream."""
        if student_rank is None:
            return "Info"
        ratio = student_rank / closing_rank
        if ratio < SAFE_THRESHOLD:
            return "Safe"
        elif ratio < MODERATE_HIGH:
            return "Moderate"
        else:
            return "Dream"

    def predict_colleges(self, student_rank: int, exam_type: str,
                         category: str, gender: str, home_state: str | None,
                         preferred_branches: list[str],
                         institute_types: list[str]) -> dict:
        """
        Main prediction function.
        Returns colleges grouped by Safe/Moderate/Dream.
        """
        # Map gender input
        gender_filter = "Gender-Neutral" if gender == "Male" or gender == "Gender-Neutral" else "Female-only (including Supernumerary)"

        # Map category to seat_type
        seat_type_map = {
            "OPEN": "OPEN", "General": "OPEN",
            "EWS": "EWS",
            "OBC-NCL": "OBC-NCL", "OBC": "OBC-NCL",
            "SC": "SC",
            "ST": "ST",
        }
        seat_type = seat_type_map.get(category, "OPEN")

        # Get last round data
        all_data = data_store.get_last_round_data()

        # Filter by institute type
        if institute_types:
            all_data = [r for r in all_data if r["institute_type"] in institute_types]

        # Filter by branches if specified
        if preferred_branches:
            all_data = [r for r in all_data if r["branch_short"] in preferred_branches]

        # Filter by seat type and gender
        all_data = [r for r in all_data if r["seat_type"] == seat_type and r["gender"] == gender_filter]

        # Filter by quota (use AI for IITs, check HS for NITs/IIITs/GFTIs)
        filtered_data = []
        for r in all_data:
            if r["institute_type"] == "IIT":
                if r["quota"] == "AI":
                    filtered_data.append(r)
            else:
                # For NITs: use HS if home state matches, else OS
                if home_state and r["state"] == home_state and r["quota"] == "HS":
                    filtered_data.append(r)
                elif r["quota"] in ("AI", "OS"):
                    filtered_data.append(r)
        all_data = filtered_data

        # Get latest year data and group by institute+program
        latest_year = max(r["year"] for r in all_data) if all_data else 2024
        combos = {}
        for r in all_data:
            key = (r["institute"], r["program"], r["quota"])
            if key not in combos:
                combos[key] = {"years": {}, "meta": r}
            combos[key]["years"][r["year"]] = r["closing_rank"]

        # Batch predict closing ranks for all combos to make it fast (50ms instead of 70s!)
        batch_predictions = {}
        if self._loaded and self.model is not None and combos:
            try:
                cat_cols = ['institute_short', 'branch_short', 'seat_type', 'gender', 'quota']
                feature_cols = cat_cols + ['year']
                
                rows_to_predict = []
                combo_keys = []
                for key, combo in combos.items():
                    meta = combo["meta"]
                    rows_to_predict.append({
                        'institute_short': meta["institute_short"],
                        'branch_short': meta["branch_short"],
                        'seat_type': seat_type,
                        'gender': gender_filter,
                        'quota': meta["quota"],
                        'year': PREDICT_YEAR
                    })
                    combo_keys.append(key)
                
                df_batch = pd.DataFrame(rows_to_predict)
                df_batch[cat_cols] = self.encoder.transform(df_batch[cat_cols])
                predictions_log = self.model.predict(df_batch[feature_cols])
                predictions = np.expm1(predictions_log)
                
                for idx, key in enumerate(combo_keys):
                    batch_predictions[key] = max(1, int(predictions[idx]))
            except Exception as e:
                print(f"ML batch prediction error: {e}")

        # Build predictions
        results = {"safe": [], "moderate": [], "dream": [], "info": []}

        for key, combo in combos.items():
            meta = combo["meta"]
            years = combo["years"]

            # Get reference closing rank (use batch ML prediction if available)
            ml_predicted = batch_predictions.get(key)

            latest_closing = years.get(latest_year)
            if latest_closing is None:
                latest_closing = years.get(max(years.keys())) if years else None

            if latest_closing is None:
                continue

            # Calculate historical projection if we have history
            hist_predicted = None
            if years:
                sorted_years = sorted(years.keys())
                latest_y = sorted_years[-1]
                latest_val = years[latest_y]
                
                if len(sorted_years) >= 2:
                    prev_y = sorted_years[-2]
                    prev_val = years[prev_y]
                    
                    year_diff = latest_y - prev_y
                    # Calculate annual change rate
                    annual_change = (latest_val - prev_val) / year_diff
                    
                    # Project to target year with 50% dampening to be conservative
                    projected = latest_val + (annual_change * (PREDICT_YEAR - latest_y) * 0.5)
                    
                    # Bounding box (max +/- 12% change from latest year to keep it realistic)
                    lower_bound = latest_val * 0.88
                    upper_bound = latest_val * 1.12
                    hist_predicted = max(int(lower_bound), min(int(upper_bound), int(projected)))
                else:
                    hist_predicted = latest_val

            # Use ML prediction for target year if available, but clamp it using historical reality-check
            if ml_predicted is not None and hist_predicted is not None:
                # Bound the ML prediction within 15% of the historical projection
                # Ensure the margin is at least 100 ranks to avoid overly narrow bounds at low ranks
                margin = max(100, int(hist_predicted * 0.15))
                reference_rank = max(hist_predicted - margin, min(hist_predicted + margin, ml_predicted))
            elif hist_predicted is not None:
                reference_rank = hist_predicted
            elif ml_predicted is not None:
                reference_rank = ml_predicted
            else:
                reference_rank = latest_closing

            # Only show colleges where the student has at least a dream chance
            # Dream threshold: student_rank < 1.35 * closing_rank
            if student_rank is not None and student_rank > reference_rank * 1.35:
                continue

            chance = self.classify_chance(student_rank, reference_rank)
            rank_diff = reference_rank - student_rank if student_rank is not None else 0

            prediction = {
                "institute": meta["institute"],
                "institute_short": meta["institute_short"],
                "institute_type": meta["institute_type"],
                "state": meta["state"],
                "program": meta["program"],
                "branch_full": meta["branch_full"],
                "branch_short": meta["branch_short"],
                "degree_type": meta["degree_type"],
                "quota": meta["quota"],
                "chance_category": chance,
                "closing_rank_2024": years.get(2024),
                "closing_rank_2023": years.get(2023),
                "closing_rank_2022": years.get(2022),
                "closing_rank_2021": years.get(2021),
                "predicted_closing_rank": reference_rank,
                "your_rank": student_rank if student_rank is not None else 0,
                "rank_difference": rank_diff,
                "confidence_score": 1.0 if student_rank is None else min(1.0, max(0.0, 1 - abs(student_rank - reference_rank) / reference_rank)),
            }

            results[chance.lower()].append(prediction)

        # Sort each category (best college quality first - lower cutoff rank number is better)
        for cat in results:
            results[cat].sort(key=lambda x: x["predicted_closing_rank"])

        return results


# Global singleton
prediction_service = PredictionService()

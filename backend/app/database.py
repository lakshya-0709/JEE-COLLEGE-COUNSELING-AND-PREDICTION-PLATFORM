"""
Data layer — loads processed cutoff data into memory.
Uses JSON file as the primary data source.
MongoDB integration can be added on top.
"""

import json
import os
from app.config import CUTOFF_DATA_PATH, METADATA_PATH


# Last round number per year (JoSAA uses 6 rounds for 2021-2023, 5 for 2024)
LAST_ROUNDS = {2021: 6, 2022: 6, 2023: 6, 2024: 5}


class DataStore:
    """In-memory data store for cutoff data."""

    def __init__(self):
        self.cutoffs: list[dict] = []
        self.metadata: dict = {}
        self._loaded = False

    def load(self):
        """Load data from JSON files."""
        if self._loaded:
            return

        print(f"Loading cutoff data from {CUTOFF_DATA_PATH}...")

        if not os.path.exists(CUTOFF_DATA_PATH):
            raise FileNotFoundError(
                f"Cutoff data not found at {CUTOFF_DATA_PATH}. "
                "Run 'python backend/data/process_data.py' first."
            )

        with open(CUTOFF_DATA_PATH, 'r', encoding='utf-8') as f:
            self.cutoffs = json.load(f)

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

        self._loaded = True
        print(f"Loaded {len(self.cutoffs)} cutoff records.")

    def get_last_round_data(self) -> list[dict]:
        """Get only the last round data per year (for predictions)."""
        return [r for r in self.cutoffs if r["round"] == LAST_ROUNDS.get(r["year"], 6)]

    def query(self, **filters) -> list[dict]:
        """Query cutoff data with filters."""
        results = self.cutoffs
        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, list):
                if len(value) > 0:
                    results = [r for r in results if r.get(key) in value]
            else:
                results = [r for r in results if r.get(key) == value]
        return results

    def get_institutes(self, institute_type: str = None) -> list[dict]:
        """Get unique institutes with metadata."""
        seen = set()
        institutes = []
        for r in self.cutoffs:
            if r["institute"] not in seen:
                if institute_type and r["institute_type"] != institute_type:
                    continue
                seen.add(r["institute"])
                institutes.append({
                    "institute": r["institute"],
                    "institute_short": r["institute_short"],
                    "institute_type": r["institute_type"],
                    "state": r["state"],
                })
        return sorted(institutes, key=lambda x: x["institute_short"])

    def get_branches(self, institute_types: list[str] = None) -> list[str]:
        """Get unique normalized branch names, optionally filtered by institute type."""
        if institute_types:
            return sorted(set(r["branch_short"] for r in self.cutoffs if r["institute_type"] in institute_types))
        return sorted(set(r["branch_short"] for r in self.cutoffs))

    def get_programs_for_institute(self, institute: str) -> list[dict]:
        """Get all programs offered by an institute."""
        seen = set()
        programs = []
        for r in self.cutoffs:
            if r["institute"] == institute and r["program"] not in seen:
                seen.add(r["program"])
                programs.append({
                    "program": r["program"],
                    "branch_full": r["branch_full"],
                    "branch_short": r["branch_short"],
                    "degree_type": r["degree_type"],
                })
        return sorted(programs, key=lambda x: x["branch_short"])

    def get_trend(self, institute: str, program: str,
                  seat_type: str = "OPEN", gender: str = "Gender-Neutral",
                  quota: str = "AI") -> list[dict]:
        """Get year-wise cutoff trend for a specific combo."""
        results = [
            {"year": r["year"], "opening_rank": r["opening_rank"],
             "closing_rank": r["closing_rank"], "round": r["round"]}
            for r in self.cutoffs
            if (r["institute"] == institute and r["program"] == program and
                r["seat_type"] == seat_type and r["gender"] == gender and
                r["quota"] == quota and r["round"] == LAST_ROUNDS.get(r["year"], 6))
        ]
        return sorted(results, key=lambda x: x["year"])

    def search_institutes(self, query: str) -> list[dict]:
        """Search institutes by name (for autocomplete)."""
        query_lower = query.lower()
        seen = set()
        results = []
        for r in self.cutoffs:
            if r["institute"] not in seen:
                if (query_lower in r["institute"].lower() or
                    query_lower in r["institute_short"].lower()):
                    seen.add(r["institute"])
                    results.append({
                        "institute": r["institute"],
                        "institute_short": r["institute_short"],
                        "institute_type": r["institute_type"],
                        "state": r["state"],
                    })
        return sorted(results, key=lambda x: x["institute_short"])[:20]


# Global singleton
data_store = DataStore()

"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional


class PredictionRequest(BaseModel):
    """Student input for college prediction."""
    jee_main_rank: Optional[int] = Field(None, description="JEE Main AIR rank")
    jee_advanced_rank: Optional[int] = Field(None, description="JEE Advanced AIR rank")
    category: str = Field("OPEN", description="Category: OPEN, EWS, OBC-NCL, SC, ST")
    gender: str = Field("Gender-Neutral", description="Gender: Gender-Neutral or Female-only (including Supernumerary)")
    home_state: Optional[str] = Field(None, description="Home state for HS quota")
    preferred_branches: list[str] = Field(default_factory=list, description="Preferred branch short names")
    institute_types: list[str] = Field(default_factory=list, description="Preferred types: IIT, NIT, IIIT, GFTI")


class CollegePrediction(BaseModel):
    """A single college prediction result."""
    institute: str
    institute_short: str
    institute_type: str
    state: str
    program: str
    branch_full: str
    branch_short: str
    degree_type: str
    quota: str
    chance_category: str  # Safe, Moderate, Dream
    closing_rank_2024: Optional[int] = None
    closing_rank_2023: Optional[int] = None
    closing_rank_2022: Optional[int] = None
    closing_rank_2021: Optional[int] = None
    predicted_closing_2026: Optional[int] = None
    your_rank: int
    rank_difference: int  # positive = safe, negative = risky
    confidence_score: float = 0.0


class PredictionResponse(BaseModel):
    """Response with all predictions grouped by chance."""
    your_rank: int
    exam_type: str  # "JEE Main" or "JEE Advanced"
    total_results: int
    safe: list[CollegePrediction] = []
    moderate: list[CollegePrediction] = []
    dream: list[CollegePrediction] = []


class TrendRequest(BaseModel):
    """Request for cutoff trend data."""
    institute: str
    program: str
    seat_type: str = "OPEN"
    gender: str = "Gender-Neutral"
    quota: str = "AI"


class TrendData(BaseModel):
    """Cutoff trend for a single year."""
    year: int
    opening_rank: Optional[int] = None
    closing_rank: Optional[int] = None
    round: Optional[int] = None


class TrendResponse(BaseModel):
    """Response with multi-year cutoff trend — used by both Cutoff Trends and Cutoff Lookup."""
    institute: str
    institute_short: str
    institute_type: str = ""        # IIT, NIT, IIIT, GFTI
    state: str = ""                 # State where institute is located
    program: str
    branch_short: str
    seat_type: str
    gender: str
    quota: str
    trends: list[TrendData] = []
    trend_direction: str = ""       # "getting_harder", "getting_easier", "stable"
    predicted_closing_2026: Optional[int] = None
    predicted_range_min: Optional[int] = None
    predicted_range_max: Optional[int] = None


class CompareRequest(BaseModel):
    """Request to compare two colleges."""
    college_a_institute: str
    college_a_program: str
    college_b_institute: str
    college_b_program: str
    seat_type: str = "OPEN"
    gender: str = "Gender-Neutral"
    quota: str = "AI"


class CompareItem(BaseModel):
    """Data for one side of a comparison."""
    institute: str
    institute_short: str
    institute_type: str
    state: str
    program: str
    branch_short: str
    trends: list[TrendData] = []
    latest_closing: Optional[int] = None
    trend_direction: str = ""


class CompareResponse(BaseModel):
    """Response with side-by-side comparison."""
    college_a: CompareItem
    college_b: CompareItem
    recommendation: str = ""

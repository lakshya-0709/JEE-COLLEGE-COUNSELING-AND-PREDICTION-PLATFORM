"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional


class PredictionRequest(BaseModel):
    """Student input for college prediction."""
    jee_main_rank: Optional[int] = Field(None, description="JEE Main AIR rank")
    jee_main_percentile: Optional[float] = Field(None, description="JEE Main percentile (0-100)")
    jee_advanced_rank: Optional[int] = Field(None, description="JEE Advanced AIR rank")
    jee_advanced_percentile: Optional[float] = Field(None, description="JEE Advanced percentile (0-100)")
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
    """Response with multi-year cutoff trend."""
    institute: str
    institute_short: str
    program: str
    branch_short: str
    seat_type: str
    gender: str
    quota: str
    trends: list[TrendData] = []
    trend_direction: str = ""  # "getting_harder", "getting_easier", "stable"


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


class PreferenceListRequest(BaseModel):
    """Request for generating a preference/choice filling list."""
    jee_main_rank: Optional[int] = None
    jee_main_percentile: Optional[float] = None
    jee_advanced_rank: Optional[int] = None
    jee_advanced_percentile: Optional[float] = None
    category: str = "OPEN"
    gender: str = "Gender-Neutral"
    home_state: Optional[str] = None
    preferred_branches: list[str] = Field(default_factory=list)
    institute_types: list[str] = Field(default_factory=list)
    branch_priority: str = Field("balanced", description="branch_first, college_first, or balanced")
    risk_tolerance: str = Field("balanced", description="safe, balanced, or aggressive")


class PreferenceItem(BaseModel):
    """A single item in the preference list."""
    rank_order: int
    institute: str
    institute_short: str
    institute_type: str
    state: str
    program: str
    branch_short: str
    chance_category: str
    closing_rank_latest: Optional[int] = None
    your_rank: int
    reason: str = ""


class PreferenceListResponse(BaseModel):
    """Response with optimized preference list."""
    your_rank: int
    total_choices: int
    strategy: str
    preference_list: list[PreferenceItem] = []

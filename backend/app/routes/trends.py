"""Trends API route — GET /api/trends"""

from fastapi import APIRouter, Query
from app.models.schemas import TrendResponse, TrendData
from app.database import data_store

router = APIRouter()


@router.get("/trends", response_model=TrendResponse)
async def get_cutoff_trends(
    institute: str = Query(..., description="Full institute name"),
    program: str = Query(..., description="Full program name"),
    seat_type: str = Query("OPEN"),
    gender: str = Query("Gender-Neutral"),
    quota: str = Query("AI"),
):
    """Get year-wise cutoff trend for a specific college+program combo."""
    trends = data_store.get_trend(institute, program, seat_type, gender, quota)

    # Get institute metadata
    institutes = data_store.search_institutes(institute[:20])
    inst_meta = institutes[0] if institutes else {"institute_short": institute, "institute_type": "Unknown"}

    # Determine trend direction
    trend_direction = "stable"
    if len(trends) >= 2:
        first = trends[0]["closing_rank"]
        last = trends[-1]["closing_rank"]
        change_pct = (last - first) / first * 100
        if change_pct < -10:
            trend_direction = "getting_harder"  # closing rank decreased = more competitive
        elif change_pct > 10:
            trend_direction = "getting_easier"
        else:
            trend_direction = "stable"

    # Extract branch short from data
    branch_short = ""
    records = data_store.query(institute=institute, program=program)
    if records:
        branch_short = records[0].get("branch_short", "")

    return TrendResponse(
        institute=institute,
        institute_short=inst_meta.get("institute_short", institute),
        program=program,
        branch_short=branch_short,
        seat_type=seat_type,
        gender=gender,
        quota=quota,
        trends=[TrendData(**t) for t in trends],
        trend_direction=trend_direction,
    )

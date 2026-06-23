"""Compare API route — POST /api/compare"""

from fastapi import APIRouter
from app.models.schemas import CompareRequest, CompareResponse, CompareItem, TrendData
from app.database import data_store

router = APIRouter()


@router.post("/compare", response_model=CompareResponse)
async def compare_colleges(request: CompareRequest):
    """Compare two colleges side by side."""

    def build_compare_item(institute: str, program: str) -> CompareItem:
        # Get trend data
        trends = data_store.get_trend(
            institute, program, request.seat_type, request.gender, request.quota
        )

        # Get institute metadata
        records = data_store.query(institute=institute, program=program)
        meta = records[0] if records else {}

        # Trend direction
        trend_direction = "stable"
        if len(trends) >= 2:
            first = trends[0]["closing_rank"]
            last = trends[-1]["closing_rank"]
            change_pct = (last - first) / first * 100
            if change_pct < -10:
                trend_direction = "getting_harder"
            elif change_pct > 10:
                trend_direction = "getting_easier"

        latest_closing = trends[-1]["closing_rank"] if trends else None

        return CompareItem(
            institute=institute,
            institute_short=meta.get("institute_short", institute),
            institute_type=meta.get("institute_type", "Unknown"),
            state=meta.get("state", "Unknown"),
            program=program,
            branch_short=meta.get("branch_short", ""),
            trends=[TrendData(**t) for t in trends],
            latest_closing=latest_closing,
            trend_direction=trend_direction,
        )

    college_a = build_compare_item(request.college_a_institute, request.college_a_program)
    college_b = build_compare_item(request.college_b_institute, request.college_b_program)

    # Generate recommendation
    recommendation = ""
    if college_a.latest_closing and college_b.latest_closing:
        if college_a.latest_closing < college_b.latest_closing:
            recommendation = f"{college_a.institute_short} has a more competitive cutoff (lower closing rank), indicating higher demand."
        elif college_b.latest_closing < college_a.latest_closing:
            recommendation = f"{college_b.institute_short} has a more competitive cutoff (lower closing rank), indicating higher demand."
        else:
            recommendation = "Both colleges have similar cutoff ranks."

    return CompareResponse(
        college_a=college_a,
        college_b=college_b,
        recommendation=recommendation,
    )

"""Trends API route — GET /api/trends"""

import statistics
from fastapi import APIRouter, Query
from app.models.schemas import TrendResponse, TrendData
from app.database import data_store
from app.services.prediction import prediction_service

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

    # Query record metadata directly to avoid prefix matching bugs
    records = data_store.query(institute=institute, program=program)
    inst_short = institute
    inst_type = ""
    inst_state = ""
    branch_short = ""
    if records:
        inst_short = records[0].get("institute_short", institute)
        inst_type = records[0].get("institute_type", "")
        inst_state = records[0].get("state", "")
        branch_short = records[0].get("branch_short", "")

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

    # Predict 2026 closing rank using ML model
    predicted_closing_2026 = prediction_service.predict_closing_rank(
        inst_short, branch_short, seat_type, gender, quota, year=2026
    )

    if predicted_closing_2026 is None and trends:
        sorted_trends = sorted(trends, key=lambda x: x["year"])
        latest_y = sorted_trends[-1]["year"]
        latest_val = sorted_trends[-1]["closing_rank"]
        if len(sorted_trends) >= 2:
            prev_val = sorted_trends[-2]["closing_rank"]
            prev_y = sorted_trends[-2]["year"]
            year_diff = latest_y - prev_y
            annual_change = (latest_val - prev_val) / year_diff
            projected = latest_val + (annual_change * (2026 - latest_y) * 0.5)
            predicted_closing_2026 = max(1, int(projected))
        else:
            predicted_closing_2026 = latest_val

    # Reality-check: clamp ML prediction against historical projection
    # Prevents the ML model from over-extrapolating beyond what history supports
    if predicted_closing_2026 is not None and trends:
        sorted_trends = sorted(trends, key=lambda x: x["year"])
        if len(sorted_trends) >= 2:
            latest_val = sorted_trends[-1]["closing_rank"]
            prev_val = sorted_trends[-2]["closing_rank"]
            year_diff = sorted_trends[-1]["year"] - sorted_trends[-2]["year"]
            annual_change = (latest_val - prev_val) / year_diff
            hist_projected = latest_val + (annual_change * (2026 - sorted_trends[-1]["year"]) * 0.5)
            # Bound ML prediction within ±12% of the historical projection
            lower_bound = hist_projected * 0.88
            upper_bound = hist_projected * 1.12
            predicted_closing_2026 = max(1, int(max(lower_bound, min(upper_bound, predicted_closing_2026))))

    # Calculate expected range bounds using historical volatility
    predicted_range_min = None
    predicted_range_max = None
    if predicted_closing_2026 is not None:
        p = predicted_closing_2026
        margin = None

        # Data-driven: use standard deviation of historical closing ranks
        closing_ranks = [t["closing_rank"] for t in trends if t.get("closing_rank")]
        if len(closing_ranks) >= 3:
            std_dev = statistics.stdev(closing_ranks)
            # 1.5× stdev ≈ 87% confidence band
            margin = max(1, int(std_dev * 1.5))

        # Fallback: percentage-based margins when history is too sparse
        if margin is None or margin < 1:
            if p < 200:
                margin = max(10, int(p * 0.08))
            elif p < 1000:
                margin = max(20, int(p * 0.09))
            else:
                margin = max(50, int(p * 0.10))

        # Floor: ensure the range is never unrealistically narrow
        if p < 200:
            margin = max(5, margin)
        elif p < 1000:
            margin = max(15, margin)
        else:
            margin = max(30, margin)

        predicted_range_min = max(1, p - margin)
        predicted_range_max = p + margin

    return TrendResponse(
        institute=institute,
        institute_short=inst_short,
        institute_type=inst_type,
        state=inst_state,
        program=program,
        branch_short=branch_short,
        seat_type=seat_type,
        gender=gender,
        quota=quota,
        trends=[TrendData(**t) for t in trends],
        trend_direction=trend_direction,
        predicted_closing_2026=predicted_closing_2026,
        predicted_range_min=predicted_range_min,
        predicted_range_max=predicted_range_max,
    )

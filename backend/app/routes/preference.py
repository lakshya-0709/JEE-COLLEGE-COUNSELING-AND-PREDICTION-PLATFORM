"""Preference list API route — POST /api/preference-list"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import PreferenceListRequest, PreferenceListResponse
from app.services.prediction import prediction_service
from app.services.preference_gen import preference_service

router = APIRouter()


@router.post("/preference-list", response_model=PreferenceListResponse)
async def generate_preference_list(request: PreferenceListRequest):
    """Generate an optimized JoSAA choice-filling preference list."""

    # Determine rank
    student_rank = None
    exam_type = "JEE Main"

    if request.jee_advanced_rank:
        student_rank = request.jee_advanced_rank
        exam_type = "JEE Advanced"
    elif request.jee_advanced_percentile:
        student_rank = prediction_service.percentile_to_rank(request.jee_advanced_percentile, "advanced")
        exam_type = "JEE Advanced"
    elif request.jee_main_rank:
        student_rank = request.jee_main_rank
        exam_type = "JEE Main"
    elif request.jee_main_percentile:
        student_rank = prediction_service.percentile_to_rank(request.jee_main_percentile, "main")
        exam_type = "JEE Main"

    if student_rank is None:
        raise HTTPException(status_code=400, detail="Please provide rank or percentile")

    institute_types = request.institute_types
    if not institute_types:
        if exam_type == "JEE Advanced":
            institute_types = ["IIT"]
        else:
            institute_types = ["NIT", "IIIT", "GFTI"]

    result = preference_service.generate_preference_list(
        student_rank=student_rank,
        exam_type=exam_type,
        category=request.category,
        gender=request.gender,
        home_state=request.home_state,
        preferred_branches=request.preferred_branches,
        institute_types=institute_types,
        branch_priority=request.branch_priority,
        risk_tolerance=request.risk_tolerance,
    )

    return PreferenceListResponse(**result)

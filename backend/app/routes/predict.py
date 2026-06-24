"""Prediction API route — POST /api/predict"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.prediction import prediction_service

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_colleges(request: PredictionRequest):
    """
    Predict which colleges a student can get based on their JEE rank.
    Returns colleges grouped by Safe / Moderate / Dream.
    """
    # Determine rank and exam type
    student_rank = None
    exam_type = "JEE Main"

    if request.jee_advanced_rank:
        student_rank = request.jee_advanced_rank
        exam_type = "JEE Advanced"
    elif request.jee_main_rank:
        student_rank = request.jee_main_rank
        exam_type = "JEE Main"

    if student_rank is None:
        raise HTTPException(status_code=400, detail="Please provide either JEE Main or JEE Advanced rank")

    # Set default institute types based on exam
    institute_types = request.institute_types
    if not institute_types:
        if exam_type == "JEE Advanced":
            institute_types = ["IIT"]
        else:
            institute_types = ["NIT", "IIIT", "GFTI"]

    # Get predictions
    results = prediction_service.predict_colleges(
        student_rank=student_rank,
        exam_type=exam_type,
        category=request.category,
        gender=request.gender,
        home_state=request.home_state,
        preferred_branches=request.preferred_branches,
        institute_types=institute_types,
    )

    total = sum(len(results[cat]) for cat in results)

    return PredictionResponse(
        your_rank=student_rank,
        exam_type=exam_type,
        total_results=total,
        safe=results["safe"],
        moderate=results["moderate"],
        dream=results["dream"],
    )

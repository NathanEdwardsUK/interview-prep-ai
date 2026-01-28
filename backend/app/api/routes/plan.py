from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.plan import (
    SuggestNewPlanRequest,
    SuggestChangesRequest,
    ApprovePlanRequest,
    PlanResponse
)
from app.llm.suggest_plan import suggest_plan
from app.llm.suggest_changes import suggest_plan_changes

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/suggest_new", response_model=PlanResponse)
async def suggest_new_plan(
    request: SuggestNewPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new study plan suggestion based on role and user context.
    """
    try:
        result = await suggest_plan(
            role=request.role,
            user_context=request.raw_user_context
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(e)}")


@router.post("/suggest_changes", response_model=PlanResponse)
async def suggest_plan_changes_endpoint(
    request: SuggestChangesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Suggest changes to an existing plan based on progress and feedback.
    """
    try:
        result = await suggest_plan_changes(
            current_plan=request.current_plan,
            role=current_user.current_applying_role or "",
            user_context=request.raw_user_context,
            current_progress=request.current_progress,
            user_feedback=request.user_feedback
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest plan changes: {str(e)}")


@router.post("/approve_plan")
async def approve_plan(
    request: ApprovePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save an approved plan to the database.
    """
    # TODO: Implement plan saving logic
    # This should create PlanTopic records for the user
    return {"status": "success", "message": "Plan approved and saved"}


@router.get("/view", response_model=PlanResponse)
async def view_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's study plan.
    """
    # TODO: Implement plan retrieval logic
    # This should fetch PlanTopic records for the user and format as PlanResponse
    raise HTTPException(status_code=501, detail="Not yet implemented")

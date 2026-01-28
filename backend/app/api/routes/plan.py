from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.plan import PlanTopic, TopicProgress
from app.models.session import RawUserContext
from app.schemas.plan import (
    SuggestNewPlanRequest,
    SuggestChangesRequest,
    ApprovePlanRequest,
    PlanResponse,
    UserContextResponse,
    UserContextRequest,
)
from app.llm.suggest_plan import suggest_plan
from app.llm.suggest_changes import suggest_plan_changes

router = APIRouter(prefix="/plan", tags=["plan"])


def _upsert_user_context(db: Session, user_id: str, context_text: str, append: bool = False) -> None:
    existing = db.query(RawUserContext).filter(RawUserContext.user_id == user_id).first()
    if existing:
        if append:
            existing.context_text = (existing.context_text or "") + "\n\n" + context_text
        else:
            existing.context_text = context_text
    else:
        db.add(RawUserContext(user_id=user_id, context_text=context_text))
    db.commit()


@router.get("/user_context", response_model=UserContextResponse)
async def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve current user's raw context."""
    ctx = db.query(RawUserContext).filter(RawUserContext.user_id == current_user.clerk_user_id).first()
    if not ctx:
        return UserContextResponse(context_text="")
    return UserContextResponse(context_text=ctx.context_text or "")


@router.post("/user_context", response_model=UserContextResponse)
async def update_user_context(
    request: UserContextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update current user's raw context."""
    _upsert_user_context(db, current_user.clerk_user_id, request.context_text, append=False)
    ctx = db.query(RawUserContext).filter(RawUserContext.user_id == current_user.clerk_user_id).first()
    return UserContextResponse(context_text=ctx.context_text or "")


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
        _upsert_user_context(db, current_user.clerk_user_id, request.raw_user_context, append=False)
        result = await suggest_plan(
            role=request.role,
            user_context=request.raw_user_context,
            time_available_minutes=request.time_available_minutes,
            weak_areas=request.weak_areas,
            motivation_level=request.motivation_level,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable. Please try again.",
        )


@router.get("/can_refine")
async def can_refine_plan(
    current_user: User = Depends(get_current_user),
):
    """Return whether the user can request plan refinement today (max once per day)."""
    today = date.today()
    can_refine = current_user.last_plan_refinement_date is None or current_user.last_plan_refinement_date < today
    return {"can_refine": can_refine}


@router.post("/suggest_changes", response_model=PlanResponse)
async def suggest_plan_changes_endpoint(
    request: SuggestChangesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Suggest changes to an existing plan based on progress and feedback.
    Limited to once per day per user.
    """
    today = date.today()
    if current_user.last_plan_refinement_date is not None and current_user.last_plan_refinement_date >= today:
        raise HTTPException(
            status_code=429,
            detail="Plan refinement is limited to once per day. Check back tomorrow.",
        )
    try:
        _upsert_user_context(db, current_user.clerk_user_id, request.raw_user_context, append=True)
        result = await suggest_plan_changes(
            current_plan=request.current_plan,
            role=current_user.current_applying_role or "",
            user_context=request.raw_user_context,
            current_progress=request.current_progress,
            user_feedback=request.user_feedback
        )
        current_user.last_plan_refinement_date = today
        db.commit()
        return result.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable. Please try again.",
        )


@router.post("/approve_plan")
async def approve_plan(
    request: ApprovePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save an approved plan to the database.
    """
    try:
        # Delete existing PlanTopic records for the user
        db.query(PlanTopic).filter(PlanTopic.user_id == current_user.clerk_user_id).delete()
        
        # Create new PlanTopic records from the approved plan
        created_topics = []
        for topic_schema in request.plan.plan_topics:
            plan_topic = PlanTopic(
                user_id=current_user.clerk_user_id,
                name=topic_schema.name,
                description=topic_schema.description,
                planned_daily_study_time=topic_schema.daily_study_minutes,
                priority=topic_schema.priority,
                expected_outcome=topic_schema.expected_outcome,
            )
            db.add(plan_topic)
            created_topics.append(plan_topic)
        
        # Commit the transaction
        db.commit()
        
        # Refresh to get IDs
        for topic in created_topics:
            db.refresh(topic)
        
        return {
            "status": "success",
            "message": "Plan approved and saved",
            "topic_ids": [topic.id for topic in created_topics]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save plan: {str(e)}")


@router.get("/view", response_model=PlanResponse)
async def view_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's study plan from the database.
    """
    topics = (
        db.query(PlanTopic)
        .filter(PlanTopic.user_id == current_user.clerk_user_id)
        .order_by(PlanTopic.priority.asc(), PlanTopic.id.asc())
        .all()
    )

    if not topics:
        raise HTTPException(status_code=404, detail="No plan found for user")

    total_daily_minutes = sum(t.planned_daily_study_time for t in topics)

    # Build a simple overview using current_applying_role and topic data
    overview = {
        "target_role": current_user.current_applying_role or "Interview Candidate",
        "total_daily_minutes": total_daily_minutes,
        "time_horizon_weeks": 8,
        "rationale": "Study plan loaded from your saved topics.",
    }

    # Load progress for each topic
    topic_ids = [t.id for t in topics]
    progress_records = (
        db.query(TopicProgress)
        .filter(
            TopicProgress.user_id == current_user.clerk_user_id,
            TopicProgress.topic_id.in_(topic_ids)
        )
        .all()
    )
    progress_by_topic = {p.topic_id: p for p in progress_records}
    
    plan_topics = [
        {
            "name": t.name,
            "description": t.description or "",
            "priority": t.priority,
            "daily_study_minutes": t.planned_daily_study_time,
            "expected_outcome": t.expected_outcome or "",
            "topic_id": t.id,
            "progress": {
                "strength_rating": progress_by_topic.get(t.id).strength_rating if progress_by_topic.get(t.id) else None,
                "total_time_spent": progress_by_topic.get(t.id).total_time_spent if progress_by_topic.get(t.id) else 0,
            } if progress_by_topic.get(t.id) else None,
        }
        for t in topics
    ]

    return {
        "plan_overview": overview,
        "plan_topics": plan_topics,
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.session import StudySession
from app.schemas.session import StudySessionCreate, StudySessionResponse
from app.schemas.question import (
    GenerateQuestionsResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse
)
from app.llm.generate_questions import generate_questions
from app.llm.evaluate_answer import evaluate_answer
from datetime import datetime

router = APIRouter(prefix="/study", tags=["study"])


@router.post("/start_session", response_model=StudySessionResponse)
async def start_session(
    topic_id: int,
    planned_study_time: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new study session for a topic.
    """
    session = StudySession(
        user_id=current_user.clerk_user_id,
        topic_id=topic_id,
        planned_duration=planned_study_time,
        start_time=datetime.utcnow(),
        last_interaction_time=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put("/end_session/{session_id}", response_model=StudySessionResponse)
async def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a study session and trigger reconciliation.
    """
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.clerk_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.end_time = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    # TODO: Trigger reconciliation process
    # This should call the reconcile_session LLM function
    
    return session


@router.post("/generate_questions/{session_id}", response_model=GenerateQuestionsResponse)
async def generate_questions_endpoint(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate questions for a study session.
    """
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.clerk_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # TODO: Get topic information and previously asked questions
    # For now, using placeholder values
    try:
        result = await generate_questions(
            topic_name="Interview Questions",
            topic_description="General interview preparation",
            previously_asked=None
        )
        return {"questions": [q.model_dump() for q in result.questions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post("/evaluate_answer/{session_id}", response_model=EvaluateAnswerResponse)
async def evaluate_answer_endpoint(
    session_id: int,
    request: EvaluateAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluate a user's answer to a question.
    """
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.clerk_user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # TODO: Get question text and context
    question_text = "Sample question"  # Placeholder
    
    try:
        result = await evaluate_answer(
            question=question_text,
            answer=request.raw_answer,
            question_context=None
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {str(e)}")

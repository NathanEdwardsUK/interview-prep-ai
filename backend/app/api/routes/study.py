from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.session import StudySession
from app.models.question import QuestionAttempt, Question
from app.models.plan import TopicProgress
from app.schemas.session import StudySessionCreate, StudySessionResponse
from app.schemas.question import (
    GenerateQuestionsResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
)
from app.llm.generate_questions import generate_questions
from app.llm.evaluate_answer import evaluate_answer
from app.llm.reconcile_session import reconcile_session
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

    # Gather question attempts for this session
    attempts = (
        db.query(QuestionAttempt, Question)
        .join(Question, Question.id == QuestionAttempt.question_id)
        .filter(QuestionAttempt.study_session_id == session_id)
        .all()
    )

    question_attempt_dicts = [
        {
            "question": question.question,
            "answer": attempt.raw_answer,
            "score": attempt.score_rating,
        }
        for attempt, question in attempts
    ]

    # Call LLM to reconcile the session and summarize performance
    avg_score = None
    if question_attempt_dicts:
        summary = await reconcile_session(question_attempt_dicts)
        best_scores = [qa.best_score for qa in summary.question_attempts]
        if best_scores:
            avg_score = int(sum(best_scores) / len(best_scores))

    # Update topic progress for this user/topic
    topic_progress = (
        db.query(TopicProgress)
        .filter(
            TopicProgress.user_id == current_user.clerk_user_id,
            TopicProgress.topic_id == session.topic_id,
        )
        .first()
    )

    if not topic_progress:
        topic_progress = TopicProgress(
            user_id=current_user.clerk_user_id,
            topic_id=session.topic_id,
            strength_rating=avg_score,
            total_time_spent=session.planned_duration,
        )
        db.add(topic_progress)
    else:
        if avg_score is not None:
            topic_progress.strength_rating = avg_score
        topic_progress.total_time_spent = (topic_progress.total_time_spent or 0) + session.planned_duration

    db.commit()
    db.refresh(session)

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

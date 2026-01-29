from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.session import StudySession
from app.models.question import QuestionAttempt, Question, StoryStructure
from app.models.plan import PlanTopic
from app.models.plan import TopicProgress
from app.schemas.session import StudySessionCreate, StudySessionResponse, StartSessionRequest, StartSessionRequest
from app.schemas.question import (
    GenerateQuestionsResponse,
    EvaluateAnswerRequest,
    EvaluateAnswerResponse,
    GenerateStoryRequest,
    StoryStructureResponse,
    UpdateStoryRequest,
)
from app.llm.generate_questions import generate_questions
from app.llm.evaluate_answer import evaluate_answer
from app.llm.reconcile_session import reconcile_session
from app.llm.generate_story_structure import generate_story_structure
from datetime import datetime, timezone

router = APIRouter(prefix="/study", tags=["study"])


@router.get("/suggested_session")
async def suggested_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Suggest the next topic to study based on priority, time since last session, and strength.
    """
    topics = (
        db.query(PlanTopic)
        .filter(PlanTopic.user_id == current_user.clerk_user_id)
        .order_by(PlanTopic.priority.asc(), PlanTopic.id.asc())
        .all()
    )
    if not topics:
        raise HTTPException(status_code=404, detail="No plan found; create a plan first")
    topic_ids = [t.id for t in topics]
    progress = (
        db.query(TopicProgress)
        .filter(
            TopicProgress.user_id == current_user.clerk_user_id,
            TopicProgress.topic_id.in_(topic_ids),
        )
        .all()
    )
    progress_by_topic = {p.topic_id: p for p in progress}
    last_session_by_topic = {}
    for tid in topic_ids:
        last = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == current_user.clerk_user_id,
                StudySession.topic_id == tid,
            )
            .order_by(StudySession.start_time.desc())
            .first()
        )
        last_session_by_topic[tid] = last
    now = datetime.utcnow()
    candidates = []
    for t in topics:
        last_sess = last_session_by_topic.get(t.id)
        days_since = None
        if last_sess and last_sess.start_time:
            st = last_sess.start_time
            st_naive = st.replace(tzinfo=None) if getattr(st, "tzinfo", None) else st
            days_since = (now - st_naive).days
        prog = progress_by_topic.get(t.id)
        strength = prog.strength_rating if prog else None
        candidates.append((t, days_since, strength))
    def score(c):
        t, days_since, strength = c
        s = 0
        if days_since is None:
            s += 1000
        else:
            s += min(days_since * 50, 500)
        if strength is not None and strength < 6:
            s += (10 - strength) * 20
        s -= t.priority * 10
        return s
    candidates.sort(key=score, reverse=True)
    best = candidates[0][0]
    return {
        "topic_id": best.id,
        "topic_name": best.name,
        "planned_study_time": best.planned_daily_study_time,
        "reason": _suggested_reason(best, last_session_by_topic.get(best.id), progress_by_topic.get(best.id)),
    }


def _suggested_reason(topic: PlanTopic, last_session, progress) -> str:
    if not last_session:
        return f"You haven't studied {topic.name} yet."
    strength = progress.strength_rating if progress else None
    if strength is not None and strength < 6:
        return f"Focus on {topic.name} — strength is {strength}/10."
    return f"Time to practice {topic.name} again."


@router.get("/session/{session_id}", response_model=StudySessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a study session by ID (for timer and session details).
    """
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.clerk_user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/start_session", response_model=StudySessionResponse)
async def start_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new study session for a topic.
    """
    session = StudySession(
        user_id=current_user.clerk_user_id,
        topic_id=request.topic_id,
        planned_duration=request.planned_study_time,
        start_time=datetime.now(timezone.utc),
        last_interaction_time=datetime.now(timezone.utc),
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
    
    session.end_time = datetime.now(timezone.utc)

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

    # Call LLM to reconcile the session and summarize performance (graceful: session still ends if LLM fails)
    avg_score = None
    if question_attempt_dicts:
        try:
            summary = await reconcile_session(question_attempt_dicts)
            best_scores = [qa.best_score for qa in summary.question_attempts]
            if best_scores:
                avg_score = int(sum(best_scores) / len(best_scores))
        except Exception:
            pass  # Session still ends; topic progress updated without avg_score

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
    
    # Get topic information
    topic = db.query(PlanTopic).filter(PlanTopic.id == session.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found for session")
    
    # Get previously asked questions for this topic with their attempt scores
    previously_asked = []
    existing_questions = (
        db.query(Question, QuestionAttempt)
        .join(QuestionAttempt, Question.id == QuestionAttempt.question_id)
        .filter(Question.topic_id == session.topic_id)
        .all()
    )
    
    for question, attempt in existing_questions:
        previously_asked.append({
            "question": question.question,
            "rating": attempt.score_rating or 0
        })
    
    try:
        result = await generate_questions(
            topic_name=topic.name,
            topic_description=topic.description or "",
            previously_asked=previously_asked if previously_asked else None
        )
        return {"questions": [q.model_dump() for q in result.questions]}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable. Please try again.",
        )


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
    
    # Get topic for context
    topic = db.query(PlanTopic).filter(PlanTopic.id == session.topic_id).first()
    question_context = topic.description if topic else None
    
    try:
        # Evaluate the answer using LLM
        result = await evaluate_answer(
            question=request.question,
            answer=request.raw_answer,
            question_context=question_context
        )
        
        # Find or create Question record for this topic
        question = (
            db.query(Question)
            .filter(
                Question.topic_id == session.topic_id,
                Question.question == request.question
            )
            .first()
        )
        
        if not question:
            question = Question(
                topic_id=session.topic_id,
                question=request.question,
                answer_anchors=[{"name": a.get("name", ""), "anchor": a.get("anchor", "")} for a in result.anchors] if result.anchors else None,
            )
            db.add(question)
            db.flush()  # Get question.id without committing
        else:
            # Update anchors from latest evaluation (best anchors)
            question.answer_anchors = [{"name": a.get("name", ""), "anchor": a.get("anchor", "")} for a in result.anchors] if result.anchors else question.answer_anchors
        
        # Create QuestionAttempt record
        attempt = QuestionAttempt(
            question_id=question.id,
            study_session_id=session_id,
            raw_answer=request.raw_answer,
            score_rating=result.score,
            answer_time_seconds=request.answer_time_seconds,
        )
        db.add(attempt)
        
        # Update session last interaction time
        session.last_interaction_time = datetime.now(timezone.utc)
        
        db.commit()
        
        return result.model_dump()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable. Please try again.",
        )


@router.post("/generate_story/{session_id}")
async def generate_story_endpoint(
    session_id: int,
    request: GenerateStoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a story structure for a question and save it.
    Returns question_id, story_id, and structure_text.
    """
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.clerk_user_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    topic = db.query(PlanTopic).filter(PlanTopic.id == session.topic_id).first()
    topic_context = topic.description if topic else None
    try:
        result = await generate_story_structure(
            question=request.question,
            topic_context=topic_context,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="LLM temporarily unavailable. Please try again.",
        )
    # Find or create Question
    question = (
        db.query(Question)
        .filter(
            Question.topic_id == session.topic_id,
            Question.question == request.question,
        )
        .first()
    )
    if not question:
        question = Question(
            topic_id=session.topic_id,
            question=request.question,
            answer_anchors=None,
        )
        db.add(question)
        db.flush()
    # Create or update StoryStructure (one per user per question)
    story = (
        db.query(StoryStructure)
        .filter(
            StoryStructure.question_id == question.id,
            StoryStructure.user_id == current_user.clerk_user_id,
        )
        .first()
    )
    if story:
        story.structure_text = result.structure_text
    else:
        story = StoryStructure(
            question_id=question.id,
            user_id=current_user.clerk_user_id,
            structure_text=result.structure_text,
        )
        db.add(story)
        db.flush()
    db.commit()
    db.refresh(story)
    return {
        "question_id": question.id,
        "story_id": story.id,
        "structure_text": story.structure_text,
        "created_at": story.created_at.isoformat() if hasattr(story.created_at, "isoformat") else str(story.created_at),
        "updated_at": story.updated_at.isoformat() if hasattr(story.updated_at, "isoformat") else str(story.updated_at),
    }


@router.get("/story/{question_id}")
async def get_story_endpoint(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get story structure for a question (current user)."""
    story = (
        db.query(StoryStructure)
        .filter(
            StoryStructure.question_id == question_id,
            StoryStructure.user_id == current_user.clerk_user_id,
        )
        .first()
    )
    if not story:
        raise HTTPException(status_code=404, detail="No story found for this question")
    return {
        "id": story.id,
        "question_id": story.question_id,
        "structure_text": story.structure_text,
        "created_at": story.created_at.isoformat() if hasattr(story.created_at, "isoformat") else str(story.created_at),
        "updated_at": story.updated_at.isoformat() if hasattr(story.updated_at, "isoformat") else str(story.updated_at),
    }


@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    topic_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's study sessions with topic name, date, duration, questions answered, average score.
    """
    q = (
        db.query(StudySession)
        .filter(StudySession.user_id == current_user.clerk_user_id)
    )
    if topic_id is not None:
        q = q.filter(StudySession.topic_id == topic_id)
    sessions = (
        q.order_by(StudySession.start_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    topic_ids = list({s.topic_id for s in sessions})
    topics = (
        db.query(PlanTopic)
        .filter(PlanTopic.id.in_(topic_ids))
        .all()
    ) if topic_ids else []
    topic_by_id = {t.id: t for t in topics}
    result = []
    for s in sessions:
        topic = topic_by_id.get(s.topic_id)
        topic_name = topic.name if topic else f"Topic {s.topic_id}"
        attempts = (
            db.query(QuestionAttempt)
            .filter(QuestionAttempt.study_session_id == s.id)
            .all()
        )
        questions_answered = len(attempts)
        scores = [a.score_rating for a in attempts if a.score_rating is not None]
        avg_score = int(sum(scores) / len(scores)) if scores else None
        start = s.start_time
        end = s.end_time
        result.append({
            "id": s.id,
            "topic_id": s.topic_id,
            "topic_name": topic_name,
            "start_time": start.isoformat() if hasattr(start, "isoformat") else str(start),
            "end_time": end.isoformat() if end and hasattr(end, "isoformat") else (str(end) if end else None),
            "planned_duration": s.planned_duration,
            "questions_answered": questions_answered,
            "average_score": avg_score,
        })
    return {"sessions": result}


@router.put("/story/{story_id}")
async def update_story_endpoint(
    story_id: int,
    request: UpdateStoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update story structure text."""
    story = (
        db.query(StoryStructure)
        .filter(
            StoryStructure.id == story_id,
            StoryStructure.user_id == current_user.clerk_user_id,
        )
        .first()
    )
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    story.structure_text = request.structure_text
    db.commit()
    db.refresh(story)
    return {
        "id": story.id,
        "question_id": story.question_id,
        "structure_text": story.structure_text,
        "created_at": story.created_at.isoformat() if hasattr(story.created_at, "isoformat") else str(story.created_at),
        "updated_at": story.updated_at.isoformat() if hasattr(story.updated_at, "isoformat") else str(story.updated_at),
    }

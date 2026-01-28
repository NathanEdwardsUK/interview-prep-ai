from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.clerk_user_id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("plan_topics.id"), nullable=False, index=True)
    planned_duration = Column(Integer, nullable=False)  # in minutes
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_interaction_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="study_sessions")
    plan_topic = relationship("PlanTopic", back_populates="study_sessions")
    question_attempts = relationship("QuestionAttempt", back_populates="study_session", cascade="all, delete-orphan")


class RawUserContext(Base):
    __tablename__ = "raw_user_context"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.clerk_user_id"), nullable=False, unique=True, index=True)
    context_text = Column(String, nullable=False)  # Stores all user experience details as text

    # Relationships
    user = relationship("User", back_populates="raw_user_context")

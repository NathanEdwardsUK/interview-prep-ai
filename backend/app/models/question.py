from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("plan_topics.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer_anchors = Column(JSON, nullable=True)  # Stores answer anchors as JSON

    # Relationships
    plan_topic = relationship("PlanTopic", back_populates="questions")
    question_attempts = relationship("QuestionAttempt", back_populates="question", cascade="all, delete-orphan")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    study_session_id = Column(Integer, ForeignKey("study_sessions.id"), nullable=False, index=True)
    raw_answer = Column(Text, nullable=False)
    score_rating = Column(Integer, nullable=True)  # Rating from 1-10

    # Relationships
    question = relationship("Question", back_populates="question_attempts")
    study_session = relationship("StudySession", back_populates="question_attempts")

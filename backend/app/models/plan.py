from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class PlanTopic(Base):
    __tablename__ = "plan_topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.clerk_user_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    planned_daily_study_time = Column(Integer, nullable=False)  # in minutes
    priority = Column(Integer, nullable=False)  # 1 = highest priority

    # Relationships
    user = relationship("User", back_populates="plan_topics")
    topic_progress = relationship("TopicProgress", back_populates="plan_topic", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="plan_topic", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="plan_topic")


class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.clerk_user_id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("plan_topics.id"), nullable=False, index=True)
    strength_rating = Column(Integer, nullable=True)  # Rating from 1-10
    total_time_spent = Column(Integer, default=0)  # in minutes

    # Relationships
    user = relationship("User", back_populates="topic_progress")
    plan_topic = relationship("PlanTopic", back_populates="topic_progress")

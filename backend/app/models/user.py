from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    clerk_user_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    current_applying_role = Column(String, nullable=True)

    # Relationships
    plan_topics = relationship("PlanTopic", back_populates="user", cascade="all, delete-orphan")
    topic_progress = relationship("TopicProgress", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    raw_user_context = relationship("RawUserContext", back_populates="user", cascade="all, delete-orphan", uselist=False)

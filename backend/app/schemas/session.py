from pydantic import BaseModel
from datetime import datetime
from typing import List


class StudySessionBase(BaseModel):
    topic_id: int
    planned_duration: int


class StudySessionCreate(StudySessionBase):
    pass


class StartSessionRequest(BaseModel):
    topic_id: int
    planned_study_time: int


class StudySessionResponse(StudySessionBase):
    id: int
    user_id: str
    start_time: datetime
    last_interaction_time: datetime
    end_time: datetime | None = None

    class Config:
        from_attributes = True


class TopicProgressBase(BaseModel):
    topic_id: int
    strength_rating: int | None = None
    total_time_spent: int = 0


class TopicProgressResponse(TopicProgressBase):
    id: int
    user_id: str

    class Config:
        from_attributes = True


class RawUserContextBase(BaseModel):
    context_text: str


class RawUserContextResponse(RawUserContextBase):
    id: int
    user_id: str

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import List, Dict, Any


class QuestionBase(BaseModel):
    question: str
    answer_anchors: Dict[str, Any] | None = None


class QuestionCreate(QuestionBase):
    topic_id: int


class QuestionResponse(QuestionBase):
    id: int
    topic_id: int

    class Config:
        from_attributes = True


class QuestionAttemptBase(BaseModel):
    raw_answer: str
    score_rating: int | None = None


class QuestionAttemptCreate(QuestionAttemptBase):
    question_id: int
    study_session_id: int


class QuestionAttemptResponse(QuestionAttemptBase):
    id: int
    question_id: int
    study_session_id: int

    class Config:
        from_attributes = True


class GenerateQuestionsResponse(BaseModel):
    questions: List[Dict[str, Any]]


class EvaluateAnswerRequest(BaseModel):
    question: str  # The actual question text
    raw_answer: str
    answer_time_seconds: int | None = None  # Time spent answering in seconds


class EvaluateAnswerResponse(BaseModel):
    score: int
    positive_feedback: List[str]
    improvement_areas: List[str]
    anchors: List[Dict[str, str]]


class GenerateStoryRequest(BaseModel):
    question: str


class StoryStructureResponse(BaseModel):
    id: int
    question_id: int
    structure_text: str
    created_at: str
    updated_at: str


class UpdateStoryRequest(BaseModel):
    structure_text: str

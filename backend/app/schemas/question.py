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
    question_id: int
    raw_answer: str


class EvaluateAnswerResponse(BaseModel):
    score: int
    positive_feedback: List[str]
    improvement_areas: List[str]
    anchors: List[Dict[str, str]]

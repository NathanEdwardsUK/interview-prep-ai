"""
LLM Mode Definitions

Each mode defines the input/output schema and prompt template for a specific LLM operation.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


# SuggestPlan Schema
class PlanOverview(BaseModel):
    target_role: str
    total_daily_minutes: int
    time_horizon_weeks: int
    rationale: str  # max 60 words


class PlanTopicSchema(BaseModel):
    name: str  # max 3 words
    description: str  # max 20 words
    priority: int  # 1 = highest priority
    daily_study_minutes: int
    expected_outcome: str  # max 15 words


class SuggestPlanResponse(BaseModel):
    plan_overview: PlanOverview
    plan_topics: List[PlanTopicSchema]


# GenerateQuestions Schema
class QuestionSchema(BaseModel):
    question: str  # max 30 words
    status: str  # "new" | "redo"
    redo_reason: str | None = None  # "weak_answer" | "incomplete" | "time_pressure" | "high_value"
    difficulty: str  # "easy" | "medium" | "hard"


class GenerateQuestionsResponse(BaseModel):
    questions: List[QuestionSchema]


# EvaluateAnswer Schema
class Anchor(BaseModel):
    name: str  # max 3 words
    anchor: str  # max 50 words


class EvaluateAnswerResponse(BaseModel):
    score: int  # 1-10
    positive_feedback: List[str]  # 0-3 items, max 30 words each
    improvement_areas: List[str]  # 0-3 items, max 30 words each
    anchors: List[Anchor]


# ReconcileSession Schema
class BestAnchor(BaseModel):
    name: str  # max 3 words
    anchor: str  # max 50 words


class QuestionAttemptSummary(BaseModel):
    question: str  # max 30 words
    attempts: int
    best_score: int  # 1-10
    best_anchors: List[BestAnchor]


class ReconcileSessionResponse(BaseModel):
    question_attempts: List[QuestionAttemptSummary]


# GenerateStoryStructure Schema
class GenerateStoryStructureResponse(BaseModel):
    structure_text: str  # Structured story outline for the question


# Mode definitions with schemas
MODES = {
    "suggest_plan": {
        "response_schema": SuggestPlanResponse.model_json_schema(),
        "max_tokens": 2000
    },
    "suggest_plan_changes": {
        "response_schema": SuggestPlanResponse.model_json_schema(),
        "max_tokens": 2000
    },
    "generate_questions": {
        "response_schema": GenerateQuestionsResponse.model_json_schema(),
        "max_tokens": 3000
    },
    "evaluate_answer": {
        "response_schema": EvaluateAnswerResponse.model_json_schema(),
        "max_tokens": 2000
    },
    "reconcile_session": {
        "response_schema": ReconcileSessionResponse.model_json_schema(),
        "max_tokens": 4000
    },
    "generate_story_structure": {
        "response_schema": GenerateStoryStructureResponse.model_json_schema(),
        "max_tokens": 2000
    }
}

from pydantic import BaseModel
from typing import List


class PlanTopicBase(BaseModel):
    name: str
    description: str | None = None
    planned_daily_study_time: int
    priority: int


class PlanTopicCreate(PlanTopicBase):
    pass


class PlanTopicResponse(PlanTopicBase):
    id: int
    user_id: str

    class Config:
        from_attributes = True


class PlanOverview(BaseModel):
    target_role: str
    total_daily_minutes: int
    time_horizon_weeks: int
    rationale: str


class PlanTopicSchema(BaseModel):
    name: str
    description: str
    priority: int
    daily_study_minutes: int
    expected_outcome: str
    topic_id: int | None = None


class PlanResponse(BaseModel):
    plan_overview: PlanOverview
    plan_topics: List[PlanTopicSchema]


class SuggestNewPlanRequest(BaseModel):
    role: str
    raw_user_context: str
    time_available_minutes: int | None = None
    weak_areas: List[str] | None = None
    motivation_level: str | None = None  # e.g. "low", "medium", "high" or "1"-"10"


class SuggestChangesRequest(BaseModel):
    current_plan: dict
    raw_user_context: str
    current_progress: dict | None = None
    user_feedback: List[dict] | None = None


class ApprovePlanRequest(BaseModel):
    plan: PlanResponse


class UserContextResponse(BaseModel):
    context_text: str


class UserContextRequest(BaseModel):
    context_text: str

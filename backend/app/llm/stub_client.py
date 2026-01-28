"""
Stub LLM Client for Testing

Returns hardcoded responses matching the expected schemas.
This allows for fast, deterministic tests without API calls.
"""

from typing import Any, Dict
from app.llm.client import LLMClient
from app.llm.modes import SuggestPlanResponse, PlanOverview, PlanTopicSchema


class StubLLMClient(LLMClient):
    """Stub LLM client that returns hardcoded responses for testing"""
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate structured output matching the provided schema.
        Returns hardcoded responses based on the schema type.
        """
        # Determine which response to return based on schema structure
        # Check if it's a SuggestPlanResponse schema
        if "plan_overview" in response_schema.get("properties", {}):
            return self._get_suggest_plan_response()
        
        # For other schemas, return empty/default responses
        # This can be extended as needed
        return {}
    
    def _get_suggest_plan_response(self) -> Dict[str, Any]:
        """Return a hardcoded SuggestPlanResponse"""
        response = SuggestPlanResponse(
            plan_overview=PlanOverview(
                target_role="Software Engineer",
                total_daily_minutes=120,
                time_horizon_weeks=8,
                rationale="Focused plan covering core algorithms, system design, and behavioral questions over 8 weeks."
            ),
            plan_topics=[
                PlanTopicSchema(
                    name="Data Structures",
                    description="Arrays, linked lists, trees, graphs",
                    priority=1,
                    daily_study_minutes=30,
                    expected_outcome="Master core data structures"
                ),
                PlanTopicSchema(
                    name="Algorithms",
                    description="Sorting, searching, dynamic programming",
                    priority=2,
                    daily_study_minutes=40,
                    expected_outcome="Solve medium difficulty problems"
                ),
                PlanTopicSchema(
                    name="System Design",
                    description="Scalability, distributed systems, databases",
                    priority=3,
                    daily_study_minutes=30,
                    expected_outcome="Design scalable systems"
                ),
                PlanTopicSchema(
                    name="Behavioral Questions",
                    description="STAR method, leadership, teamwork",
                    priority=4,
                    daily_study_minutes=20,
                    expected_outcome="Articulate experiences clearly"
                )
            ]
        )
        # Convert to dict format that matches what the real client returns
        return response.model_dump()

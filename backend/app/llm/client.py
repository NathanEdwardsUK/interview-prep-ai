from abc import ABC, abstractmethod
from typing import Any, Dict
from app.config import settings
import openai
from anthropic import Anthropic
from app.llm.modes import (
    SuggestPlanResponse, PlanOverview, PlanTopicSchema,
    GenerateQuestionsResponse, QuestionSchema,
    EvaluateAnswerResponse, Anchor,
    ReconcileSessionResponse, QuestionAttemptSummary, BestAnchor,
    GenerateStoryStructureResponse,
)


class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate structured output matching the provided schema"""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI client implementation"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI"""
        try:
            # Try using structured outputs (beta feature)
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Always respond with valid JSON matching the requested schema."},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_schema,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Parse the response
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                return response.choices[0].message.parsed
            else:
                # Fallback to JSON parsing if structured output not available
                import json
                content = response.choices[0].message.content
                return json.loads(content)
        except Exception:
            # Fallback to regular chat completion with JSON mode
            import json
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Always respond with valid JSON matching this schema: " + str(response_schema)},
                    {"role": "user", "content": prompt + "\n\nRespond with valid JSON only, no other text."}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)


class AnthropicClient(LLMClient):
    """Anthropic client implementation"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate structured output using Anthropic"""
        # Anthropic uses tool use for structured outputs
        # For now, we'll use JSON mode and parse manually
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": f"{prompt}\n\nRespond with valid JSON matching this schema: {response_schema}"}
            ]
        )
        
        import json
        content = response.content[0].text
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        return json.loads(content)


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
        # Detect schema type by checking properties
        props = response_schema.get("properties", {})
        
        if "plan_overview" in props:
            return self._get_suggest_plan_response()
        elif "questions" in props:
            return self._get_generate_questions_response()
        elif "score" in props and "positive_feedback" in props:
            return self._get_evaluate_answer_response()
        elif "question_attempts" in props:
            return self._get_reconcile_session_response()
        elif "structure_text" in props:
            return self._get_generate_story_structure_response()
        
        # For other schemas, return empty/default responses
        return {}
    
    def _get_suggest_plan_response(self) -> Dict[str, Any]:
        """Return a hardcoded SuggestPlanResponse"""
        response = SuggestPlanResponse(
            plan_overview=PlanOverview(
                target_role="Software Engineer",
                total_daily_minutes=120,
                time_horizon_weeks=8,
                rationale="Focused plan covering core algorithms, system design, and behavioral questions over 8 weeks.",
            ),
            plan_topics=[
                PlanTopicSchema(
                    name="Data Structures",
                    description="Arrays, linked lists, trees, graphs",
                    priority=1,
                    daily_study_minutes=30,
                    expected_outcome="Master core data structures",
                ),
                PlanTopicSchema(
                    name="Algorithms",
                    description="Sorting, searching, dynamic programming",
                    priority=2,
                    daily_study_minutes=40,
                    expected_outcome="Solve medium difficulty problems",
                ),
                PlanTopicSchema(
                    name="System Design",
                    description="Scalability, distributed systems, databases",
                    priority=3,
                    daily_study_minutes=30,
                    expected_outcome="Design scalable systems",
                ),
                PlanTopicSchema(
                    name="Behavioral Questions",
                    description="STAR method, leadership, teamwork",
                    priority=4,
                    daily_study_minutes=20,
                    expected_outcome="Articulate experiences clearly",
                ),
            ],
        )
        return response.model_dump()
    
    def _get_generate_questions_response(self) -> Dict[str, Any]:
        """Return a hardcoded GenerateQuestionsResponse"""
        response = GenerateQuestionsResponse(
            questions=[
                QuestionSchema(
                    question="Explain the difference between a stack and a queue.",
                    status="new",
                    redo_reason=None,
                    difficulty="easy"
                ),
                QuestionSchema(
                    question="How would you implement a binary search tree?",
                    status="new",
                    redo_reason=None,
                    difficulty="medium"
                ),
                QuestionSchema(
                    question="Design a system to handle 1 million requests per second.",
                    status="new",
                    redo_reason=None,
                    difficulty="hard"
                ),
            ]
        )
        return response.model_dump()
    
    def _get_evaluate_answer_response(self) -> Dict[str, Any]:
        """Return a hardcoded EvaluateAnswerResponse"""
        response = EvaluateAnswerResponse(
            score=7,
            positive_feedback=[
                "Good structure and clear explanation",
                "Demonstrated understanding of key concepts"
            ],
            improvement_areas=[
                "Could provide more concrete examples",
                "Consider discussing edge cases"
            ],
            anchors=[
                Anchor(name="Core concept", anchor="The fundamental principle that explains the main idea"),
                Anchor(name="Example", anchor="A practical illustration of how this applies in real scenarios")
            ]
        )
        return response.model_dump()
    
    def _get_reconcile_session_response(self) -> Dict[str, Any]:
        """Return a hardcoded ReconcileSessionResponse"""
        response = ReconcileSessionResponse(
            question_attempts=[
                QuestionAttemptSummary(
                    question="Explain the difference between a stack and a queue.",
                    attempts=1,
                    best_score=7,
                    best_anchors=[
                        BestAnchor(name="LIFO vs FIFO", anchor="Stack uses Last In First Out, queue uses First In First Out")
                    ]
                )
            ]
        )
        return response.model_dump()
    
    def _get_generate_story_structure_response(self) -> Dict[str, Any]:
        """Return a hardcoded GenerateStoryStructureResponse"""
        response = GenerateStoryStructureResponse(
            structure_text="""## Situation
- [Describe the context and background]
- [When and where did this happen?]

## Task
- [What was your responsibility or goal?]
- [What challenges did you face?]

## Action
- [What specific steps did you take?]
- [How did you collaborate or lead?]

## Result
- [What was the outcome?]
- [What did you learn?]"""
        )
        return response.model_dump()


def get_llm_client() -> LLMClient:
    """Factory function to get the appropriate LLM client"""
    if settings.USE_STUB_LLM:
        return StubLLMClient()
    elif settings.LLM_PROVIDER == "openai":
        return OpenAIClient()
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

from app.llm.client import get_llm_client
from app.llm.modes import MODES, SuggestPlanResponse
from app.llm.retry import with_retry


async def suggest_plan(
    role: str,
    user_context: str,
    time_available_minutes: int | None = None,
    weak_areas: list[str] | None = None,
    motivation_level: str | None = None,
) -> SuggestPlanResponse:
    """
    Generate a personalized study plan based on role and user context.
    """
    client = get_llm_client()
    extra = []
    if time_available_minutes is not None:
        extra.append(f"Time available per day: {time_available_minutes} minutes.")
    if weak_areas:
        extra.append(f"Areas of weakness / to focus on: {', '.join(weak_areas)}.")
    if motivation_level:
        extra.append(f"Motivation / capacity level: {motivation_level}.")
    extra_text = "\n".join(extra) if extra else ""
    prompt = f"""You are an expert interview coach. Create a personalized study plan for interview preparation.

User's Target Role: {role}

User Context:
{user_context}
{f'\n\nAdditional preferences:\n{extra_text}' if extra_text else ''}

Based on this information, create a structured study plan that:
1. Breaks down the interview preparation into key topics/categories
2. Allocates appropriate daily study time for each topic
3. Prioritizes topics based on importance and user's weaknesses
4. Sets realistic time horizons
5. Provides clear expected outcomes for each topic

Consider:
- The specific requirements of the role
- Areas where the user may need more practice
- Balanced time allocation across all topics
- Realistic daily time commitments

Respond with a JSON object matching the required schema."""
    
    mode_config = MODES["suggest_plan"]
    response = await with_retry(
        lambda: client.generate_structured(
            prompt=prompt,
            response_schema=mode_config["response_schema"],
            max_tokens=mode_config["max_tokens"],
            temperature=0.7,
        )
    )
    return SuggestPlanResponse(**response)

from app.llm.client import get_llm_client
from app.llm.modes import MODES, SuggestPlanResponse


async def suggest_plan(role: str, user_context: str) -> SuggestPlanResponse:
    """
    Generate a personalized study plan based on role and user context.
    
    Args:
        role: The role the user is applying for
        user_context: Raw user context/story about their experience
    
    Returns:
        SuggestPlanResponse with plan overview and topics
    """
    client = get_llm_client()
    
    prompt = f"""You are an expert interview coach. Create a personalized study plan for interview preparation.

User's Target Role: {role}

User Context:
{user_context}

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
    response = await client.generate_structured(
        prompt=prompt,
        response_schema=mode_config["response_schema"],
        max_tokens=mode_config["max_tokens"],
        temperature=0.7
    )
    
    return SuggestPlanResponse(**response)

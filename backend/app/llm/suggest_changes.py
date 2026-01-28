from app.llm.client import get_llm_client
from app.llm.modes import MODES, SuggestPlanResponse
from app.llm.retry import with_retry


async def suggest_plan_changes(
    current_plan: dict,
    role: str,
    user_context: str,
    current_progress: dict | None = None,
    user_feedback: list[dict] | None = None
) -> SuggestPlanResponse:
    """
    Suggest changes to an existing study plan based on progress and feedback.
    
    Args:
        current_plan: Current plan structure
        role: The role the user is applying for
        user_context: Raw user context/story
        current_progress: Progress data on plan topics
        user_feedback: User feedback on the current plan
    
    Returns:
        SuggestPlanResponse with updated plan
    """
    client = get_llm_client()
    
    progress_text = ""
    if current_progress:
        progress_text = f"\n\nCurrent Progress:\n{current_progress}"
    
    feedback_text = ""
    if user_feedback:
        feedback_text = f"\n\nUser Feedback:\n{user_feedback}"
    
    prompt = f"""You are an expert interview coach. Analyze the current study plan and suggest improvements.

User's Target Role: {role}

Current Plan:
{current_plan}

User Context:
{user_context}{progress_text}{feedback_text}

Based on the current plan, user progress, and feedback, suggest an updated plan that:
1. Adjusts time allocation based on progress (spend more time on weak areas, less on mastered topics)
2. Re-prioritizes topics if needed
3. Maintains realistic daily time commitments
4. Addresses any user feedback or concerns
5. Explains the rationale for changes

Respond with a JSON object matching the required schema."""
    
    mode_config = MODES["suggest_plan_changes"]
    response = await with_retry(
        lambda: client.generate_structured(
            prompt=prompt,
            response_schema=mode_config["response_schema"],
            max_tokens=mode_config["max_tokens"],
            temperature=0.7,
        )
    )
    return SuggestPlanResponse(**response)

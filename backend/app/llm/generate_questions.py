from app.llm.client import get_llm_client
from app.llm.modes import MODES, GenerateQuestionsResponse


async def generate_questions(
    topic_name: str,
    topic_description: str,
    previously_asked: list[dict] | None = None
) -> GenerateQuestionsResponse:
    """
    Generate interview questions for a specific topic.
    
    Args:
        topic_name: Name of the topic
        topic_description: Description of the topic
        previously_asked: List of previously asked questions with their ratings
    
    Returns:
        GenerateQuestionsResponse with list of questions
    """
    client = get_llm_client()
    
    previous_questions_text = ""
    if previously_asked:
        previous_questions_text = "\n\nPreviously Asked Questions:\n"
        for q in previously_asked:
            question = q.get("question", "")
            rating = q.get("rating", "N/A")
            previous_questions_text += f"- {question} (Rating: {rating})\n"
    
    prompt = f"""You are an expert interview coach. Generate interview questions for practice.

Topic: {topic_name}
Description: {topic_description}{previous_questions_text}

Generate a mix of questions that:
1. Cover different aspects of the topic
2. Vary in difficulty (easy, medium, hard)
3. Include both new questions and questions to redo (if previous attempts were weak)
4. Focus on areas that need more practice

For questions marked as "redo", include the reason (weak_answer, incomplete, time_pressure, or high_value).

Respond with a JSON object matching the required schema."""
    
    mode_config = MODES["generate_questions"]
    response = await client.generate_structured(
        prompt=prompt,
        response_schema=mode_config["response_schema"],
        max_tokens=mode_config["max_tokens"],
        temperature=0.8
    )
    
    return GenerateQuestionsResponse(**response)

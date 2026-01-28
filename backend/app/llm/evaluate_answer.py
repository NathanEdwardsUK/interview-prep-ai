from app.llm.client import get_llm_client
from app.llm.modes import MODES, EvaluateAnswerResponse


async def evaluate_answer(
    question: str,
    answer: str,
    question_context: str | None = None
) -> EvaluateAnswerResponse:
    """
    Evaluate a user's answer to an interview question.
    
    Args:
        question: The interview question
        answer: The user's answer
        question_context: Additional context about the question (topic, difficulty, etc.)
    
    Returns:
        EvaluateAnswerResponse with score, feedback, and anchors
    """
    client = get_llm_client()
    
    context_text = ""
    if question_context:
        context_text = f"\n\nQuestion Context: {question_context}"
    
    prompt = f"""You are an expert interview coach. Evaluate the following interview answer.

Question: {question}{context_text}

User's Answer:
{answer}

Evaluate this answer and provide:
1. A score from 1-10 (1 = very bad, 10 = very good)
2. 0-3 positive feedback points (what they did well, max 30 words each)
3. 0-3 improvement areas (what could be better, max 30 words each)
4. Answer anchors (key points that should be covered, max 3 words for name, max 50 words for anchor)

Be constructive and specific. Focus on helping the user improve.

Respond with a JSON object matching the required schema."""
    
    mode_config = MODES["evaluate_answer"]
    response = await client.generate_structured(
        prompt=prompt,
        response_schema=mode_config["response_schema"],
        max_tokens=mode_config["max_tokens"],
        temperature=0.5
    )
    
    return EvaluateAnswerResponse(**response)

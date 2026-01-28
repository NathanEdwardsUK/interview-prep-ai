from app.llm.client import get_llm_client
from app.llm.modes import MODES, ReconcileSessionResponse


async def reconcile_session(question_attempts: list[dict]) -> ReconcileSessionResponse:
    """
    Reconcile a study session by summarizing question attempts and updating progress.
    
    Args:
        question_attempts: List of question attempts with scores and answers
    
    Returns:
        ReconcileSessionResponse with summarized attempts
    """
    client = get_llm_client()
    
    attempts_text = "\n\nQuestion Attempts:\n"
    for i, attempt in enumerate(question_attempts, 1):
        question = attempt.get("question", "")
        answer = attempt.get("answer", "")
        score = attempt.get("score", "N/A")
        attempts_text += f"\n{i}. Question: {question}\n"
        attempts_text += f"   Answer: {answer}\n"
        attempts_text += f"   Score: {score}\n"
    
    prompt = f"""You are an expert interview coach. Reconcile a study session by analyzing all question attempts.

{attempts_text}

For each question, provide:
1. The question text (max 30 words)
2. Number of attempts made
3. Best score achieved (1-10)
4. Best answer anchors (key points from the best attempt, max 3 words for name, max 50 words for anchor)

This summary will be used to track progress and plan future study sessions.

Respond with a JSON object matching the required schema."""
    
    mode_config = MODES["reconcile_session"]
    response = await client.generate_structured(
        prompt=prompt,
        response_schema=mode_config["response_schema"],
        max_tokens=mode_config["max_tokens"],
        temperature=0.6
    )
    
    return ReconcileSessionResponse(**response)

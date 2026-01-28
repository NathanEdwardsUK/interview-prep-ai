from app.llm.client import get_llm_client
from app.llm.modes import MODES, GenerateStoryStructureResponse
from app.llm.retry import with_retry


async def generate_story_structure(question: str, topic_context: str | None = None) -> GenerateStoryStructureResponse:
    """
    Generate a structured story outline for answering a behavioral/interview question.
    """
    client = get_llm_client()
    context_text = f"\n\nTopic context: {topic_context}" if topic_context else ""
    prompt = f"""You are an expert interview coach. Generate a structured story outline to help the user answer this interview question using the STAR method (Situation, Task, Action, Result) or similar framework.

Question: {question}{context_text}

Provide a clear, editable outline that the user can fill in with their own experiences. Include section headers and bullet points for key points to cover. Keep it concise but comprehensive (max 500 words).

Respond with a JSON object with a single field "structure_text" containing the full outline."""
    mode_config = MODES["generate_story_structure"]
    response = await with_retry(
        lambda: client.generate_structured(
            prompt=prompt,
            response_schema=mode_config["response_schema"],
            max_tokens=mode_config["max_tokens"],
            temperature=0.7,
        )
    )
    return GenerateStoryStructureResponse(**response)

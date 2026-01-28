from abc import ABC, abstractmethod
from typing import Any, Dict
from app.config import settings
import openai
from anthropic import Anthropic


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
        pass


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


def get_llm_client() -> LLMClient:
    """Factory function to get the appropriate LLM client"""
    if settings.LLM_PROVIDER == "openai":
        return OpenAIClient()
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

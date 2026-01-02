"""OpenAI API client for documentation generation."""

import logging
import tiktoken
from typing import Optional
from openai import OpenAI

from .config import Config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, config: Config, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.config = config
        self.api_key = api_key or self._get_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.encoding = tiktoken.encoding_for_model(config.model)
    
    def _get_api_key(self) -> str:
        """Get API key from environment."""
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        return api_key
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token count."""
        cost_per_1k = self.config.cost_per_1k_tokens.get(self.config.model, 0.005)
        return (tokens / 1000) * cost_per_1k
    
    def generate_documentation(self, content: str, system_prompt: str) -> str:
        """Generate documentation using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens_per_request
            )
            
            if not response.choices:
                raise ValueError("Empty response from OpenAI API")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise 
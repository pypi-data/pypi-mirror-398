"""OpenAI API client for documentation generation."""

import logging
import tiktoken
from typing import Optional
from openai import OpenAI

from .config import Config, get_model_encoding, DEFAULT_ENCODING

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, config: Config, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.config = config
        self.api_key = api_key or self._get_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.encoding = self._get_encoding(config.model)
    
    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoding for model with fallback support.
        
        GPT-5 and other new models may not be directly supported by tiktoken yet,
        so we use explicit encoding names from our config.
        """
        encoding_name = get_model_encoding(model)
        try:
            return tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to get encoding '{encoding_name}' for model '{model}': {e}")
            logger.warning(f"Falling back to {DEFAULT_ENCODING} encoding")
            return tiktoken.get_encoding(DEFAULT_ENCODING)
    
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
    
    def _uses_max_completion_tokens(self) -> bool:
        """Check if model uses max_completion_tokens instead of max_tokens.
        
        GPT-5, GPT-4.1, o3, o4 and newer models require max_completion_tokens.
        """
        model = self.config.model.lower()
        new_model_prefixes = ("gpt-5", "gpt-4.1", "o3", "o4")
        return any(model.startswith(prefix) for prefix in new_model_prefixes)
    
    def generate_documentation(self, content: str, system_prompt: str) -> str:
        """Generate documentation using OpenAI API."""
        try:
            # Build request parameters
            request_params = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                "temperature": self.config.temperature,
            }
            
            # Use appropriate token limit parameter based on model
            if self._uses_max_completion_tokens():
                request_params["max_completion_tokens"] = self.config.max_tokens_per_request
            else:
                request_params["max_tokens"] = self.config.max_tokens_per_request
            
            response = self.client.chat.completions.create(**request_params)
            
            if not response.choices:
                raise ValueError("Empty response from OpenAI API")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise 
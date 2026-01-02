"""Configuration for readme-writer."""

import os
from pathlib import Path
from typing import Set, Dict, Optional
from dataclasses import dataclass, field


# Supported OpenAI models with their tiktoken encoding
# Note: GPT-5 models use o200k_base encoding (same as GPT-4o family)
SUPPORTED_MODELS: Dict[str, Dict[str, any]] = {
    # GPT-5 family (newest)
    "gpt-5.2": {"encoding": "o200k_base", "cost_per_1k": 0.01, "description": "Best model for coding and agentic tasks"},
    "gpt-5.2-pro": {"encoding": "o200k_base", "cost_per_1k": 0.02, "description": "Smarter, more precise GPT-5.2"},
    "gpt-5.1": {"encoding": "o200k_base", "cost_per_1k": 0.008, "description": "Coding and agentic tasks with configurable reasoning"},
    "gpt-5": {"encoding": "o200k_base", "cost_per_1k": 0.006, "description": "Intelligent reasoning model"},
    "gpt-5-mini": {"encoding": "o200k_base", "cost_per_1k": 0.002, "description": "Faster, cost-efficient GPT-5"},
    "gpt-5-nano": {"encoding": "o200k_base", "cost_per_1k": 0.001, "description": "Fastest, most cost-efficient GPT-5"},
    "gpt-5-pro": {"encoding": "o200k_base", "cost_per_1k": 0.015, "description": "Smarter GPT-5 responses"},
    # GPT-4.1 family
    "gpt-4.1": {"encoding": "o200k_base", "cost_per_1k": 0.005, "description": "Smartest non-reasoning model"},
    "gpt-4.1-mini": {"encoding": "o200k_base", "cost_per_1k": 0.001, "description": "Smaller, faster GPT-4.1"},
    "gpt-4.1-nano": {"encoding": "o200k_base", "cost_per_1k": 0.0005, "description": "Fastest GPT-4.1"},
    # GPT-4o family
    "gpt-4o": {"encoding": "o200k_base", "cost_per_1k": 0.005, "description": "Fast, intelligent, flexible GPT model"},
    "gpt-4o-mini": {"encoding": "o200k_base", "cost_per_1k": 0.00015, "description": "Fast, affordable small model"},
    # GPT-4 family
    "gpt-4-turbo": {"encoding": "cl100k_base", "cost_per_1k": 0.01, "description": "High-intelligence GPT model"},
    "gpt-4": {"encoding": "cl100k_base", "cost_per_1k": 0.03, "description": "Original GPT-4"},
    # GPT-3.5 family
    "gpt-3.5-turbo": {"encoding": "cl100k_base", "cost_per_1k": 0.0005, "description": "Legacy GPT model"},
    # Reasoning models (o-series)
    "o3": {"encoding": "o200k_base", "cost_per_1k": 0.015, "description": "Reasoning model for complex tasks"},
    "o3-mini": {"encoding": "o200k_base", "cost_per_1k": 0.003, "description": "Small reasoning model"},
    "o3-pro": {"encoding": "o200k_base", "cost_per_1k": 0.03, "description": "More compute for better responses"},
    "o4-mini": {"encoding": "o200k_base", "cost_per_1k": 0.002, "description": "Fast, cost-efficient reasoning"},
    "o1": {"encoding": "o200k_base", "cost_per_1k": 0.015, "description": "Previous o-series reasoning model"},
    "o1-mini": {"encoding": "o200k_base", "cost_per_1k": 0.003, "description": "Small o1 alternative"},
    "o1-pro": {"encoding": "o200k_base", "cost_per_1k": 0.03, "description": "More compute o1"},
}

# Default encoding for unknown models
DEFAULT_ENCODING = "o200k_base"


def get_model_encoding(model: str) -> str:
    """Get tiktoken encoding name for a model."""
    if model in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[model]["encoding"]
    return DEFAULT_ENCODING


def get_supported_models_list() -> str:
    """Get formatted list of supported models for help text."""
    lines = ["Available models:"]
    for model, info in SUPPORTED_MODELS.items():
        lines.append(f"  - {model}: {info['description']}")
    return "\n".join(lines)


@dataclass
class Config:
    """Configuration for readme-writer."""
    
    # OpenAI Configuration
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    temperature: float = field(default_factory=lambda: float(os.getenv("OPENAI_TEMPERATURE", "0.3")))
    max_tokens_per_request: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS_PER_REQUEST", "4000")))
    max_tokens_per_chunk: int = field(default_factory=lambda: int(os.getenv("OPENAI_MAX_TOKENS_PER_CHUNK", "3000")))
    
    # File Processing
    output_file: str = field(default_factory=lambda: os.getenv("OUTPUT_FILE", "README.md"))
    max_file_size: int = 1024 * 1024  # 1MB
    chunk_overlap: int = 200
    
    # Skip patterns
    skip_patterns: Set[str] = field(default_factory=lambda: {
        ".git", ".gitignore", ".gitattributes", "__pycache__", 
        ".pytest_cache", ".coverage", "*.pyc", "*.pyo", "*.pyd",
        ".DS_Store", "Thumbs.db", "*.log", "*.tmp", "*.temp"
    })
    
    # Cost estimation (derived from SUPPORTED_MODELS)
    cost_per_1k_tokens: dict = field(default_factory=lambda: {
        model: info["cost_per_1k"] for model, info in SUPPORTED_MODELS.items()
    })
    
    def should_skip_file(self, file_path: Path, additional_skip_patterns: Set[str] = None) -> bool:
        """Check if a file should be skipped."""
        file_name = file_path.name
        file_path_str = str(file_path)
        
        all_skip_patterns = self.skip_patterns.copy()
        if additional_skip_patterns:
            all_skip_patterns.update(additional_skip_patterns)
        
        return any(pattern in file_name or pattern in file_path_str for pattern in all_skip_patterns)
    
    def get_system_prompt(self, is_update: bool = False) -> str:
        """Get the system prompt."""
        from .prompt_loader import PromptLoader
        loader = PromptLoader()
        if is_update:
            return loader.load_update_prompt()
        else:
            return loader.load_full_prompt() 
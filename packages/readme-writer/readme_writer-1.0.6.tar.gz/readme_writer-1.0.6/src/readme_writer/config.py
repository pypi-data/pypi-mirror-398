"""Configuration for readme-writer."""

import os
from pathlib import Path
from typing import Set
from dataclasses import dataclass, field


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
    
    # Cost estimation
    cost_per_1k_tokens: dict = field(default_factory=lambda: {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.0005,
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
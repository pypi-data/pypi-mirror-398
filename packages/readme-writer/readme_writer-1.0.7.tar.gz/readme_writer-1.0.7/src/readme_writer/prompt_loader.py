"""Prompt loading utilities."""

import os
from pathlib import Path
from typing import Optional


class PromptLoader:
    """Load prompts from files."""
    
    def __init__(self):
        """Initialize prompt loader."""
        # Get the directory where this file is located
        current_dir = Path(__file__).parent
        self.prompts_dir = current_dir.parent / "prompts"
    
    def load_full_prompt(self) -> str:
        """Load the full prompt for creating new README files."""
        prompt_file = self.prompts_dir / "full-prompt.txt"
        return self._load_prompt_file(prompt_file)
    
    def load_update_prompt(self) -> str:
        """Load the update prompt for updating existing README files."""
        prompt_file = self.prompts_dir / "update-prompt.txt"
        return self._load_prompt_file(prompt_file)
    
    def _load_prompt_file(self, prompt_file: Path) -> str:
        """Load prompt from file."""
        try:
            if not prompt_file.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt from {prompt_file}: {e}") 
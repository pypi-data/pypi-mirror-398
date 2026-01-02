"""readme-writer - AI-powered documentation generator for Git repositories."""

from .core import DocumentationGenerator
from .file_processor import FileProcessor
from .openai_client import OpenAIClient
from .config import Config
from .prompt_loader import PromptLoader

__version__ = "1.0.0"
__all__ = [
    "DocumentationGenerator", 
    "FileProcessor", 
    "OpenAIClient", 
    "Config",
    "PromptLoader"
] 
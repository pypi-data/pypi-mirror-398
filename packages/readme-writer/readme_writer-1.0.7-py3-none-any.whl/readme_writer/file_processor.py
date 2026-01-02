"""File processing utilities for documentation generation."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file to be processed."""
    path: Path
    relative_path: str
    size: int
    extension: str
    content: str = ""


class FileProcessor:
    """Handles file discovery and processing for documentation generation."""
    
    def __init__(self, config: Config):
        """Initialize file processor."""
        self.config = config
    
    def discover_files(self, repository_path: Path, additional_skip_patterns: Set[str] = None) -> List[FileInfo]:
        """Discover all relevant files in the repository."""
        if not repository_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repository_path}")
        
        if not repository_path.is_dir():
            raise ValueError(f"Repository path must be a directory: {repository_path}")
        
        files = []
        
        for file_path in repository_path.rglob("*"):
            if file_path.is_file() and not self.config.should_skip_file(file_path, additional_skip_patterns):
                try:
                    relative_path = file_path.relative_to(repository_path)
                    file_info = FileInfo(
                        path=file_path,
                        relative_path=str(relative_path),
                        size=file_path.stat().st_size,
                        extension=file_path.suffix.lower()
                    )
                    files.append(file_info)
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
        
        # Sort files by path for consistent ordering
        files.sort(key=lambda f: f.relative_path)
        
        logger.info(f"Discovered {len(files)} files for processing")
        return files
    
    def read_file_content(self, file_info: FileInfo) -> str:
        """Read file content with size limits and encoding handling."""
        if file_info.size > self.config.max_file_size:
            logger.warning(f"File too large to process: {file_info.relative_path} ({file_info.size} bytes)")
            return f"# File too large to process: {file_info.relative_path}\nSize: {file_info.size} bytes\n"
        
        try:
            # Try UTF-8 first
            with open(file_info.path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                # Try with error handling
                with open(file_info.path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Error reading file {file_info.relative_path}: {e}")
                return f"# Error reading file: {file_info.relative_path}\nError: {e}\n"
        
        return content
    
    def read_all_files(self, files: List[FileInfo]) -> List[FileInfo]:
        """Read content for all files."""
        for file_info in files:
            file_info.content = self.read_file_content(file_info)
        return files
    
    def format_files_for_documentation(self, files: List[FileInfo]) -> str:
        """Format files for documentation generation."""
        formatted_content = []
        
        for file_info in files:
            formatted_content.append(f"## File: {file_info.relative_path}")
            formatted_content.append(f"Size: {file_info.size} bytes")
            formatted_content.append(f"Extension: {file_info.extension}")
            formatted_content.append("```")
            formatted_content.append(file_info.content)
            formatted_content.append("```")
            formatted_content.append("")
        
        return "\n".join(formatted_content)
    
    def chunk_files(self, files: List[FileInfo], max_tokens_per_chunk: int = None) -> List[List[FileInfo]]:
        """Split files into chunks based on token limits."""
        max_tokens = max_tokens_per_chunk or self.config.max_tokens_per_chunk
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for file_info in files:
            # Estimate tokens (rough approximation: 4 chars per token)
            estimated_tokens = len(file_info.content) // 4
            
            if current_tokens + estimated_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [file_info]
                current_tokens = estimated_tokens
            else:
                current_chunk.append(file_info)
                current_tokens += estimated_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_repository_stats(self, repository_path: Path, additional_skip_patterns: Set[str] = None) -> Dict[str, Any]:
        """Get repository statistics."""
        files = self.discover_files(repository_path, additional_skip_patterns)
        total_size = sum(f.size for f in files)
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "files": files
        } 
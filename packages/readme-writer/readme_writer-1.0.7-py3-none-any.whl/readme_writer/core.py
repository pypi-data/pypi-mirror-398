"""Core documentation generation logic."""

import logging
from pathlib import Path
from typing import List, Optional, Set
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config
from .file_processor import FileProcessor, FileInfo
from .openai_client import OpenAIClient
from .diff_analyzer import DiffAnalyzer, FileChange

logger = logging.getLogger(__name__)
console = Console()


class DocumentationGenerator:
    """Main class for generating documentation using OpenAI API."""
    
    def __init__(self, config: Config, api_key: Optional[str] = None):
        """Initialize documentation generator."""
        self.config = config
        self.file_processor = FileProcessor(config)
        self.openai_client = OpenAIClient(config, api_key)
        self.diff_analyzer = DiffAnalyzer()
    
    def generate_documentation(self, repository_path: Path, output_path: Optional[Path] = None, 
                             additional_skip_patterns: Set[str] = None) -> str:
        """Generate documentation for a repository."""
        console.print(f"[bold blue]Generating documentation for: {repository_path}[/bold blue]")
        
        # Check if output file already exists
        existing_readme = None
        is_update = False
        if output_path and output_path.exists():
            console.print("[yellow]Found existing README, will update it...[/yellow]")
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_readme = f.read()
                console.print(f"[green]Loaded existing README ({len(existing_readme)} characters)[/green]")
                is_update = True
            except Exception as e:
                console.print(f"[red]Warning: Could not read existing README: {e}[/red]")
                existing_readme = None
        
        # Get system prompt
        system_prompt = self.config.get_system_prompt(is_update)
        
        # Discover and process files
        console.print("[yellow]Discovering files...[/yellow]")
        files = self.file_processor.discover_files(repository_path, additional_skip_patterns)
        
        if not files:
            console.print("[red]No files found to process![/red]")
            return "No files found to generate documentation for."
        
        # Display files that will be processed
        console.print(f"[cyan]Found {len(files)} files to process:[/cyan]")
        for file_info in files:
            console.print(f"  • {file_info.relative_path} ({file_info.size} bytes)")
        
        # Read file contents
        console.print("[yellow]Reading file contents...[/yellow]")
        files = self.file_processor.read_all_files(files)
        
        # Analyze changes if updating existing README and diff analysis is enabled
        changes = []
        if is_update and existing_readme and self.diff_analyzer:
            console.print("[yellow]Analyzing changes since last update...[/yellow]")
            previous_snapshot = self.diff_analyzer.load_snapshot(repository_path)
            if previous_snapshot:
                changes = self.diff_analyzer.analyze_changes(files, previous_snapshot)
                change_summary = self.diff_analyzer.get_change_summary(changes)
                console.print(f"[cyan]Changes detected: {change_summary['added']} added, {change_summary['deleted']} deleted, {change_summary['modified']} modified[/cyan]")
            else:
                console.print("[yellow]No previous snapshot found, treating as new documentation[/yellow]")
        
        # Create and save current snapshot if diff analysis is enabled
        if self.diff_analyzer:
            current_snapshot = self.diff_analyzer.create_snapshot(files, repository_path)
            self.diff_analyzer.save_snapshot(current_snapshot, repository_path)
        
        # Estimate tokens and cost
        total_content = self.file_processor.format_files_for_documentation(files)
        estimated_tokens = self.openai_client.count_tokens(total_content)
        estimated_cost = self.openai_client.estimate_cost(estimated_tokens)
        
        console.print(f"[cyan]Estimated tokens: {estimated_tokens:,}[/cyan]")
        console.print(f"[cyan]Estimated cost: ${estimated_cost:.4f}[/cyan]")
        
        # Generate documentation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating...", total=None)
            
            if is_update and existing_readme:
                documentation = self._generate_update_documentation(total_content, system_prompt, existing_readme, repository_path, changes)
            elif estimated_tokens <= self.config.max_tokens_per_chunk:
                documentation = self._generate_single_chunk(total_content, system_prompt)
            else:
                documentation = self._generate_multiple_chunks(files, system_prompt)
            
            progress.update(task, completed=True)
        
        # Save documentation
        if output_path:
            self._save_documentation(documentation, output_path)
        
        console.print("[green]Documentation generated successfully![/green]")
        return documentation
    
    def _generate_single_chunk(self, content: str, system_prompt: str) -> str:
        """Generate documentation in a single API call."""
        return self.openai_client.generate_documentation(content, system_prompt)
    
    def _generate_update_documentation(self, project_content: str, system_prompt: str, existing_readme: str, repository_path: Path, changes: List[FileChange]) -> str:
        """Generate updated documentation by combining existing README with current project structure and detected changes."""
        # Format changes for inclusion in the prompt
        changes_text = self.diff_analyzer.format_changes_for_documentation(changes) if self.diff_analyzer else "No change analysis available."
        
        # Check if the combined content would be too large
        combined_content = f"""EXISTING README:
{existing_readme}

RECENT CHANGES DETECTED:
{changes_text}

CURRENT PROJECT STRUCTURE AND FILES:
{project_content}

Please update the existing README to reflect the current project structure and recent changes while preserving all valuable existing content. Pay special attention to:
1. Remove references to deleted files
2. Add documentation for new files
3. Update documentation for modified files
4. Maintain the overall structure and style of the existing README"""
        
        estimated_tokens = self.openai_client.count_tokens(combined_content)
        
        if estimated_tokens <= self.config.max_tokens_per_chunk:
            # If content is small enough, process in one request
            return self.openai_client.generate_documentation(combined_content, system_prompt)
        else:
            # If content is too large, we need to chunk the project files
            console.print(f"[yellow]Content too large ({estimated_tokens:,} tokens), chunking project files...[/yellow]")
            return self._generate_update_with_chunking(existing_readme, system_prompt, repository_path, changes)
    
    def _generate_update_with_chunking(self, existing_readme: str, system_prompt: str, repository_path: Path, changes: List[FileChange]) -> str:
        """Generate updated documentation by chunking project files and processing them separately."""
        # First, get the project structure summary without full file contents
        console.print("[yellow]Generating project structure summary...[/yellow]")
        
        # Format changes for inclusion
        changes_text = self.diff_analyzer.format_changes_for_documentation(changes) if self.diff_analyzer else "No change analysis available."
        
        # Create a simplified project structure prompt
        structure_prompt = """Analyze the current project structure and create a comprehensive summary that includes:
1. Directory structure and organization
2. Key files and their purposes
3. Main components and modules
4. Configuration files
5. Dependencies and requirements
6. Build and deployment files

Focus on the overall structure and organization rather than detailed file contents."""
        
        # Get just the file structure without contents
        files = self.file_processor.discover_files(repository_path, None)
        structure_content = self._format_structure_only(files)
        
        # Get project structure summary
        structure_summary = self.openai_client.generate_documentation(
            structure_content,
            structure_prompt
        )
        
        # Now combine the existing README with the structure summary and changes
        update_content = f"""EXISTING README:
{existing_readme}

RECENT CHANGES DETECTED:
{changes_text}

CURRENT PROJECT STRUCTURE SUMMARY:
{structure_summary}

Please update the existing README to reflect the current project structure and recent changes while preserving all valuable existing content. Use the structure summary to update relevant sections and ensure deleted files are removed from documentation."""
        
        # Check if this combined content is still too large
        estimated_tokens = self.openai_client.count_tokens(update_content)
        if estimated_tokens > self.config.max_tokens_per_chunk:
            console.print(f"[yellow]Update content still too large ({estimated_tokens:,} tokens), using simplified approach...[/yellow]")
            # Use a more aggressive approach - just update the structure section
            return self._generate_simplified_update(existing_readme, structure_content, repository_path, changes)
        
        return self.openai_client.generate_documentation(update_content, system_prompt)
    
    def _generate_simplified_update(self, existing_readme: str, structure_content: str, repository_path: Path, changes: List[FileChange]) -> str:
        """Generate a simplified update focusing only on the project structure section."""
        changes_text = self.diff_analyzer.format_changes_for_documentation(changes) if self.diff_analyzer else "No change analysis available."
        
        simplified_prompt = """You are updating an existing README file. Your task is to:

1. Keep all existing content that is still relevant
2. Update or add a "Project Structure" section based on the provided structure
3. Update any outdated file references or paths
4. Remove references to deleted files
5. Add documentation for new files
6. Preserve the existing formatting and style

Do NOT rewrite the entire README. Only make necessary updates to reflect the current project structure and recent changes."""
        
        update_content = f"""EXISTING README:
{existing_readme}

RECENT CHANGES DETECTED:
{changes_text}

CURRENT PROJECT STRUCTURE:
{structure_content}

Please update the README to reflect the current project structure and recent changes while preserving all existing content."""
        
        return self.openai_client.generate_documentation(update_content, simplified_prompt)
    
    def _format_structure_only(self, files: List['FileInfo']) -> str:
        """Format files as structure-only information without full contents."""
        if not files:
            return "No files found in the project."
        
        # Group files by directory
        structure = {}
        for file_info in files:
            # Convert string path to Path for easier manipulation
            path_obj = Path(file_info.relative_path)
            path_parts = path_obj.parts
            
            if len(path_parts) == 1:
                # Root level file
                if "root" not in structure:
                    structure["root"] = []
                structure["root"].append(f"- {file_info.relative_path} ({file_info.size} bytes)")
            else:
                # File in subdirectory
                dir_name = str(path_parts[0])
                if dir_name not in structure:
                    structure[dir_name] = []
                structure[dir_name].append(f"- {file_info.relative_path} ({file_info.size} bytes)")
        
        # Format the structure
        result = "Project Structure:\n\n"
        for dir_name, files_list in sorted(structure.items()):
            if dir_name == "root":
                result += "Root files:\n"
            else:
                result += f"{dir_name}/:\n"
            result += "\n".join(sorted(files_list)) + "\n\n"
        
        return result
    
    def _generate_multiple_chunks(self, files: List[FileInfo], system_prompt: str) -> str:
        """Generate documentation by processing files in chunks."""
        chunks = self.file_processor.chunk_files(files, self.config.max_tokens_per_chunk)
        
        chunk_documentations = []
        for i, chunk in enumerate(chunks):
            console.print(f"[yellow]Processing chunk {i+1}/{len(chunks)}...[/yellow]")
            chunk_content = self.file_processor.format_files_for_documentation(chunk)
            chunk_doc = self.openai_client.generate_documentation(chunk_content, system_prompt)
            chunk_documentations.append(chunk_doc)
        
        # Merge chunks
        console.print("[yellow]Merging chunks...[/yellow]")
        merged_content = "\n\n".join(chunk_documentations)
        
        # Create final merged documentation
        merge_prompt = """You are an expert at merging documentation sections. 
        Create a cohesive, well-structured README.md from the provided documentation chunks.
        Remove duplicates, maintain logical flow, and ensure consistent formatting."""
        
        return self.openai_client.generate_documentation(merged_content, merge_prompt)
    
    def _save_documentation(self, documentation: str, output_path: Path) -> None:
        """Save documentation to file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            console.print(f"[green]Documentation saved to: {output_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving documentation: {e}[/red]")
            raise
    
    def validate_repository(self, repository_path: Path, additional_skip_patterns: Set[str] = None) -> dict:
        """Validate repository and return statistics."""
        try:
            stats = self.file_processor.get_repository_stats(repository_path, additional_skip_patterns)
            
            # Estimate tokens
            files = stats["files"]
            total_content = self.file_processor.format_files_for_documentation(files)
            estimated_tokens = self.openai_client.count_tokens(total_content)
            estimated_cost = self.openai_client.estimate_cost(estimated_tokens)
            
            return {
                "valid": True,
                "stats": stats,
                "estimated_tokens": estimated_tokens,
                "estimated_cost": estimated_cost,
                "needs_chunking": estimated_tokens > self.config.max_tokens_per_chunk
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            } 
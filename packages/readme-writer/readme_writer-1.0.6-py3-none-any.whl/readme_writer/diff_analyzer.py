"""Diff analysis utilities for detecting file changes."""

import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

from .file_processor import FileInfo

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a change to a file."""
    path: str
    change_type: str  # 'added', 'deleted', 'modified'
    size: int
    extension: str
    content_hash: str = ""


@dataclass
class RepositorySnapshot:
    """Snapshot of repository state at a point in time."""
    timestamp: str
    files: Dict[str, Dict[str, any]]  # path -> file_info_dict
    total_files: int
    total_size: int


class DiffAnalyzer:
    """Analyzes differences between repository states to detect changes."""
    
    def __init__(self, snapshot_dir: Path = None):
        """Initialize diff analyzer."""
        self.snapshot_dir = snapshot_dir or Path(".readme-writer-snapshots")
        self.snapshot_dir.mkdir(exist_ok=True)
    
    def create_snapshot(self, files: List[FileInfo], repository_path: Path) -> RepositorySnapshot:
        """Create a snapshot of the current repository state."""
        files_dict = {}
        total_size = 0
        
        for file_info in files:
            # Create content hash for change detection
            content_hash = hashlib.md5(file_info.content.encode('utf-8')).hexdigest()
            
            files_dict[file_info.relative_path] = {
                'size': file_info.size,
                'extension': file_info.extension,
                'content_hash': content_hash,
                'path': file_info.relative_path
            }
            total_size += file_info.size
        
        snapshot = RepositorySnapshot(
            timestamp=datetime.now().isoformat(),
            files=files_dict,
            total_files=len(files),
            total_size=total_size
        )
        
        return snapshot
    
    def save_snapshot(self, snapshot: RepositorySnapshot, repository_path: Path) -> Path:
        """Save snapshot to disk."""
        # Create a unique filename based on repository path
        repo_hash = hashlib.md5(str(repository_path.absolute()).encode()).hexdigest()[:8]
        snapshot_file = self.snapshot_dir / f"snapshot_{repo_hash}.json"
        
        with open(snapshot_file, 'w') as f:
            json.dump(asdict(snapshot), f, indent=2)
        
        logger.info(f"Saved snapshot to {snapshot_file}")
        return snapshot_file
    
    def load_snapshot(self, repository_path: Path) -> Optional[RepositorySnapshot]:
        """Load the most recent snapshot for a repository."""
        repo_hash = hashlib.md5(str(repository_path.absolute()).encode()).hexdigest()[:8]
        snapshot_file = self.snapshot_dir / f"snapshot_{repo_hash}.json"
        
        if not snapshot_file.exists():
            return None
        
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to RepositorySnapshot
            snapshot = RepositorySnapshot(
                timestamp=data['timestamp'],
                files=data['files'],
                total_files=data['total_files'],
                total_size=data['total_size']
            )
            
            logger.info(f"Loaded snapshot from {snapshot_file}")
            return snapshot
        except Exception as e:
            logger.warning(f"Failed to load snapshot: {e}")
            return None
    
    def analyze_changes(self, current_files: List[FileInfo], previous_snapshot: RepositorySnapshot) -> List[FileChange]:
        """Analyze changes between current state and previous snapshot."""
        changes = []
        
        # Create current file set
        current_file_paths = {f.relative_path for f in current_files}
        current_file_dict = {f.relative_path: f for f in current_files}
        
        # Create previous file set
        previous_file_paths = set(previous_snapshot.files.keys())
        
        # Find added files
        added_files = current_file_paths - previous_file_paths
        for path in added_files:
            file_info = current_file_dict[path]
            content_hash = hashlib.md5(file_info.content.encode('utf-8')).hexdigest()
            changes.append(FileChange(
                path=path,
                change_type='added',
                size=file_info.size,
                extension=file_info.extension,
                content_hash=content_hash
            ))
        
        # Find deleted files
        deleted_files = previous_file_paths - current_file_paths
        for path in deleted_files:
            file_info = previous_snapshot.files[path]
            changes.append(FileChange(
                path=path,
                change_type='deleted',
                size=file_info['size'],
                extension=file_info['extension'],
                content_hash=file_info['content_hash']
            ))
        
        # Find modified files (same path, different content hash)
        common_files = current_file_paths & previous_file_paths
        for path in common_files:
            current_file = current_file_dict[path]
            previous_file = previous_snapshot.files[path]
            
            current_hash = hashlib.md5(current_file.content.encode('utf-8')).hexdigest()
            if current_hash != previous_file['content_hash']:
                changes.append(FileChange(
                    path=path,
                    change_type='modified',
                    size=current_file.size,
                    extension=current_file.extension,
                    content_hash=current_hash
                ))
        
        return changes
    
    def format_changes_for_documentation(self, changes: List[FileChange]) -> str:
        """Format changes for inclusion in documentation update prompt."""
        if not changes:
            return "No changes detected since last update."
        
        # Group changes by type
        added_files = [c for c in changes if c.change_type == 'added']
        deleted_files = [c for c in changes if c.change_type == 'deleted']
        modified_files = [c for c in changes if c.change_type == 'modified']
        
        result = "## Recent Changes Detected\n\n"
        
        if added_files:
            result += "### Added Files:\n"
            for change in added_files:
                result += f"- `{change.path}` ({change.size} bytes)\n"
            result += "\n"
        
        if deleted_files:
            result += "### Deleted Files:\n"
            for change in deleted_files:
                result += f"- `{change.path}` ({change.size} bytes)\n"
            result += "\n"
        
        if modified_files:
            result += "### Modified Files:\n"
            for change in modified_files:
                result += f"- `{change.path}` ({change.size} bytes)\n"
            result += "\n"
        
        return result
    
    def get_change_summary(self, changes: List[FileChange]) -> Dict[str, int]:
        """Get a summary of changes."""
        summary = {
            'added': len([c for c in changes if c.change_type == 'added']),
            'deleted': len([c for c in changes if c.change_type == 'deleted']),
            'modified': len([c for c in changes if c.change_type == 'modified']),
            'total': len(changes)
        }
        return summary 
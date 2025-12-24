"""
Git Repository Metadata Module

This module provides utilities for extracting metadata from git repositories,
including repository information, branch details, commit hashes, and working
directory status.

Key Features:
- Extract git repository remote URL
- Get current branch name
- Retrieve current commit hash
- Check working directory dirty status
- Safe error handling for non-git directories

Main Functions:
- get_git_metadata: Extract comprehensive git repository metadata

Usage Example:
    ```python
    from src.git import get_git_metadata

    # Get all git metadata for current directory
    git_info = get_git_metadata()

    print(f"Repository: {git_info['git_repo']}")
    print(f"Branch: {git_info['git_branch']}")
    print(f"Commit: {git_info['git_commit']}")
    print(f"Has uncommitted changes: {git_info['git_dirty']}")
    ```

Note:
    All functions safely handle non-git directories and git command failures
    by returning None values instead of raising exceptions.

Author: @Ruppert20
Version: 0.0.1
"""

from typing import Dict, Optional
import subprocess


def get_git_metadata() -> Dict[str, Optional[str]]:
    """
    Extract comprehensive metadata from the current git repository.

    Retrieves repository URL, branch name, commit hash, and working directory
    status using git subprocess commands. All operations have a 2-second timeout
    and gracefully handle failures by returning None values.

    Returns
    -------
    Dict[str, Optional[str]]
        Dictionary containing git metadata with the following keys:
        - 'git_repo': Remote origin URL (None if not available)
        - 'git_branch': Current branch name (None if not available)
        - 'git_commit': Current commit hash (None if not available)
        - 'git_dirty': Boolean indicating uncommitted changes (None if not available)

    Examples
    --------
    >>> metadata = get_git_metadata()
    >>> if metadata['git_repo']:
    ...     print(f"Working in repository: {metadata['git_repo']}")

    Note:
        Returns a dict with None values if not in a git repository or if git
        commands fail. The function never raises exceptions for git errors.
    """
    git_info = {
        'git_repo': None,
        'git_branch': None,
        'git_commit': None,
        'git_dirty': None
    }
    
    try:
        # Get remote URL
        result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            git_info['git_repo'] = result.stdout.strip() # type: ignore
        
        # Get current branch
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            git_info['git_branch'] = result.stdout.strip() # type: ignore
        
        # Get current commit hash
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            git_info['git_commit'] = result.stdout.strip() # type: ignore
        
        # Check if working directory is dirty
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            git_info['git_dirty'] = bool(result.stdout.strip()) # type: ignore
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Git not available or timeout
    
    return git_info # type: ignore
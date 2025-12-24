import re
from pathlib import Path
from typing import Union, List, Optional, Iterator, cast
import fnmatch


class FileSearcher:
    """
    Flexible file search utility with support for patterns, file types, and exclusions.

    This class provides comprehensive file searching capabilities including:
    - File type filtering by extension
    - Include/exclude patterns using glob or regex
    - Recursive or non-recursive directory traversal
    - Multiple pattern matching strategies

    Examples
    --------
    Search for Python files:
        >>> searcher = FileSearcher("/path/to/dir")
        >>> results = list(searcher.search(file_types=".py"))

    Search with patterns:
        >>> results = list(searcher.search(
        ...     patterns="test_*.py",
        ...     exclude_patterns="*_old.py",
        ...     recursive=True
        ... ))

    Search with regex:
        >>> results = list(searcher.search(
        ...     patterns=r"^test_\\w+\\.py$",
        ...     use_regex=True
        ... ))
    """

    def __init__(self, root_directory: Union[str, Path]):
        """
        Initialize FileSearcher with a root directory.

        Parameters
        ----------
        root_directory : Union[str, Path]
            Root directory to search from.

        Raises
        ------
        ValueError
            If root_directory does not exist or is not a directory.
        """
        self.root_directory = Path(root_directory)
        if not self.root_directory.exists():
            raise ValueError(f"Directory does not exist: {root_directory}")
        if not self.root_directory.is_dir():
            raise ValueError(f"Path is not a directory: {root_directory}")

    @staticmethod
    def _normalize_to_list(value: Optional[Union[str, List[str]]]) -> List[str]:
        """
        Convert a value to a list format.

        Parameters
        ----------
        value : Optional[Union[str, List[str]]]
            Value to normalize (string, list, or None).

        Returns
        -------
        List[str]
            List of strings (empty list if value is None).
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)

    @staticmethod
    def _normalize_extensions(extensions: List[str]) -> List[str]:
        """
        Normalize file extensions to include leading dot.

        Parameters
        ----------
        extensions : List[str]
            List of file extensions.

        Returns
        -------
        List[str]
            Normalized extensions with leading dots.

        Examples
        --------
        >>> FileSearcher._normalize_extensions(["py", ".txt", "md"])
        ['.py', '.txt', '.md']
        """
        normalized = []
        for ext in extensions:
            if not ext.startswith('.'):
                normalized.append('.' + ext)
            else:
                normalized.append(ext)
        return normalized

    @staticmethod
    def _compile_regex_patterns(patterns: List[str]) -> List[re.Pattern]:
        """
        Compile regex patterns.

        Parameters
        ----------
        patterns : List[str]
            List of regex pattern strings.

        Returns
        -------
        List[re.Pattern]
            List of compiled regex patterns.

        Raises
        ------
        re.error
            If any pattern is invalid regex.
        """
        return [re.compile(pattern) for pattern in patterns]

    def _match_glob(self, filename: str, patterns: List[str]) -> bool:
        """
        Check if filename matches any glob pattern.

        Parameters
        ----------
        filename : str
            Filename to match.
        patterns : List[str]
            List of glob patterns.

        Returns
        -------
        bool
            True if filename matches any pattern, False otherwise.
        """
        if not patterns:
            return True
        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)

    def _match_regex(self, filename: str, patterns: List[re.Pattern]) -> bool:
        """
        Check if filename matches any regex pattern.

        Parameters
        ----------
        filename : str
            Filename to match.
        patterns : List[re.Pattern]
            List of compiled regex patterns.

        Returns
        -------
        bool
            True if filename matches any pattern, False otherwise.
        """
        if not patterns:
            return True
        return any(pattern.search(filename) for pattern in patterns)

    def _should_exclude_directory(
        self,
        dir_path: Path,
        exclude_dirs: List[str],
        use_regex: bool
    ) -> bool:
        """
        Check if a directory should be excluded from search.

        Parameters
        ----------
        dir_path : Path
            Directory path to check.
        exclude_dirs : List[str]
            List of directory exclusion patterns.
        use_regex : bool
            Whether to use regex matching.

        Returns
        -------
        bool
            True if directory should be excluded, False otherwise.
        """
        if not exclude_dirs:
            return False

        dir_name = dir_path.name

        if use_regex:
            regex_patterns = self._compile_regex_patterns(exclude_dirs)
            return any(pattern.search(dir_name) for pattern in regex_patterns)
        else:
            return any(fnmatch.fnmatch(dir_name, pattern) for pattern in exclude_dirs)

    def search(
        self,
        file_types: Optional[Union[str, List[str]]] = None,
        patterns: Optional[Union[str, List[str]]] = None,
        exclude_patterns: Optional[Union[str, List[str]]] = None,
        exclude_dirs: Optional[Union[str, List[str]]] = None,
        recursive: bool = True,
        use_regex: bool = False,
        case_sensitive: bool = True,
        follow_symlinks: bool = False
    ) -> Iterator[Path]:
        """
        Search for files matching the specified criteria.

        Parameters
        ----------
        file_types : Optional[Union[str, List[str]]], optional
            File extension(s) to match (e.g., ".py" or [".py", ".txt"]).
            Extensions can be specified with or without leading dot.
        patterns : Optional[Union[str, List[str]]], optional
            Pattern(s) to match filenames against. Can be glob patterns
            (e.g., "test_*.py") or regex patterns if use_regex=True.
            If None, all filenames match.
        exclude_patterns : Optional[Union[str, List[str]]], optional
            Pattern(s) to exclude from results. Same format as patterns.
        exclude_dirs : Optional[Union[str, List[str]]], optional
            Directory name patterns to exclude from recursive search.
            Common examples: "__pycache__", ".git", "node_modules".
        recursive : bool, optional
            Whether to search subdirectories recursively. Default is True.
        use_regex : bool, optional
            Whether to interpret patterns as regular expressions.
            If False (default), patterns are treated as glob patterns.
        case_sensitive : bool, optional
            Whether pattern matching is case-sensitive. Default is True.
            Note: Only affects regex patterns; glob patterns follow
            filesystem case sensitivity.
        follow_symlinks : bool, optional
            Whether to follow symbolic links during traversal. Default is False.

        Yields
        ------
        Path
            Paths to files matching the search criteria.

        Examples
        --------
        Find all Python files:
            >>> searcher = FileSearcher("/project")
            >>> for path in searcher.search(file_types=".py"):
            ...     print(path)

        Find test files, exclude old ones:
            >>> for path in searcher.search(
            ...     patterns="test_*.py",
            ...     exclude_patterns="*_old.py",
            ...     exclude_dirs=["__pycache__", ".git"]
            ... ):
            ...     print(path)

        Find files with regex:
            >>> for path in searcher.search(
            ...     patterns=r"^data_\\d{4}\\.json$",
            ...     use_regex=True
            ... ):
            ...     print(path)

        Find multiple file types:
            >>> for path in searcher.search(
            ...     file_types=[".py", ".md", ".txt"],
            ...     recursive=True
            ... ):
            ...     print(path)
        """
        # Normalize inputs to lists
        file_types_list = self._normalize_to_list(file_types)
        patterns_list = self._normalize_to_list(patterns)
        exclude_patterns_list = self._normalize_to_list(exclude_patterns)
        exclude_dirs_list = self._normalize_to_list(exclude_dirs)

        # Normalize file extensions
        if file_types_list:
            file_types_list = self._normalize_extensions(file_types_list)

        # Compile patterns if using regex
        if use_regex:
            regex_flags = 0 if case_sensitive else re.IGNORECASE

            if patterns_list:
                include_patterns = [
                    re.compile(p, regex_flags) for p in patterns_list
                ]
            else:
                include_patterns = []

            if exclude_patterns_list:
                exclude_patterns_compiled = [
                    re.compile(p, regex_flags) for p in exclude_patterns_list
                ]
            else:
                exclude_patterns_compiled = []
        else:
            include_patterns = patterns_list
            exclude_patterns_compiled = exclude_patterns_list

        # Perform search
        if recursive:
            yield from self._search_recursive(
                self.root_directory,
                file_types_list,
                include_patterns,
                exclude_patterns_compiled,
                exclude_dirs_list,
                use_regex,
                follow_symlinks
            )
        else:
            yield from self._search_single_directory(
                self.root_directory,
                file_types_list,
                include_patterns,
                exclude_patterns_compiled,
                use_regex,
                follow_symlinks
            )

    def _search_single_directory(
        self,
        directory: Path,
        file_types: List[str],
        include_patterns: Union[List[str], List[re.Pattern]],
        exclude_patterns: Union[List[str], List[re.Pattern]],
        use_regex: bool,
        follow_symlinks: bool = False
    ) -> Iterator[Path]:
        """
        Search a single directory (non-recursive).

        Parameters
        ----------
        directory : Path
            Directory to search.
        file_types : List[str]
            File extensions to match.
        include_patterns : Union[List[str], List[re.Pattern]]
            Patterns to include.
        exclude_patterns : Union[List[str], List[re.Pattern]]
            Patterns to exclude.
        use_regex : bool
            Whether patterns are regex.
        follow_symlinks : bool
            Whether to include symlinks.

        Yields
        ------
        Path
            Matching file paths.
        """
        try:
            for entry in directory.iterdir():
                if entry.is_symlink() and not follow_symlinks:
                    continue

                if entry.is_file():
                    if self._matches_criteria(
                        entry,
                        file_types,
                        include_patterns,
                        exclude_patterns,
                        use_regex
                    ):
                        yield entry
        except PermissionError:
            pass

    def _search_recursive(
        self,
        directory: Path,
        file_types: List[str],
        include_patterns: Union[List[str], List[re.Pattern]],
        exclude_patterns: Union[List[str], List[re.Pattern]],
        exclude_dirs: List[str],
        use_regex: bool,
        follow_symlinks: bool
    ) -> Iterator[Path]:
        """
        Search directory recursively.

        Parameters
        ----------
        directory : Path
            Directory to search.
        file_types : List[str]
            File extensions to match.
        include_patterns : Union[List[str], List[re.Pattern]]
            Patterns to include.
        exclude_patterns : Union[List[str], List[re.Pattern]]
            Patterns to exclude.
        exclude_dirs : List[str]
            Directory patterns to exclude.
        use_regex : bool
            Whether patterns are regex.
        follow_symlinks : bool
            Whether to follow symbolic links.

        Yields
        ------
        Path
            Matching file paths.
        """
        try:
            for entry in directory.iterdir():
                if entry.is_symlink() and not follow_symlinks:
                    continue

                if entry.is_file():
                    if self._matches_criteria(
                        entry,
                        file_types,
                        include_patterns,
                        exclude_patterns,
                        use_regex
                    ):
                        yield entry
                elif entry.is_dir():
                    if not self._should_exclude_directory(entry, exclude_dirs, use_regex):
                        yield from self._search_recursive(
                            entry,
                            file_types,
                            include_patterns,
                            exclude_patterns,
                            exclude_dirs,
                            use_regex,
                            follow_symlinks
                        )
        except PermissionError:
            pass

    def _matches_criteria(
        self,
        file_path: Path,
        file_types: List[str],
        include_patterns: Union[List[str], List[re.Pattern]],
        exclude_patterns: Union[List[str], List[re.Pattern]],
        use_regex: bool
    ) -> bool:
        """
        Check if a file matches all search criteria.

        Parameters
        ----------
        file_path : Path
            File path to check.
        file_types : List[str]
            File extensions to match.
        include_patterns : Union[List[str], List[re.Pattern]]
            Patterns to include.
        exclude_patterns : Union[List[str], List[re.Pattern]]
            Patterns to exclude.
        use_regex : bool
            Whether patterns are regex.

        Returns
        -------
        bool
            True if file matches all criteria, False otherwise.
        """
        filename = file_path.name

        if file_types and file_path.suffix not in file_types:
            return False

        if use_regex:
            # Type narrowing: use_regex=True means patterns are compiled regex
            regex_include = cast(List[re.Pattern], include_patterns)
            if not self._match_regex(filename, regex_include):
                return False
        else:
            # Type narrowing: use_regex=False means patterns are strings
            glob_include = cast(List[str], include_patterns)
            if not self._match_glob(filename, glob_include):
                return False

        if use_regex:
            # Type narrowing: use_regex=True means patterns are compiled regex
            regex_exclude = cast(List[re.Pattern], exclude_patterns)
            if exclude_patterns and self._match_regex(filename, regex_exclude):
                return False
        else:
            # Type narrowing: use_regex=False means patterns are strings
            glob_exclude = cast(List[str], exclude_patterns)
            if exclude_patterns and self._match_glob(filename, glob_exclude):
                return False

        return True

    def count(self, **kwargs) -> int:
        """
        Count files matching the search criteria.

        Parameters
        ----------
        **kwargs
            Same parameters as search() method.

        Returns
        -------
        int
            Number of files matching the criteria.

        Examples
        --------
        >>> searcher = FileSearcher("/project")
        >>> count = searcher.count(file_types=".py", recursive=True)
        >>> print(f"Found {count} Python files")
        """
        return sum(1 for _ in self.search(**kwargs))

    def find_first(self, **kwargs) -> Optional[Path]:
        """
        Find the first file matching the search criteria.

        Parameters
        ----------
        **kwargs
            Same parameters as search() method.

        Returns
        -------
        Optional[Path]
            Path to first matching file, or None if no matches found.

        Examples
        --------
        >>> searcher = FileSearcher("/project")
        >>> first_test = searcher.find_first(patterns="test_*.py")
        """
        for path in self.search(**kwargs):
            return path
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

def find_files(
    directory: Union[str, Path],
    **kwargs
) -> List[Path]:
    """
    Convenience function to find all files matching criteria.

    Parameters
    ----------
    directory : Union[str, Path]
        Directory to search.
    **kwargs
        Search parameters (see FileSearcher.search()).

    Returns
    -------
    List[Path]
        List of matching file paths.

    Examples
    --------
    >>> files = find_files("/project", file_types=".py", recursive=True)
    >>> test_files = find_files("/project", patterns="test_*.py")
    """
    searcher = FileSearcher(directory)
    return list(searcher.search(**kwargs))


def count_files(
    directory: Union[str, Path],
    **kwargs
) -> int:
    """
    Convenience function to count files matching criteria.

    Parameters
    ----------
    directory : Union[str, Path]
        Directory to search.
    **kwargs
        Search parameters (see FileSearcher.search()).

    Returns
    -------
    int
        Number of matching files.

    Examples
    --------
    >>> count = count_files("/project", file_types=".py")
    """
    searcher = FileSearcher(directory)
    return searcher.count(**kwargs)


# ============================================================================
# Usage Examples
# ============================================================================
#
# Basic file type search:
#     searcher = FileSearcher("/path/to/project")
#     for file in searcher.search(file_types=".py"):
#         print(file)
#
# Multiple file types:
#     for file in searcher.search(file_types=[".py", ".txt", ".md"]):
#         print(file)
#
# Pattern matching with glob:
#     for file in searcher.search(patterns="test_*.py"):
#         print(file)
#
# Pattern matching with regex:
#     for file in searcher.search(patterns=r"^test_\w+\.py$", use_regex=True):
#         print(file)
#
# Exclude patterns:
#     for file in searcher.search(
#         file_types=".py",
#         exclude_patterns=["*_old.py", "*_backup.py"]
#     ):
#         print(file)
#
# Exclude directories:
#     for file in searcher.search(
#         file_types=".py",
#         exclude_dirs=["__pycache__", ".git", "venv", "node_modules"]
#     ):
#         print(file)
#
# Non-recursive search:
#     for file in searcher.search(file_types=".py", recursive=False):
#         print(file)
#
# Count files:
#     count = searcher.count(file_types=".py")
#     print(f"Found {count} Python files")
#
# Find first match:
#     first = searcher.find_first(patterns="config.json")
#     if first:
#         print(f"Config found at: {first}")
#
# Complex search:
#     for file in searcher.search(
#         file_types=[".py", ".pyi"],
#         patterns=["test_*.py", "*_test.py"],
#         exclude_patterns="*_old.py",
#         exclude_dirs=["__pycache__", ".tox", "build"],
#         recursive=True
#     ):
#         print(file)

"""
CoreUtils-Python

A comprehensive collection of Python utility functions and modules for data science,
file operations, serialization, encryption, and general-purpose programming tasks.

This package provides a wide range of utilities organized into functional modules:
- Core utilities (generics, functions, lists, strings, numbers, dictionaries)
- Data processing (core_types, iterables, serialization)
- Security & encryption (encrypt, signature)
- Testing utilities (debugging)
- File operations (search, git)
- Logging and parallelization (enhanced_logging, parrallelization)

Author: @Ruppert20
License: MIT
"""

# Core Utilities - Generic functions
from .generics import (
    notnull,
    isnull,
    coalesce,
    get_name,
)

# Core Utilities - Function utilities
from .functions import (
    convert_func_to_string,
    is_pickleable,
    debug_inputs,
    get_func,
    filter_kwargs,
    inspect_class,
    get_function_signature,
)

# Core Utilities - List operations
from .lists import (
    convert_list_to_string,
    chunk_list,
    list_intersection,
    flatten_list,
)

# Core Utilities - String manipulation
from .strings import (
    remove_illegal_characters,
    get_file_name_components,
    tokenize_id,
    snake_to_camel_case,
    camel_to_snake_case,
    convert_identifier_case,
)

# Core Utilities - Number operations
from .numbers import (
    extract_num,
    isfloat,
    convert_to_comma_seperated_integer_list,
)

# Core Utilities - Dictionary operations
from .dictionaries import (
    create_aggregation_dict,
)

# Data Processing - Type classification
from .core_types import CoreDataType

# Data Processing - Memory profiling
from .iterables import (
    deep_stats,
    find_large_objects,
)

# Data Processing - Serialization
from .serialization import XSer

# Security - Encryption
from .encrypt import (
    Encryptor,
    CryptoYAML,
)

# Security - File signing
from .signature import SignedFile

# Testing - Debugging and random data generation
from .debugging import (
    random_ascii_sequence,
    random_uuid,
    random_TINYINT,
    random_SMALLINT,
    random_BIGINT,
    random_int,
    random_float,
    random_date,
    random_datetime,
    random_time,
    random_bool,
    random_json,
    random_xml_safe_string,
    random_xml,
    generate_random_sequence,
    debug_print,
)

# File Operations - Search utilities
from .search import (
    FileSearcher,
    find_files,
    count_files,
)

# File Operations - Git metadata
from .git import get_git_metadata

# Logging - Enhanced logging system
from .enhanced_logging import (
    LogLevel,
    PerformanceMetrics,
    LogFormatter,
    EnhancedLogger,
    ProgressContext,
    get_logger,
    configure_default_logging,
    set_global_log_level,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
    timer,
    time_function,
    get_performance_metrics,
    progress_iter,
    progress_wrapper,
    progress_context,
)

# Parallelization - Parallel processing utilities
from .parrallelization import (
    ExecutionMetrics,
    TaskResult,
    ParallelProcessor,
    parallel_execute,
)

# Define public API
__all__ = [
    # Generic utilities
    'notnull',
    'isnull',
    'coalesce',
    'get_name',

    # Function utilities
    'convert_func_to_string',
    'is_pickleable',
    'debug_inputs',
    'get_func',
    'filter_kwargs',
    'inspect_class',
    'get_function_signature',

    # List utilities
    'convert_list_to_string',
    'chunk_list',
    'list_intersection',
    'flatten_list',

    # String utilities
    'remove_illegal_characters',
    'get_file_name_components',
    'tokenize_id',
    'snake_to_camel_case',
    'camel_to_snake_case',
    'convert_identifier_case',

    # Number utilities
    'extract_num',
    'isfloat',
    'convert_to_comma_seperated_integer_list',

    # Dictionary utilities
    'create_aggregation_dict',

    # Type classification
    'CoreDataType',

    # Memory profiling
    'deep_stats',
    'find_large_objects',

    # Serialization
    'XSer',

    # Encryption
    'Encryptor',
    'CryptoYAML',

    # File signing
    'SignedFile',

    # Debugging and testing
    'random_ascii_sequence',
    'random_uuid',
    'random_TINYINT',
    'random_SMALLINT',
    'random_BIGINT',
    'random_int',
    'random_float',
    'random_date',
    'random_datetime',
    'random_time',
    'random_bool',
    'random_json',
    'random_xml_safe_string',
    'random_xml',
    'generate_random_sequence',
    'debug_print',

    # File search
    'FileSearcher',
    'find_files',
    'count_files',

    # Git operations
    'get_git_metadata',

    # Enhanced logging
    'LogLevel',
    'PerformanceMetrics',
    'LogFormatter',
    'EnhancedLogger',
    'ProgressContext',
    'get_logger',
    'configure_default_logging',
    'set_global_log_level',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'exception',
    'timer',
    'time_function',
    'get_performance_metrics',
    'progress_iter',
    'progress_wrapper',
    'progress_context',

    # Parallelization
    'ExecutionMetrics',
    'TaskResult',
    'ParallelProcessor',
    'parallel_execute',
]

# Package metadata
try:
    from ._version import __version__, __version_tuple__
except ImportError:
    # Development mode - _version.py not yet generated
    __version__ = "0.0.0.dev0"
    __version_tuple__ = (0, 0, 0, "dev0")

__author__ = '@Ruppert20'
__license__ = 'MIT'

"""
String Utilities for Ruppert20

This module provides comprehensive string manipulation and processing utilities
for data science workflows. It includes functions for cleaning, transforming,
and analyzing string data across various data processing libraries.

Key Features:
- String cleaning and normalization
- Text preprocessing for machine learning
- Pattern matching and extraction
- String similarity and comparison
- Encoding/decoding utilities
- Text analysis and metrics

Usage Example:
    ```python
    from iterables.strings import clean_text, extract_patterns
    
    # Clean and normalize text data
    cleaned = clean_text(text_series, remove_punctuation=True, lowercase=True)
    
    # Extract patterns from strings
    emails = extract_patterns(text_series, pattern_type='email')
    ```

Supported Operations:
- Text cleaning and normalization
- Regular expression utilities
- String similarity metrics
- Text encoding/decoding
- Pattern extraction and validation
- String tokenization and splitting
- Case conversion utilities
- Whitespace and special character handling

Author: Ruppert20
Created: July 2025
Version: 0.0.1
License: MIT
"""

from typing import Union, List, Optional, Literal
import re
import string

# Version information
__version__ = "0.0.1"
__author__ = "Ruppert20"



# Regular expression patterns for common use cases
COMMON_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'(\+?1-?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
    'url': r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
    'zip_code': r'\b\d{5}(?:-\d{4})?\b',
    'ipv4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    'hashtag': r'#\w+',
    'mention': r'@\w+',
    'currency': r'\$\d+(?:\.\d{2})?'
}

# Text cleaning constants
PUNCTUATION = string.punctuation
WHITESPACE_CHARS = string.whitespace
UNICODE_CATEGORIES_TO_REMOVE = ['Cc', 'Cf', 'Cs', 'Co', 'Cn']  # Control characters


from collections import namedtuple
import re
import os
import pandas as pd
from .numbers import isfloat
from .generics import isnull, notnull

# Import enhanced logging from same directory
from .enhanced_logging import get_logger, LogLevel

# Configure logging for utility package - low verbosity except for warnings/errors
logger = get_logger(
    'string_utils',
    level=LogLevel.WARNING,  # Only warnings and above by default
    include_performance=True,
    include_emoji=True
)


def remove_illegal_characters(string: str,
                              case: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase', 'capitalize', 'casefold', 'preserve'] = 'snake_case',
                              preserve_decimals: bool = True):
    """Strip illegal characters from column names."""
    temp = str(string).replace('?', '').replace('-', '_')\
        .replace('\\', '_').replace('(', '')\
        .replace(')', '').replace('/', '_')\
        .replace(' ', '_').replace(':', '_')\
        .replace("'", '').replace('__', '_')\
        .replace('+', '_and_')\
        .replace('*', 'asterisk')\
        .replace('1st', 'first')\
        .replace('_datatime', '_datetime')

    if not preserve_decimals:
        temp = temp.replace('.', '')


    if case == 'preserve':
        return temp

    return convert_identifier_case(temp, target_format=case, preserve_acronyms=True).lower()


def _is_ascii(s):
    """Check if all characters in a string are ascii characters."""
    return all(ord(c) < 128 for c in s)


file_components = namedtuple('file_components', 'directory file_name batch_numbers file_type optimized bs_sep')


def get_file_name_components(file_path: str) -> tuple:
    """
    Extract directory, file_name, batch_numbers, and file type from a file_path.
    
    This function parses file paths to extract meaningful components including
    directory structure, base filename, batch/chunk numbers, file extensions,
    and optimization flags. It handles various naming patterns commonly used
    in data processing workflows.
    
    Parameters
    ----------
    file_path : str
        The file path to parse. Can be absolute or relative path, or just filename.
        Supports various naming patterns including:
        - Simple files: "data.csv"
        - Batched files: "data_1_2.csv"
        - Chunked files: "data_1_chunk_5.csv"
        - Optimized files: "data_optimized_ids.csv"
        - Stage files: "data_1_stage.csv"
    
    Returns
    -------
    tuple
        A named tuple with the following fields:
        - directory (str or None): Directory path if present
        - file_name (str): Base filename without extensions and suffixes
        - batch_numbers (list of int): Extracted numeric batch/chunk identifiers
        - file_type (str or None): File extension including the dot (e.g., '.csv')
        - optimized (bool): Whether '_optimized_ids' suffix was found
        - bs_sep (str): Batch separator used ('_', '_chunk_', or '_subset_')
    
    Examples
    --------
    >>> get_file_name_components('/path/to/data_1_2.csv')
    file_components(directory='/path/to', file_name='data', batch_numbers=[1, 2], 
                   file_type='.csv', optimized=False, bs_sep='_')
    
    >>> get_file_name_components('data_5_chunk_3_optimized_ids.parquet')
    file_components(directory=None, file_name='data', batch_numbers=[5, 3], 
                   file_type='.parquet', optimized=True, bs_sep='_chunk_')
    
    Notes
    -----
    The function handles multiple naming patterns and is robust against
    regex match failures. If no batch numbers are found, an empty list
    is returned for batch_numbers.
    """
    if bool(re.search(r'\\|/', file_path)):
        directory: Optional[str] = os.path.dirname(file_path)

        file_path = os.path.basename(file_path)
    else:
        directory = None

    if '.' in file_path:
        file_type: Optional[str] = file_path[file_path.rfind('.'):]
        file_path = file_path.replace(file_type, '')
    else:
        file_type = None

    optimized: bool = bool(re.search(r'_optimized_ids$', file_path, re.IGNORECASE))
    if optimized:
        file_path = re.sub(r'_optimized_ids$', '', file_path, flags=re.IGNORECASE)

    # Pattern matching with null checks to prevent AttributeError
    match = re.search(r'_[0-9]+_[0-9]+$', file_path)
    if match:
        file_name: str = re.sub(r'_[0-9]+_[0-9]+$', '', file_path)
        batch_nums: list = match.group(0)[1:].split('_')
    else:
        match = re.search(r'_[0-9]+_[0-9]+_chunk_[0-9]+$', file_path)
        if match:
            file_name: str = re.sub(r'_[0-9]+_[0-9]+_chunk_[0-9]+$', '', file_path)
            batch_nums: list = match.group(0)[1:].split('_')
        else:
            match = re.search(r'_[0-9]+_chunk_[0-9]+$', file_path)
            if match:
                file_name: str = re.sub(r'_[0-9]+_chunk_[0-9]+$', '', file_path)
                batch_nums: list = match.group(0)[1:].split('_')
            else:
                match = re.search(r'_[0-9]+$', file_path)
                if match:
                    file_name: str = re.sub(r'_[0-9]+$', '', file_path)
                    batch_nums: list = [match.group(0)[1:]]
                else:
                    match = re.search(r'_[0-9]+_[a-z]+_stage$|_[0-9]+_[0-9]+_[a-z]+_stage$', file_path)
                    if match:
                        temp_batches = match.group()
                        file_name = file_path.replace(temp_batches, '')
                        batch_nums: list = re.findall(r'[0-9]+', temp_batches)
                    else:
                        file_name = file_path
                        batch_nums: list = []

    # format to integer array
    if 'chunk' in batch_nums:
        bs_sep: str = '_chunk_'
    elif 'subset' in batch_nums:
        bs_sep: str = '_subset_'
    else:
        bs_sep: str = '_'

    batch_nums = [int(x) for x in batch_nums if (('chunk' not in x) and ('subset' not in x))]

    return file_components(directory, file_name, batch_nums, file_type, optimized, bs_sep)


def tokenize_id(input_str: str, token_index: Optional[int] = None, delimeter: str = '_', ignore_errors: bool = False) -> Optional[str]:
    """
    Split an identifier string using a specified delimiter and optionally extract a specific token.

    This function parses identifier strings by splitting them on a delimiter character.
    If a token_index is provided, it attempts to extract and convert the token at that
    position to an integer (if numeric). The function handles various edge cases including
    null values, single tokens, and conversion errors.

        The input identifier string to be tokenized. Can handle string representations
        of numbers, null values ('nan', 'None'), or any delimited string.
        The zero-based index of the token to extract from the split result.
        If None (default), returns the original input string when multiple tokens exist.
        If provided, attempts to convert the token at this position to an integer.
        The character(s) used to split the input string. Default is '_'.
        Can be any string that serves as a separator.
    ignore_errors : bool, optional
        If True, returns the original input_str when token extraction or conversion fails.
        If False (default), raises an Exception when errors occur during processing.

    Optional[str]
        - None if input_str is null, 'nan', or 'None'
        - Original input_str if it's a single token or if token_index is None with multiple tokens
        - String representation of integer if input_str is numeric (single token case)
        - String representation of integer from the specified token position
        - Original input_str if ignore_errors=True and an error occurs

        Raised when token_index is specified but the token at that position cannot be
        converted to a numeric value, and ignore_errors is False. The exception message
        includes the problematic input string for debugging.

    Examples
    --------
    >>> tokenize_id("user_123_active", token_index=1)
    '123'
    
    >>> tokenize_id("12345")
    '12345'
    
    >>> tokenize_id("item-456-pending", token_index=1, delimeter='-')
    '456'
    
    >>> tokenize_id("invalid_text_here", token_index=1, ignore_errors=True)
    'invalid_text_here'
    """
    if isnull(input_str) or input_str in ['nan', 'None']:
        return None
    tokens = str(input_str).split(delimeter)

    if len(tokens) == 1:
        if isfloat(input_str):
            return str(int(float(input_str)))
        else:
            return input_str

    try:
        if token_index is None:
            return input_str
        return str(int(float(tokens[token_index])))
    except:
        if ignore_errors:
            return input_str

        raise Exception(f'Invalid ID string: {input_str}')
        
    

def _format_time(input_s: str) -> str:

    if notnull(input_s):

        try:
            t = str(input_s).strip().replace(':', '').zfill(4)
            return t[:2] + ':' + t[2:]
        except:
            pass
    return '00:00'

def snake_to_camel_case(snake_str: str, capitalize_first: bool = False) -> str:
    """
    Convert snake_case string to camelCase or PascalCase.
    
    Args:
        snake_str: The snake_case string to convert
        capitalize_first: If True, return PascalCase (first letter capitalized)
                         If False, return camelCase (first letter lowercase)
    
    Returns:
        The converted string in camelCase or PascalCase
        
    Examples:
        >>> snake_to_camel_case('user_name')
        'userName'
        >>> snake_to_camel_case('user_name', capitalize_first=True)
        'UserName'
        >>> snake_to_camel_case('table_id')
        'tableId'
    """
    if not snake_str:
        return snake_str
    
    logger.debug(f"Converting snake_case '{snake_str}' to camelCase (capitalize_first={capitalize_first})", emoji="🔄")
    
    # Split by underscores and filter out empty strings
    components = [comp for comp in snake_str.split('_') if comp]
    
    if not components:
        return snake_str
    
    # First component handling
    if capitalize_first:
        result = components[0].capitalize()
    else:
        result = components[0].lower()
    
    # Capitalize subsequent components
    for component in components[1:]:
        result += component.capitalize()
    
    logger.debug(f"Converted '{snake_str}' to '{result}'", emoji="✅")
    return result


def camel_to_snake_case(camel_str: str, preserve_acronyms: bool = True) -> str:
    """
    Convert camelCase or PascalCase string to snake_case.
    
    Args:
        camel_str: The camelCase/PascalCase string to convert
        preserve_acronyms: If True, preserve consecutive uppercase letters as acronyms
                          If False, split each uppercase letter individually
    
    Returns:
        The converted string in snake_case
        
    Examples:
        >>> camel_to_snake_case('userName')
        'user_name'
        >>> camel_to_snake_case('UserName')
        'user_name'
        >>> camel_to_snake_case('XMLHttpRequest')
        'xml_http_request'
        >>> camel_to_snake_case('XMLHttpRequest', preserve_acronyms=False)
        'x_m_l_http_request'
    """
    if not camel_str:
        return camel_str
    
    logger.debug(f"Converting camelCase '{camel_str}' to snake_case (preserve_acronyms={preserve_acronyms})", emoji="🔄")
    
    import re
    
    if preserve_acronyms:
        # Insert underscores before uppercase letters that follow lowercase letters
        # or before single uppercase letters that precede lowercase letters
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str)
        # Handle sequences of uppercase letters followed by lowercase
        result = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', result)
    else:
        # Insert underscore before every uppercase letter
        result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    
    # Convert to lowercase
    result = result.lower()
    
    logger.debug(f"Converted '{camel_str}' to '{result}'", emoji="✅")
    return result


def convert_identifier_case(identifier: str,
                            target_format: Literal['snake_case', 'camelCase', 'PascalCase', 'upper', 'lower', 'title', 'swapcase', 'capitalize', 'casefold'] = 'snake_case',
                            source_format: str = 'auto',
                            preserve_acronyms: bool = True) -> str:
    """
    Convert identifier between different case formats, including SQL dialect cases.
    
    Args:
        identifier: The identifier to convert
        target_format: Target format ('snake_case', 'camelCase', 'PascalCase', 'upper', 'lower')
        source_format: Source format ('snake_case', 'camelCase', 'PascalCase', 'auto')
                      If 'auto', will attempt to detect the format
    
    Returns:
        The converted identifier
        
    Examples:
        >>> convert_identifier_case('user_name', 'camelCase')
        'userName'
        >>> convert_identifier_case('userName', 'snake_case')
        'user_name'
        >>> convert_identifier_case('UserName', 'snake_case')
        'user_name'
        >>> convert_identifier_case('user_name', 'upper')
        'USER_NAME'
        >>> convert_identifier_case('USER_NAME', 'lower')
        'user_name'
    """
    if not identifier:
        return identifier
    
    logger.debug(f"Converting identifier '{identifier}' from {source_format} to {target_format}", emoji="🔄")
    
    # Handle traditional SQL dialect case conversions first
    if target_format == 'upper':
        result = identifier.upper()
        logger.debug(f"Applied upper case conversion: '{identifier}' -> '{result}'", emoji="🔠")
        return result
    elif target_format == 'lower':
        result = identifier.lower()
        logger.debug(f"Applied lower case conversion: '{identifier}' -> '{result}'", emoji="🔡")
        return result
    elif target_format == 'title':
        result = identifier.title()
        logger.debug(f"Applied title case conversion: '{identifier}' -> '{result}'", emoji="🔡")
        return result
    elif target_format == 'capitalize':
        result = identifier.capitalize()
        logger.debug(f"Applied capitalize conversion: '{identifier}' -> '{result}'", emoji="🔡")
        return result
    elif target_format == 'casefold':
        result = identifier.casefold()
        logger.debug(f"Applied casefold conversion: '{identifier}' -> '{result}'", emoji="🔡")
        return result
    elif target_format == 'swapcase':
        result = identifier.swapcase()
        logger.debug(f"Applied swapcase conversion: '{identifier}' -> '{result}'", emoji="🔡")
        return result

    # Auto-detect source format if needed for naming conventions
    if source_format == 'auto':
        if '_' in identifier:
            source_format = 'snake_case'
        elif identifier[0].isupper():
            source_format = 'PascalCase'
        else:
            source_format = 'camelCase'
        logger.debug(f"Auto-detected source format: {source_format}", emoji="🔍")
    
    # If source and target are the same, return as-is
    if source_format == target_format:
        logger.debug(f"Source and target formats are the same, returning unchanged", emoji="↩️")
        return identifier
    
    # Convert to target format
    result = identifier
    
    # First convert to snake_case if needed
    if source_format in ['camelCase', 'PascalCase']:
        result = camel_to_snake_case(result, preserve_acronyms=preserve_acronyms)
    
    # Then convert to target format
    if target_format == 'camelCase':
        result = snake_to_camel_case(result, capitalize_first=False)
    elif target_format == 'PascalCase':
        result = snake_to_camel_case(result, capitalize_first=True)
    # snake_case is already handled above
    
    logger.debug(f"Final conversion result: '{identifier}' -> '{result}'", emoji="✅")
    return result

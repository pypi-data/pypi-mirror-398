"""
Numerical Operations and Utilities Module

This module provides a comprehensive set of numerical operations, mathematical utilities,
and statistical functions for data science and scientific computing workflows.

Note: This module name 'numbers' may shadow Python's built-in 'numbers' module.
      Consider importing with an alias: `import numbers as num_utils`

The module includes:
- Basic mathematical operations and transformations
- Statistical calculations and descriptive statistics
- Numerical analysis and computational methods
- Data type conversions and validations
- Mathematical constants and helper functions
- Performance-optimized numerical algorithms

Key Features:
- Cross-library compatibility (NumPy, SciPy, pandas)
- Memory-efficient implementations
- Robust error handling and input validation
- Vectorized operations for performance
- Support for different numerical data types
- Integration with the Ruppert20 ecosystem

Usage Example:
    ```python
    import src.numbers as num_utils  # Use alias to avoid stdlib conflict
    
    # Example usage will be added as functions are implemented
    ```

Supported Operations:
- Arithmetic operations and transformations
- Statistical measures (mean, median, std, etc.)
- Mathematical functions (log, exp, trig functions)
- Data validation and type checking
- Numerical conversions and formatting
- Array and matrix operations

Dependencies:
- numpy (required)
- scipy (optional, for advanced functions)
- pandas (optional, for data structure integration)

Author: Ruppert20
Created: July 2025
Version: 0.0.1
License: MIT
"""

# Version information
__version__ = "0.0.1"
__author__ = "Ruppert20"
__license__ = "MIT"

# Standard library imports
import math
from typing import Optional, Union
from decimal import Decimal
import re
import pandas as pd



# Mathematical constants
PI = math.pi
E = math.e
TAU = 2 * math.pi
GOLDEN_RATIO = (1 + math.sqrt(5)) / 2
EULER_MASCHERONI = 0.5772156649015329  # Euler-Mascheroni constant

# Tolerance values for numerical comparisons
DEFAULT_TOLERANCE = 1e-9
FLOAT_TOLERANCE = 1e-7
DOUBLE_TOLERANCE = 1e-15


# local imports
from .generics import isnull


def extract_num(input_str: str, return_pos: int = 0, abs_value: bool = False) -> Optional[str]:
    """
    Extract number from specified position.

    Parameters
    ----------
    input_str : str
        string to parse.
    return_pos : int, optional
        Location in found numbers to return. The default is 0.
    abs_value : bool, optional
        Whether to force abolute value or not. The default is False.

    Returns
    -------
    str
        DESCRIPTION.

    """
    # check if blank
    if isnull(input_str):
        return None
    else:
        input_str = str(input_str)

    # force absolute value if there is a letter preceeding a dash
    if bool(re.search(r'[A-z]\-[0-9]', input_str)):
        abs_value = True

    # recognize dates and return None
    elif bool(re.search(r'[0-9]{4}\-[0-9]{2}\-[0-9]{2}|[0-9]{4}/[0-9]{2}/[0-9]{2}|[0-9]{2}\-[0-9]{2}\-[0-9]{4}|[0-9]{2}/[0-9]{2}/[0-9]{4}', input_str)):
        return None

    # extract number and operator
    nums = re.findall(r'(-|neg|neg\s|negative\s|negative|<\s|<|<=\s|<=|>\s|>|>=\s|>=|=\s|=|)([0-9][0-9,.]+[0-9]+|[0-9]+)', input_str, re.IGNORECASE)

    # return None if no numberser identified
    if len(nums) == 0:
        return None

    # average ranges
    elif bool(re.search(r'[0-9]\-[0-9]', input_str)):
        if len(nums) == 2:
            try:
                num1 = _format_number(nums[0], abs_value=abs_value)
                num2 = _format_number(nums[1], abs_value=True)
                if num1 is not None and num2 is not None:
                    return str((num1 + num2) / 2)
            except Exception:
                pass
        return None
    elif len(nums) > 3:
        return None
    else:
        formatted_num = _format_number(nums[return_pos], abs_value=abs_value)
        return str(formatted_num) if formatted_num is not None else None
    
def isfloat(value) -> bool:
    """
    Check if a value can be converted to or is already a float.
    This function determines whether the input value is either already a float
    or can be safely converted to a float without raising an exception.
    Args:
        value: The value to check. Can be of any type including:
            - Numeric types (int, float, Decimal)
            - String representations of numbers
            - None or null values
            - Any other object type
    Returns:
        bool: True if the value is a float or can be converted to float,
              False otherwise.
    Examples:
        >>> isfloat(3.14)
        True
        >>> isfloat("3.14")
        True
        >>> isfloat(42)
        True
        >>> isfloat("not a number")
        False
        >>> isfloat(None)
        False
        >>> isfloat("")
        False
        >>> isfloat("inf")
        True
        >>> isfloat("-123.456")
        True
    Note:
        - Returns False for null/None values
        - Handles special float values like 'inf', '-inf', 'nan'
        - Works with Decimal objects and other numeric types
        - Safe to use with any input type without raising exceptions
    """
    if isnull(value):
        return False
    
    # If already a float, return True immediately
    if isinstance(value, float):
        return True
    
    # If it's a string, try conversion
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    # For other numeric types that can be converted to float
    if isinstance(value, (int, Decimal)):
        return True
    
    # For any other type, try conversion as last resort
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False
    
    
def _format_number(input_tuple: str, abs_value: bool = False) -> Optional[float]:
    """
    Convert a formatted number string from a tuple into a float value.
    
    This function processes number strings that may contain formatting characters
    and determines the sign based on tuple context or explicit negative indicators.
    
    Args:
        input_tuple (tuple): A tuple containing two elements:
            - [0]: Context string that may contain sign indicators ('neg', '-')
            - [1]: Number string that may contain formatting characters (',', '...', '..')
        abs_value (bool, optional): If True, ignores negative indicators and returns
            absolute value. Defaults to False.
    
    Returns:
        Optional[float]: The parsed float value with appropriate sign, or None if
            parsing fails.
    
    Processing Rules:
        - Removes commas (',') from the number string
        - Converts multiple dots ('...', '..') to single dot ('.')
        - Applies negative multiplier if:
            * 'neg' appears in context string (case-insensitive), OR
            * '-' appears in context string AND abs_value is False
        - Returns positive value if abs_value is True regardless of context
    
    Examples:
        >>> _format_number(('positive', '1,234.56'))
        1234.56
        >>> _format_number(('neg_value', '1,234.56'))
        -1234.56
        >>> _format_number(('-amount', '1,234.56'), abs_value=True)
        1234.56
        >>> _format_number(('invalid', 'not_a_number'))
        None
    
    Note:
        This is a private helper function intended for internal number formatting
        operations. Invalid input that cannot be converted to float returns None.
    """
    input_str: str = input_tuple[1].replace(',', '').replace('...', '.').replace('..', '.')
    multiplier: int = -1 if (('neg' in input_tuple[0].lower()) or (('-' in input_tuple[0]) and (not abs_value))) else 1
    try:
        return float(input_str) * multiplier
    except:
        return None

def convert_to_comma_seperated_integer_list(input_value: Union[str, int, pd.Series, list]) -> str:
    """
    Converts an input value (string, integer, list, or pandas Series) into a comma-separated string of integers.

    input_value : Union[str, int, pd.Series, list]
        The input to be converted. Accepts:
            - str: A single integer value as a string, or a comma-separated string of integers.
            - int: A single integer value.
            - list: A list of values convertible to integers.
            - pd.Series: A pandas Series of values convertible to integers.

        A comma-separated string of integers.

    Raises
    ------
    Exception
        If the input cannot be converted to a list of integers or is of an unsupported type.

    Notes
    -----
    - Non-integer values in lists or Series will be converted to float first, then to integer (truncating decimals).
    - NaN values in lists or Series are dropped.
    - If the input is a string containing commas, it is assumed to already be a comma-separated list of integers and returned as-is.
    - If the input is a string representing a single number, it is converted to an integer and returned as a string.
    - For unsupported types or conversion errors, an Exception is raised with details about the input and error.

    Examples
    --------
    >>> convert_to_comma_seperated_integer_list("1,2,3")
    '1,2,3'
    >>> convert_to_comma_seperated_integer_list("42")
    '42'
    >>> convert_to_comma_seperated_integer_list([1, 2.5, None, 3])
    '1,2,3'
    >>> convert_to_comma_seperated_integer_list(pd.Series([4, 5.7, None, 6]))
    '4,5,6'
    """
    try:
        if isinstance(input_value, str):
            if ',' in input_value:
                id_list = input_value
            else:
                id_list = str(int(float(input_value)))
        elif isinstance(input_value, int):
            id_list = str(input_value)
        elif isinstance(input_value, list):
            id_list = ','.join(pd.Series(input_value).dropna().astype(float).astype(int).astype(str))
        elif isinstance(input_value, pd.Series):
            id_list = ','.join(input_value.dropna().astype(float).astype(int).astype(str))
        else:
            raise Exception(f'Invalid input format: {input_value}')

        return id_list
    except Exception as e:
        raise Exception(f'Invalid input, {e}, {input_value}')
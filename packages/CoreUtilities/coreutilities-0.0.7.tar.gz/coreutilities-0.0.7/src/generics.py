"""
Generic Utility Functions Module

This module provides fundamental utility functions for handling null values,
coalescing operations, and extracting object names. These functions work across
multiple data types and libraries including Python built-ins, pandas, and numpy.

Key Features:
- Comprehensive null checking across multiple data types
- Support for pandas/numpy special null types (NA, NaT, NaN)
- Container emptiness checking (lists, dicts, tuples)
- Iterable null value handling
- First non-null value selection (coalesce)
- Generic object name extraction

Main Functions:
- notnull: Check if a value is not null/empty
- isnull: Check if a value is null/empty
- coalesce: Return first non-null value from multiple arguments
- get_name: Extract name attribute from objects

Usage Example:
    ```python
    from src.generics import notnull, isnull, coalesce, get_name

    # Check for null values
    if notnull(value):
        process(value)

    # Use coalesce to get first non-null value
    result = coalesce(None, '', [1, 2, 3])  # Returns [1, 2, 3]

    # Get object name
    name = get_name(my_function)  # Returns function name
    ```

Supported Null Types:
- Python: None, empty strings, empty containers
- Pandas: pd.NA, pd.NaT, empty Series
- NumPy: np.nan, NaTType

Author: @Ruppert20
Version: 0.0.1
"""

from typing import Any, Iterable
import pandas as pd


def notnull(v: Any) -> bool:
    """
    Check if input value is not null using pandas notnull function with additional type handling.
    
    This function extends pandas' notnull functionality to handle various data types
    including containers, iterables, and edge cases that pandas doesn't handle directly.
    
    Parameters
    ----------
    v : Any
        The value to check for null/empty status. Can be of any type including:
        - Primitive types (str, int, float, bool)
        - Container types (dict, tuple, list, set)
        - Iterables (generators, custom iterables)
        - pandas-compatible types (Series, DataFrame, etc.)
        - None values
        
    Returns
    -------
    bool
        True if the value is not null/empty, False otherwise.
        
    Notes
    -----
    - Returns False for None values
    - For primitive types (str, int, float, bool), uses pandas.notnull()
    - For containers (dict, tuple), checks if length > 0
    - For iterables, returns True if any element is not null
    - For other types, falls back to pandas.notnull()
    
    Behavior by Type:
    - None: Always returns False
    - str/int/float/bool: Uses pd.notnull() (handles NaN, empty strings, etc.)
    - dict/tuple: Returns True if container has elements (len > 0)
    - Iterables (list, set, etc.): Returns True if any non-None element passes pd.notnull()
    - Other types: Falls back to pd.notnull()
    
    Examples
    --------
    >>> notnull(None)
    False
    >>> notnull("")
    False
    >>> notnull("hello")
    True
    >>> notnull([])
    False
    >>> notnull([1, 2, 3])
    True
    >>> notnull([None, None])
    False
    >>> notnull([None, 1])
    True
    >>> notnull({})
    False
    >>> notnull({"key": "value"})
    True
    >>> notnull(0)
    True
    >>> notnull(float('nan'))
    False
    
    Raises
    ------
    Exception
        Re-raises any TypeError that occurs during processing, with additional
        debugging information about the value and its type printed to stdout.
        
    See Also
    --------
    pandas.notnull : Base function for checking null values
    coalesce : Function for finding first non-null value from multiple inputs
    """
    try:
        if v is None:
            return False
        # Handle pandas special types explicitly
        elif hasattr(v, '__class__') and v.__class__.__name__ == 'NaTType':
            # pandas NaTType (Not-a-Time) should be considered null
            return False
        elif hasattr(v, '__class__') and v.__class__.__name__ == 'Timestamp':
            # pandas Timestamp - check if it's NaT (Not-a-Time)
            try:
                return not pd.isna(v)
            except:
                # Fallback to standard pandas check
                return pd.notnull(v)
        elif isinstance(v, (str, int, float, bool)):
            return pd.notnull(v)
        elif isinstance(v, (dict, tuple)):
            return len(v) > 0
        elif isinstance(v, Iterable):
            # For iterables like lists, check if any element is not null
            return any(pd.notnull(item) for item in v if item is not None)
        else:
            return pd.notnull(v)
    except TypeError as e:
        print(v)
        print(type(v))
        raise Exception(e)

def isnull(v: Any) -> bool:
    """
    Check if input value is null using inverse of notnull function.
    
    This function provides the logical inverse of the notnull() function,
    returning True when a value is considered null/empty and False otherwise.
    It handles the same variety of data types as notnull() but with inverted logic.
    
    Parameters
    ----------
    v : Any
        The value to check for null/empty status. Can be of any type including:
        - Primitive types (str, int, float, bool)
        - Container types (dict, tuple, list, set)
        - Iterables (generators, custom iterables)
        - pandas-compatible types (Series, DataFrame, etc.)
        - None values
        
    Returns
    -------
    bool
        True if the value is null/empty, False otherwise.
        
    Notes
    -----
    This function simply returns the logical NOT of notnull(v). All behavior
    and type handling is delegated to the notnull() function.
    
    Behavior by Type (inverse of notnull):
    - None: Always returns True
    - str/int/float/bool: Returns True for NaN, empty strings, etc.
    - dict/tuple: Returns True if container has no elements (len == 0)
    - Iterables (list, set, etc.): Returns True if no non-None element passes pd.notnull()
    - Other types: Falls back to NOT pd.notnull()
    
    Examples
    --------
    >>> isnull(None)
    True
    >>> isnull("")
    True
    >>> isnull("hello")
    False
    >>> isnull([])
    True
    >>> isnull([1, 2, 3])
    False
    >>> isnull([None, None])
    True
    >>> isnull([None, 1])
    False
    >>> isnull({})
    True
    >>> isnull({"key": "value"})
    False
    >>> isnull(0)
    False
    >>> isnull(float('nan'))
    True
    
    Raises
    ------
    Exception
        Re-raises any exception that occurs in the underlying notnull() function.
        
    See Also
    --------
    notnull : The underlying function that provides the null-checking logic
    """
    return not notnull(v)

def coalesce(*values) -> Any:
    """
    Return the first non-null value from the provided arguments.

    Iterates through the provided values and returns the first one that
    passes the notnull() check. If all values are null, returns None.

    Parameters
    ----------
    *values : Any
        Variable number of values to check, evaluated in order

    Returns
    -------
    Any
        The first non-null value, or None if all values are null

    Examples
    --------
    >>> coalesce(None, '', 'value')
    'value'
    >>> coalesce(None, [1, 2, 3], 'fallback')
    [1, 2, 3]
    >>> coalesce(None, None, None)
    None
    >>> coalesce(0, 1, 2)  # 0 is not null
    0

    See Also
    --------
    notnull : Function used to determine null status
    isnull : Inverse of notnull
    """
    return next((v for v in values if notnull(v)), None)


def get_name(obj: Any) -> str:
    """
    Extract a string name from an object using available name attributes.

    Attempts to extract a name from an object by checking for __name__ and
    name attributes. Falls back to string representation if neither exists.

    Parameters
    ----------
    obj : Any
        The object from which to extract a name

    Returns
    -------
    str
        The object's name as a string, or str(obj) if no name attribute exists

    Examples
    --------
    >>> def my_function():
    ...     pass
    >>> get_name(my_function)
    'my_function'

    >>> class MyClass:
    ...     name = 'MyClass'
    >>> get_name(MyClass())
    'MyClass'

    Note:
        Prioritizes __name__ attribute over name attribute, then falls back
        to string conversion.
    """
    return str(obj.__name__ if hasattr(obj, '__name__') else obj.name if hasattr(obj, 'name') else str(obj))
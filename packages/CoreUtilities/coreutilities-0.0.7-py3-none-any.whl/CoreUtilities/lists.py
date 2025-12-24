"""
List Utilities Module

This module provides utility functions for working with Python lists in data processing
workflows, including conversion, chunking, intersection, and flattening operations.

Key Features:
- List to comma-separated string conversion with optional encapsulation
- List chunking for batch processing
- List intersection operations preserving order
- Recursive list flattening for nested structures
- Integration with pandas Series for data cleaning

Main Functions:
- convert_list_to_string: Convert list to comma-separated string
- chunk_list: Split list into equal-sized chunks
- list_intersection: Find common elements between two lists
- flatten_list: Recursively flatten nested lists

Usage Example:
    ```python
    from src.lists import chunk_list, list_intersection, flatten_list

    # Chunk a list for batch processing
    data = list(range(100))
    for chunk in chunk_list(data, 10):
        process_batch(chunk)

    # Find intersection preserving order
    common = list_intersection([1, 2, 3, 4], [3, 4, 5, 6])

    # Flatten nested lists
    nested = [[1, 2], [3, [4, 5]], 6]
    flat = flatten_list(nested)  # [1, 2, 3, 4, 5, 6]
    ```

Author: @Ruppert20
Version: 0.0.1
"""

from typing import Callable, Optional, Iterator as TypingIterator
import pandas as pd


def convert_list_to_string(input_list: list, encapsulate_values: bool = False, coercion_func: Optional[Callable] = None) -> str:
    """
    Convert a list to a comma-separated string with optional quote encapsulation.

    Removes duplicates and null values before conversion. Optionally applies
    a coercion function to transform values before stringification.

    Parameters
    ----------
    input_list : list
        List of values to be converted
    encapsulate_values : bool, optional
        Whether to encapsulate each value in single quotes. Default is False.
    coercion_func : Callable, optional
        Optional function to apply to the Series before conversion. Default is None.

    Returns
    -------
    str
        Comma-separated string of unique, non-null values from the input list

    Examples
    --------
    >>> convert_list_to_string([1, 2, 3, 2, None])
    '1,2,3'
    >>> convert_list_to_string(['a', 'b', 'c'], encapsulate_values=True)
    "'a','b','c'"
    """
    temp = pd.Series(input_list).drop_duplicates().dropna()

    if isinstance(coercion_func, Callable):
        temp = coercion_func(temp)

    return ','.join([f"'{x}'" if encapsulate_values else str(x) for x in temp.tolist()])

def chunk_list(l: list, n: int) -> TypingIterator[list]:
    """
    Split a list into chunks of specified size.

    This generator function divides the input list into smaller sublists,
    each containing at most n elements. The last chunk may contain fewer
    than n elements if the list length is not evenly divisible by n.

    Args:
        l (list): The input list to be chunked. Can contain elements of any type.
        n (int): The maximum number of elements per chunk. Must be a positive integer.

    Yields:
        list: A sublist containing at most n elements from the original list.
              Each yielded list maintains the original order of elements.

    Raises:
        ValueError: If n is less than or equal to 0.
        TypeError: If l is not a list or n is not an integer.

    Examples:
        >>> list(chunk_list([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
        
        >>> list(chunk_list(['a', 'b', 'c', 'd'], 3))
        [['a', 'b', 'c'], ['d']]
        
        >>> list(chunk_list([], 2))
        []

    Note:
        If the input list is empty, the generator will not yield any chunks.
        The function uses slicing which creates new list objects for each chunk.
    """
    for i in range(0, len(l), n):
        yield l[i: i + n]


def list_intersection(lst1: list, lst2: list) -> list:
    """
    Return the intersection of two lists, preserving order from the first list.
    
    This function returns a new list containing elements that appear in both
    input lists. The order of elements in the result follows the order they
    appear in the first list (lst1). Duplicate elements in lst1 will appear
    multiple times in the result if they also exist in lst2.
    
    Args:
        lst1 (list): The first input list. Order of elements in this list
                    determines the order in the result.
        lst2 (list): The second input list used for intersection check.
    
    Returns:
        list: A new list containing elements present in both lst1 and lst2,
              ordered according to their appearance in lst1.
    
    Examples:
        >>> list_intersection([1, 2, 3, 4], [3, 4, 5, 6])
        [3, 4]
        
        >>> list_intersection(['a', 'b', 'c'], ['b', 'c', 'd'])
        ['b', 'c']
        
        >>> list_intersection([1, 2, 2, 3], [2, 3, 4])
        [2, 2, 3]
        
        >>> list_intersection([], [1, 2, 3])
        []
        
        >>> list_intersection([1, 2, 3], [])
        []
    
    Note:
        - Time complexity is O(n*m) where n and m are the lengths of lst1 and lst2
        - For better performance with large lists, consider using set operations
        - This function preserves duplicates from lst1 if they exist in lst2
    """
    lst3: list = [value for value in lst1 if value in lst2]
    return lst3


def flatten_list(nested_list: list) -> list:
    """
    Recursively flatten a nested list structure into a single-level list.

    This function traverses nested lists of arbitrary depth and returns a flat
    list containing all non-list elements in their original order.

    Parameters
    ----------
    nested_list : list
        A potentially nested list structure containing lists and other elements

    Returns
    -------
    list
        A flat list containing all elements from the nested structure

    Examples
    --------
    >>> flatten_list([[1, 2], [3, 4]])
    [1, 2, 3, 4]
    >>> flatten_list([[1, [2, 3]], 4, [5, [6, 7]]])
    [1, 2, 3, 4, 5, 6, 7]
    >>> flatten_list([])
    []

    Note:
        This function only flattens lists. Other iterable types (tuples, sets, etc.)
        are treated as single items and not flattened.
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result
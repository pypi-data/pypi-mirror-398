"""
Dictionary Utilities Module

This module provides utility functions for working with dictionaries in data processing
workflows, particularly for pandas DataFrame groupby aggregation operations.

Key Features:
- Creation of aggregation dictionaries for pandas groupby operations
- Automatic handling of grouping column exclusions
- Support for start/end column min/max operations
- Flexible column-to-aggregation-function mapping

Main Functions:
- create_aggregation_dict: Create aggregation dictionaries for pandas groupby.agg()

Usage Example:
    ```python
    import pandas as pd
    from src.dictionaries import create_aggregation_dict

    # Define aggregation strategy
    col_dict = {
        'sum': ['sales', 'profit'],
        'mean': ['rating'],
        'grouping': ['region', 'category']
    }

    # Create aggregation dict
    agg_dict = create_aggregation_dict(
        col_dict,
        start_col='date_start',
        end_col='date_end'
    )

    # Use with pandas groupby
    df.groupby(['region', 'category']).agg(agg_dict)
    ```

Author: @Ruppert20
Version: 0.0.1
"""

from typing import Optional

def create_aggregation_dict(col_action_dict: dict,
                            start_col: Optional[str] = None, end_col: Optional[str] = None) -> dict:
    """
    Create an aggregation dictionary for pandas DataFrame groupby operations.
    
    This function processes a column-action mapping dictionary to create a properly
    formatted aggregation dictionary that can be passed to pandas groupby.agg() method.
    It excludes grouping columns from aggregation and optionally adds min/max operations
    for start and end columns.
    
    Parameters
    ----------
    col_action_dict : dict
        A dictionary mapping aggregation functions to lists of column names.
        Must contain a 'grouping' key with columns to be excluded from aggregation.
        Example: {
            'sum': ['col1', 'col2'],
            'mean': ['col3'],
            'grouping': ['group_col1', 'group_col2']
        }
    start_col : str, optional
        Column name to be aggregated with 'min' function. If provided and is a string,
        it will be added to the aggregation dictionary with 'min' operation.
        Default is None.
    end_col : str, optional
        Column name to be aggregated with 'max' function. If provided and is a string,
        it will be added to the aggregation dictionary with 'max' operation.
        Default is None.
    
    Returns
    -------
    dict
        A dictionary mapping column names to aggregation functions, suitable for
        use with pandas groupby.agg() method.
        Example: {'col1': 'sum', 'col2': 'sum', 'col3': 'mean', 'start_col': 'min'}
    
    Notes
    -----
    - Columns listed under 'grouping' key are automatically excluded from the final
        aggregation dictionary, even if they appear in other aggregation function lists.
    - If start_col or end_col are specified but already exist in the aggregation
        dictionary, they will be overwritten with 'min' and 'max' respectively.
    - KeyError exceptions are silently handled when attempting to remove grouping
        columns that don't exist in the aggregation dictionary.
    
    Examples
    --------
    >>> col_dict = {
    ...     'sum': ['sales', 'profit'],
    ...     'mean': ['rating'],
    ...     'grouping': ['region', 'category']
    ... }
    >>> create_aggregation_dict(col_dict, start_col='date_start', end_col='date_end')
    {'sales': 'sum', 'profit': 'sum', 'rating': 'mean', 'date_start': 'min', 'date_end': 'max'}
    """

    d: dict = {}
    for key in col_action_dict:
        if key != 'grouping':
            d.update({x: key for x in col_action_dict[key]})

    for col in col_action_dict['grouping']:
        try:
            del d[col]
        except KeyError:
            pass

    if start_col or end_col:
        if isinstance(start_col, str):
            d[start_col] = 'min'

        if isinstance(end_col, str):
            d[end_col] = 'max'

    return d
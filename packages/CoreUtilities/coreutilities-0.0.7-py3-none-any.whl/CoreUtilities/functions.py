"""
Function Utilities and Introspection Module

This module provides utilities for working with Python functions including dynamic
function loading, introspection, parameter filtering, and debugging capabilities.

Key Features:
- Dynamic function loading from module paths
- Function signature extraction and analysis
- Parameter filtering and validation
- Class introspection for properties and methods
- Function serialization and deserialization
- Debug utilities for function inputs

Main Functions:
- get_func: Dynamically load functions from string paths
- filter_kwargs: Filter kwargs to match function parameters
- get_function_signature: Extract comprehensive function metadata
- inspect_class: Extract class properties and methods
- debug_inputs: Debug and optionally serialize function inputs
- convert_func_to_string: Convert function to string representation

Usage Example:
    ```python
    from src.functions import get_func, filter_kwargs, get_function_signature

    # Load a function dynamically
    func = get_func('json.loads')

    # Filter kwargs to match function signature
    kwargs = {'a': 1, 'b': 2, 'c': 3}
    filtered = filter_kwargs(my_func, kwargs)

    # Get function signature metadata
    sig_info = get_function_signature(my_func)
    ```

Security Considerations:
- Dynamic imports from untrusted sources should be validated
- get_func uses importlib which can execute arbitrary code
- Ensure input validation in security-sensitive contexts

Author: @Ruppert20
Version: 0.0.1
"""

from typing import Callable, Optional, Dict, Any, Tuple, Union, List, Set
import pickle
import inspect
import importlib
import re
import logging


def convert_func_to_string(func: Callable) -> str:
    """
    Convert a function to its fully qualified string representation.

    Creates a string in the format 'module.name' that can be used to
    identify or reload the function later using get_func().

    Parameters
    ----------
    func : Callable
        The function to convert to string format

    Returns
    -------
    str
        Fully qualified function name in format 'module_name.function_name'

    Examples
    --------
    >>> import json
    >>> convert_func_to_string(json.loads)
    'json.loads'
    """
    return '.'.join([func.__module__, func.__name__])


def is_pickleable(obj) -> bool:
    """
    Check if an object can be serialized using pickle.

    Attempts to serialize the object with pickle.dumps(). Returns True if
    successful, False if any pickle-related error occurs.

    Parameters
    ----------
    obj : Any
        The object to test for pickle compatibility

    Returns
    -------
    bool
        True if the object can be pickled, False otherwise

    Examples
    --------
    >>> is_pickleable({'key': 'value'})
    True
    >>> is_pickleable(lambda x: x)
    False
    """
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, TypeError, AttributeError):
        return False

def debug_inputs(function: Callable, kwargs: dict, dump_fp: Optional[str] = None) -> Dict[str, Any] | None:
    """
    Function debugging utility.
    
    Extracts function parameters from kwargs and optionally dumps them to a file.
    Only includes pickleable objects when dump_fp is provided.
    
    Parameters
    ----------
    function : Callable
        Function whose parameters will be extracted.
    kwargs : dict
        Dictionary containing variable names and values (recommended to use locals()).
    dump_fp : str, optional
        File path where the parameters will be pickled. If None, no file is created.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing function parameters and their values. If dump_fp is provided,
        only includes pickleable objects.
    """
    
    sig, vard = inspect.signature(function), kwargs
    func_input: Dict[str, Any] = {param.name: vard[param.name] for param in sig.parameters.values() if (is_pickleable(vard[param.name]) if isinstance(dump_fp, str) else True)}

    if isinstance(dump_fp, str):
        pickle.dump(func_input, open(dump_fp, 'wb'))

    return func_input


def get_func(input_str: str):
    """
    Dynamically retrieve a function object from its string representation.
    
    This function supports loading functions from multiple sources:
    1. Local namespace (functions defined in current scope)
    2. Global namespace (functions defined at module level)
    3. External modules (using dot notation: 'module.submodule.function')
    
    The function uses importlib for dynamic module importing when dot notation
    is detected, making it useful for plugin systems, configuration-driven
    function loading, and runtime function resolution.
    
        The function identifier. Can be either:
        - Simple function name: 'my_function' (searches local/global namespaces)
        - Qualified module path: 'package.module.function' (imports module dynamically)
        - Examples: 'numpy.sum', 'os.path.join', 'my_module.my_function'
        
    callable or None
        The function object if successfully found and loaded, None otherwise.
        Returns None when:
        - Function name not found in any namespace
        - Module import fails
        - Attribute doesn't exist in specified module
        - Any other loading error occurs
        
    Notes
    -----
    - Uses regex pattern r'(?<!\\\\)\\.' to detect unescaped dots for module separation
    - Searches namespaces in order: local -> global -> import module
    - Logs warning message when function loading fails
    - Safe error handling prevents exceptions from propagating
    
    Examples
    --------
    >>> # Load from global namespace
    >>> func = get_func('print')
    >>> func('Hello')  # Same as print('Hello')
    
    >>> # Load from external module
    >>> json_loads = get_func('json.loads')
    >>> data = json_loads('{"key": "value"}')
    
    >>> # Handle missing function gracefully
    >>> missing = get_func('nonexistent.function')
    >>> print(missing)  # None
    
    Warnings
    --------
    This function uses dynamic imports and attribute access, which can pose
    security risks if used with untrusted input. Ensure input validation
    in security-sensitive contexts.
    """
    if bool(re.search(r'(?<!\\)\.', input_str)):
        mod_name, func_name = input_str.rsplit('.', 1)

        try:
            return getattr(
                locals().get(mod_name)
                or globals().get(mod_name)
                or importlib.import_module(mod_name),
                func_name)
        except:
            logging.warning(msg=f'Unable to load functon: {input_str}')
            return None
    else:
        return locals().get(input_str) or globals().get(input_str)
    

def filter_kwargs(func: Callable, kwargs: dict) -> dict:
    """
    Filter a dictionary of keyword arguments to only include those accepted by a given function.
    
    Parameters
    ----------
    func : Callable
        The function whose parameters will be used for filtering.
    kwargs : dict
        The dictionary of keyword arguments to filter.
        
    Returns
    -------
    dict
        A new dictionary containing only the key-value pairs from `kwargs` that match the parameter names of `func`.
        
    Examples
    --------
    >>> def example_func(a, b, c=3):
    ...     pass
    ...
    >>> kwargs = {'a': 1, 'b': 2, 'c': 4, 'd': 5}
    >>> filtered = filter_kwargs(example_func, kwargs)
    >>> print(filtered)
    {'a': 1, 'b': 2, 'c': 4}
    
    Notes
    -----
    - This function uses the `inspect` module to retrieve the signature of `func`.
    - Only parameters that are explicitly defined in `func` will be included in the output dictionary.
    - Extra keys in `kwargs` that do not correspond to any parameter in `func` will be ignored.
    """
    sig = inspect.signature(func)
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def inspect_class(cls: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Inspects a class and extracts its properties and methods.

    Args:
        cls: The class to inspect.

    Returns:
        A tuple containing two dictionaries: (properties, methods).
    """
    properties_info: Dict[str, Any] = {}
    methods_info: Dict[str, Any] = {}

    for name, member in inspect.getmembers(cls):
        # --- Inspect Methods ---
        if inspect.isfunction(member):
            sig = inspect.signature(member)
            params = {}
            for param in sig.parameters.values():
                param_info = {
                    "kind": str(param.kind),
                    "default": "NO_DEFAULT" if param.default is inspect.Parameter.empty else param.default,
                }
                params[param.name] = param_info

            methods_info[name] = {
                "docstring": inspect.getdoc(member),
                "parameters": params,
                "return_annotation": str(sig.return_annotation) if sig.return_annotation is not inspect.Signature.empty else "Any"
            }

        # --- Inspect Properties ---
        elif isinstance(member, property):
            properties_info[name] = {
                "docstring": inspect.getdoc(member),
                "fget": member.fget.__name__ if member.fget else None,
                "fset": member.fset.__name__ if member.fset else None,
                "fdel": member.fdel.__name__ if member.fdel else None,
            }

    return properties_info, methods_info


def get_function_signature(func: Callable) -> Dict[str, Any]:
    """
    Extract structured metadata from a function signature.
    
    Analyzes a function and returns comprehensive metadata including function name,
    parameters with their names, types, and default values.
    
    Parameters
    ----------
    func : Callable
        The function to analyze
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'name': str - Function name only
        - 'module': str - Module where function is defined  
        - 'qualified_name': str - Full module path + function name
        - 'docstring': str - Function docstring
        - 'parameters': List[Dict] - List of parameter metadata
        - 'return_annotation': str - Return type annotation
        
    Each parameter dict contains:
        - 'name': str - Parameter name
        - 'type': str - Type annotation (or 'Any' if not specified)
        - 'default': Any - Default value (or 'NO_DEFAULT' if required)
        - 'kind': str - Parameter kind (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, etc.)
        
    Examples
    --------
    >>> def example_func(a: int, b: str = "default", *args, **kwargs) -> bool:
    ...     '''Example function docstring'''
    ...     return True
    ...
    >>> metadata = get_function_signature(example_func)
    >>> print(metadata['name'])
    'example_func'
    >>> print(len(metadata['parameters']))
    4
    >>> print(metadata['parameters'][0]['name'])
    'a'
    >>> print(metadata['parameters'][1]['default'])
    'default'
    """
    sig = inspect.signature(func)
    
    parameters = []
    for param in sig.parameters.values():
        param_info = {
            'name': param.name,
            'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
            'default': param.default if param.default != inspect.Parameter.empty else 'NO_DEFAULT',
            'kind': str(param.kind)
        }
        parameters.append(param_info)
    
    return {
        'name': func.__name__,
        'module': func.__module__,
        'qualified_name': f"{func.__module__}.{func.__name__}" if func.__module__ else func.__name__,
        'docstring': inspect.getdoc(func) or '',
        'parameters': parameters,
        'return_annotation': str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else 'Any'
    }

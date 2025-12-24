"""
Memory Profiling and Object Analysis Module

This module provides utilities for analyzing Python object memory usage and
identifying memory-intensive components in nested data structures. It includes
cycle-safe deep memory analysis and tools for finding large objects.

Key Features:
- Deep memory size calculation with cycle detection
- Support for NumPy arrays and pandas data structures
- Recursive traversal of nested containers (dicts, lists, sets)
- Large object identification with configurable thresholds
- Memory usage reporting with object counts
- Library-specific optimizations (NumPy, pandas, PyArrow)

Main Functions:
- deep_stats: Calculate deep memory size and object count
- find_large_objects: Recursively find objects exceeding size threshold
- _base_size: Calculate shallow size with library-specific adjustments

Usage Example:
    ```python
    from src.iterables import deep_stats, find_large_objects

    # Calculate deep memory usage
    data = {'arrays': [np.ones(1000) for _ in range(10)]}
    size_bytes, n_objects = deep_stats(data)
    print(f"Total size: {size_bytes / 1024:.2f} KB, Objects: {n_objects}")

    # Find large objects exceeding threshold
    large_objs = find_large_objects(data, threshold_kb=10.0)
    for obj in large_objs:
        print(f"{obj['path']}: {obj['size_kb']} KB ({obj['n_objects']} objects)")
    ```

Memory Calculation Details:
- Uses sys.getsizeof() for base object size
- Adds buffer sizes for NumPy arrays (nbytes)
- Includes memory_usage(deep=True) for pandas structures
- Handles __dict__ and __slots__ for custom classes
- Cycle detection prevents infinite recursion

Author: @Ruppert20
Version: 0.0.1
"""

import sys
from collections.abc import Mapping, Sequence, Set
import pandas as pd
import numpy as np


def _base_size(obj) -> int:
    """
    Return the shallow size of `obj`, with library-specific adjustments.
    """
    # NumPy arrays: count the buffer too
    if np is not None and isinstance(obj, np.ndarray):
        # sys.getsizeof covers the Python object header; nbytes is the data buffer
        return sys.getsizeof(obj) + int(getattr(obj, "nbytes", 0))

    # pandas: use memory_usage(deep=True) for the data buffers
    if pd is not None and isinstance(obj, (pd.Series, pd.Index)):
        try:
            return sys.getsizeof(obj) + int(obj.memory_usage(deep=True))
        except Exception:
            return sys.getsizeof(obj)
    if pd is not None and isinstance(obj, pd.DataFrame):
        try:
            return sys.getsizeof(obj) + int(obj.memory_usage(deep=True).sum())
        except Exception:
            return sys.getsizeof(obj)

    return sys.getsizeof(obj)


def deep_stats(obj, memo=None, _seen=None):
    """
    Compute the deep size (bytes) and distinct object count for `obj`,
    traversing into dicts, lists/tuples, sets, etc. Cycle-safe, memoized.
    Returns (size_bytes, n_objects).

    `memo` caches results by object id across calls;
    `_seen` guards cycles within a single traversal.
    """
    if memo is None:
        memo = {}
    if _seen is None:
        _seen = set()

    oid = id(obj)
    if oid in memo:
        return memo[oid]
    if oid in _seen:
        return (0, 0)  # cycle guard

    _seen.add(oid)

    size = _base_size(obj)
    count = 1  # count this object

    # Dict-like
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            s, c = deep_stats(k, memo, _seen)
            size += s
            count += c
            s, c = deep_stats(v, memo, _seen)
            size += s
            count += c

    # Sequence-like (but not str/bytes/bytearray), and Set-like
    elif (isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))) or isinstance(obj, Set):
        for item in obj:
            s, c = deep_stats(item, memo, _seen)
            size += s
            count += c

    # Optionally: handle objects with __dict__ or __slots__
    else:
        # Traverse attributes if present (helps with simple custom classes)
        if hasattr(obj, "__dict__"):
            s, c = deep_stats(vars(obj), memo, _seen)
            size += s
            count += c
        if hasattr(obj, "__slots__"):
            for slot in obj.__slots__ if isinstance(obj.__slots__, (list, tuple)) else [obj.__slots__]: # type: ignore
                try:
                    val = getattr(obj, slot)
                except Exception:
                    continue
                s, c = deep_stats(val, memo, _seen)
                size += s
                count += c

    _seen.remove(oid)
    memo[oid] = (size, count)
    return size, count


def find_large_objects(obj, threshold_kb: float, path="root", memo=None):
    """
    Recursively walk a nested structure, reporting entries whose DEEP size exceeds threshold_kb.
    For each reported entry, include:
      - path (string)
      - type (string)
      - size_kb (float)
      - n_objects (int)  # number of distinct objects counted in its deep size
    """
    if memo is None:
        memo = {}

    results = []

    # Deep stats for the current node (fresh cycle guard but shared memo)
    size_bytes, n_objs = deep_stats(obj, memo=memo, _seen=None)
    size_kb = size_bytes / 1024.0

    if size_kb > threshold_kb:
        results.append({
            "path": path,
            "type": type(obj).__name__,
            "size_kb": round(size_kb, 2),
            "n_objects": int(n_objs),
        })

    # Recurse into children to evaluate them individually
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            child_path = f"{path}[{repr(k)}]"
            results.extend(find_large_objects(v, threshold_kb, child_path, memo))
    elif (isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray))):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            results.extend(find_large_objects(item, threshold_kb, child_path, memo))
    elif isinstance(obj, Set):
        # Sets are unordered; use an index for path clarity
        for i, item in enumerate(obj):
            child_path = f"{path}{{{i}}}"
            results.extend(find_large_objects(item, threshold_kb, child_path, memo))

    return results
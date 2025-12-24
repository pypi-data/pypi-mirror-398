"""
Testing and Debugging Utilities Module

This module provides utilities for generating random test data and debugging output
across various data types including primitives, temporal types, and structured data.
All random generation functions are deterministic when provided with a seed.

Key Features:
- Deterministic random data generation for testing
- Support for all common SQL and Python data types
- UUID, date, datetime, and time generation
- JSON and XML string generation
- Configurable null value percentages
- Type-safe random value generation

Supported Data Types:
- TEXT: Random ASCII sequences
- UUID: Deterministic UUIDs
- TINYINT, SMALLINT, INTEGER, BIGINT: Various integer ranges
- FLOAT: Random floating-point numbers
- DATE, DATETIME, TIME: Temporal types with configurable ranges
- BOOLEAN: Random boolean values
- JSON: Valid JSON strings
- XML: Valid XML strings

Main Functions:
- generate_random_sequence: Generate random sequences with configurable null percentage
- random_ascii_sequence: Generate random ASCII strings
- random_uuid: Generate deterministic UUIDs
- random_int, random_float: Generate numeric values
- random_date, random_datetime, random_time: Generate temporal values
- random_json, random_xml: Generate structured data strings
- debug_print: Print debug output with visual separators

Usage Example:
    ```python
    from src.debugging import generate_random_sequence

    # Generate test data with 10% nulls
    test_ints = generate_random_sequence('INTEGER', n=100, percent_null=0.1, seed=42)
    test_dates = generate_random_sequence('DATE', n=50, seed=42)
    test_text = generate_random_sequence('TEXT', n=20, seed=42)

    # All sequences are deterministic with the same seed
    assert generate_random_sequence('INTEGER', 10, seed=1) == \
           generate_random_sequence('INTEGER', 10, seed=1)
    ```

Author: @Ruppert20
Version: 0.0.1
"""

import random
import uuid
import datetime
import string
import json
from typing import List, Any, Literal, Optional


def random_ascii_sequence(rng: random.Random, length: int = 200) -> str:
    """
    Generate a random ASCII string containing letters, digits, and punctuation.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output
    length : int, optional
        Length of the generated string. Default is 200.

    Returns
    -------
    str
        Random string of specified length with ASCII characters
    """
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(rng.choices(chars, k=length))


def random_uuid(rng: random.Random) -> uuid.UUID:
    """
    Generate a deterministic UUID using the provided random generator.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    uuid.UUID
        Randomly generated UUID
    """
    return uuid.UUID(int=rng.getrandbits(128))


def random_TINYINT(rng: random.Random) -> int:
    """
    Generate a random TINYINT value (0-255).

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    int
        Random integer in TINYINT range [0, 255]
    """
    return rng.randint(0, 255)


def random_SMALLINT(rng: random.Random) -> int:
    """
    Generate a random SMALLINT value (-32768 to 32767).

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    int
        Random integer in SMALLINT range [-32768, 32767]
    """
    return rng.randint(-32768, 32767)

def random_BIGINT(rng: random.Random) -> int:
    # Generate numbers outside the 32-bit INTEGER range (-2^31 to 2^31-1)
    # Choose either a large positive or large negative number
    if rng.choice([True, False]):
        # Generate large positive number (above int32_max)
        return rng.randint(2**31 + 1, 2**62)  # Up to 2^62 for safer range
    else:
        # Generate large negative number (below int32_min)
        return rng.randint(-2**62, -2**31 - 1)  # Down to -2^62 for safer range

def random_int(rng: random.Random) -> int:
    """
    Generate a random 32-bit INTEGER value.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    int
        Random integer in 32-bit signed range [-2^31, 2^31-1]
    """
    return rng.randint(-2**31, 2**31 - 1)


def random_float(rng: random.Random) -> float:
    """
    Generate a random floating-point value.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    float
        Random float in range [-1e6, 1e6]
    """
    return rng.uniform(-1e6, 1e6)

def random_date(
    rng: random.Random,
    start: datetime.date = datetime.date(2000, 1, 1),
    end: datetime.date = datetime.date(2030, 12, 31)
) -> datetime.date:
    days_between = (end - start).days
    return start + datetime.timedelta(days=rng.randint(0, days_between))

def random_datetime(
    rng: random.Random,
    start: datetime.datetime = datetime.datetime(2000, 1, 1),
    end: datetime.datetime = datetime.datetime(2030, 12, 31, 23, 59, 59)
) -> datetime.datetime:
    total_seconds = int((end - start).total_seconds())
    return start + datetime.timedelta(seconds=rng.randint(0, total_seconds))

def random_time(rng: random.Random) -> datetime.time:
    return datetime.time(
        hour=rng.randint(0, 23),
        minute=rng.randint(0, 59),
        second=rng.randint(0, 59),
        microsecond=rng.randint(0, 999999)
    )

def random_bool(rng: random.Random) -> bool:
    """
    Generate a random boolean value.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    bool
        Random boolean (True or False)
    """
    return rng.choice([True, False])


def random_json(rng: random.Random, length: int = 2) -> str:
    """
    Generate a random JSON string with specified number of key-value pairs.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output
    length : int, optional
        Number of key-value pairs in the JSON object. Default is 2.

    Returns
    -------
    str
        Valid JSON string with random keys and values
    """
    data = {
        random_ascii_sequence(rng, 8): random_ascii_sequence(rng, 12)
        for _ in range(length)
    }
    return json.dumps(data)


def random_xml_safe_string(rng: random.Random, length: int = 12) -> str:
    """
    Generate XML-safe string containing only alphanumeric characters and spaces.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output
    length : int, optional
        Length of the generated string. Default is 12.

    Returns
    -------
    str
        Random XML-safe string with leading/trailing whitespace removed
    """
    chars = string.ascii_letters + string.digits + ' '
    return ''.join(rng.choices(chars, k=length)).strip()


def random_xml(rng: random.Random) -> str:
    """
    Generate a simple but valid XML string.

    Creates a basic XML structure with a root element containing a child
    element with an attribute and text content.

    Parameters
    ----------
    rng : random.Random
        Random number generator for deterministic output

    Returns
    -------
    str
        Valid XML string with random element names, attribute, and content
    """
    root_tag = f"root{rng.randint(1, 100)}"
    element_tag = f"element{rng.randint(1, 50)}"
    content = random_xml_safe_string(rng, 20)
    attribute_value = random_xml_safe_string(rng, 8)
    
    return f'<{root_tag}><{element_tag} attr="{attribute_value}">{content}</{element_tag}></{root_tag}>'

def generate_random_sequence(
    dtype: Literal[
        "TEXT", "UUID", "TINYINT", "SMALLINT", "BIGINT", "INTEGER",
        "FLOAT", "DATE", "DATETIME", "TIME", "BOOLEAN",
        "JSON", "XML"
    ],
    n: int,
    percent_null: float = 0.0,
    seed: Optional[int] = None
) -> List[Optional[Any]]:
    """
    Generate a deterministic random sequence of the specified type and length, with given percent nulls.
    :param dtype: The type of value to generate.
    :param n: Number of elements.
    :param percent_null: Percent of elements to be None (0.0–1.0).
    :param seed: Optional INTEGER to set the random seed.
    :return: List of random values (possibly including None).
    """
    rng = random.Random(seed)
    generators = {
        "TEXT": lambda: random_ascii_sequence(rng, 12),
        "UUID": lambda: random_uuid(rng),
        "TINYINT": lambda: random_TINYINT(rng),
        "SMALLINT": lambda: random_SMALLINT(rng),
        "BIGINT": lambda: random_BIGINT(rng),
        "INTEGER": lambda: random_int(rng),
        "FLOAT": lambda: random_float(rng),
        "DATE": lambda: random_date(rng),
        "DATETIME": lambda: random_datetime(rng),
        "TIME": lambda: random_time(rng),
        "BOOLEAN": lambda: random_bool(rng),
        "JSON": lambda: random_json(rng, length=3),
        "XML": lambda: random_xml(rng)
    }
    if dtype not in generators:
        raise ValueError(f"Unsupported dtype: {dtype}")

    null_count = int(n * percent_null)
    not_null_count = n - null_count
    sequence = [generators[dtype]() for _ in range(not_null_count)] + [None] * null_count
    rng.shuffle(sequence)
    return sequence



def debug_print(*args):
    """
    Print debug output with visual separator lines for improved readability.

    Wraps the provided arguments with asterisk separator lines to make
    debug output stand out in console logs.

    Parameters
    ----------
    *args : Any
        Variable number of arguments to print, passed to built-in print()

    Examples
    --------
    >>> debug_print("Debug message", 42, [1, 2, 3])
    **************************************************************************************

    Debug message 42 [1, 2, 3]

    **************************************************************************************
    """
    print('**************************************************************************************\n\n')
    print(*args)
    print('\n\n**************************************************************************************')
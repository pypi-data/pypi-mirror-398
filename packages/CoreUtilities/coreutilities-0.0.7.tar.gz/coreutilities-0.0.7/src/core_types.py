"""
Core Data Type Classification and Detection Module

This module provides a comprehensive enumeration-based system for classifying and
detecting data types across multiple Python data science libraries including pandas,
NumPy, Polars, and PyArrow. It enables unified type handling and conversion across
different data processing frameworks.

Key Features:
- Universal data type classification system
- Cross-library type mapping (pandas, NumPy, Polars, PyArrow)
- String representation detection for typed values
- Comprehensive null value recognition
- Type hierarchy and relationships
- Instance and type checking utilities
- Support for temporal, numeric, container, and special types

Supported Type Categories:
- Numeric: INTEGER, FLOAT, COMPLEX, BOOLEAN, DECIMAL
- Temporal: DATETIME, DATE, TIME, TIMEDELTA
- Text: STRING, BYTES, UUID, XML
- Containers: LIST, TUPLE, SET, DICT, ARRAY
- Data Structures: SERIES, DATAFRAME, INDEX
- Special: NONE_TYPE, OBJECT, CATEGORICAL, ANY

Main Components:
- CoreDataType: Enum containing all type classifications
- Type detection from objects and strings
- String representation parsing (JSON, XML, UUID, dates, etc.)
- Type hierarchy queries (is_numeric, is_temporal, is_container)
- Value introspection and metadata extraction

Usage Example:
    ```python
    from src.core_types import CoreDataType
    import numpy as np

    # Detect type from value
    value = np.array([1, 2, 3])
    core_type = CoreDataType.get_core_type(type(value))
    print(core_type)  # CoreDataType.ARRAY

    # Check type properties
    assert core_type.is_array_like
    assert core_type.is_container

    # Get comprehensive value info
    info = CoreDataType.get_value_info(value)
    print(info['core_type'])  # CoreDataType.ARRAY
    print(info['library'])    # 'numpy'

    # Detect from string representations
    date_str = "2024-01-15"
    core_type = CoreDataType.get_value_info(date_str, parse_string=True)
    print(core_type['core_type'])  # CoreDataType.DATE
    ```

Library Support:
- Python built-ins: list, dict, int, float, str, etc.
- NumPy: arrays, scalars, dtypes
- pandas: Series, DataFrame, Index, extension dtypes
- Polars: Series, DataFrame, LazyFrame (optional)
- PyArrow: Table, arrays, dtypes (optional)

String Detection:
- JSON strings: Valid JSON objects/arrays
- XML strings: Valid XML documents
- UUID strings: Standard UUID format
- Numeric strings: Integer and float representations
- Boolean strings: true/false, yes/no, 1/0, etc.
- Date/datetime strings: ISO format and common patterns
- Null strings: Comprehensive null value patterns

Author: @Ruppert20
Version: 0.0.1
"""

from enum import Enum
from typing import Any, Dict, Type, Literal
import uuid
import datetime
import pandas as pd
import numpy as np
import re
from decimal import Decimal
from pandas._libs.tslibs import NaTType
from collections import OrderedDict

# Add XML types if available
additional_xml_types = set()
try:
    import xml.etree.ElementTree as ET
    additional_xml_types.update({ET.Element, ET.ElementTree})
except ImportError:
    pass

try:
    import lxml.etree as lxml_etree # type: ignore[import]
    additional_xml_types.update({lxml_etree._Element, lxml_etree._ElementTree})
except ImportError:
    pass

# additional specialty types
additional_ints: set = set()
additional_floats: set = set()
additional_bools: set = set()
additional_dates: set = set()
additional_datetimes: set = set()
additional_times: set = set()
additional_timedelta: set = set()
additional_categories: set = set()
additional_lists: set = set()
additional_series: set = set()
additional_dataframes: set = set()
additional_none_types: set = set()
additional_strings: set = set()
additional_bytes: set = set()
additional_decimals: set = set()
additional_dicts: set = set()
try:
    import polars as pl
    HAS_POLARS = True
    additional_ints.update({pl.Int8, pl.Int16, pl.Int32, pl.Int64,
            pl.Int8, pl.Int16, pl.Int32, pl.Int64,
            pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
        })
    additional_floats.update({pl.Float32, pl.Float64})
    additional_bools.update({pl.Boolean})
    additional_strings.update({pl.Utf8, pl.String})
    additional_bytes.update({pl.Binary})
    additional_datetimes.update({pl.Datetime})
    additional_dates.update({pl.Date})
    additional_times.update({pl.Time})
    additional_timedelta.update({pl.Duration})
    additional_categories.update({pl.Categorical})
    additional_lists.update({pl.List})
    additional_series.update({pl.Series})
    additional_dataframes.update({pl.DataFrame, pl.LazyFrame})
    additional_none_types.update({pl.Null})  # Polars null type
    additional_decimals.update({pl.Decimal})
except ImportError:
    HAS_POLARS = False
    pass

try:
    import pyarrow as pa
    HAS_PYARROW = True
    additional_ints.update({pa.int8(), pa.int16(), pa.int32(), pa.int64(),
                             pa.uint8(), pa.uint16(), pa.uint32(), pa.uint64()})
    additional_bools.update({pa.bool_()})
    additional_bytes.update({pa.binary()})
    additional_dicts.update({pa.map_(pa.string(), pa.string())})
    additional_none_types.update({pa.null()})
    additional_floats.update({pa.float16(), pa.float32(), pa.float64()})
    additional_dates.update({pa.date32(), pa.date64()})
    additional_datetimes.update({pa.timestamp('us'), pa.timestamp('ns')})
    additional_times.update({pa.time32('s'), pa.time64('us')})
    additional_timedelta.update({pa.duration('s'), pa.duration('ms'), pa.duration('us'), pa.duration('ns')})
    # XML is not a native PyArrow type, removing it
    # additional_xml_types.update({pa.DataType.XML})
    additional_dataframes.update({pa.Table})
except ImportError:
    HAS_PYARROW = False

class CoreDataType(Enum):
    """
    Enumeration of core data types that exist across different libraries.
    Each enum value represents a fundamental data type concept.
    """
    
    # Numeric types
    INTEGER = ("integer", "Signed and unsigned integer types of various bit widths", {int, np.int8, np.int16, np.int32, np.int64,
                                                                                      np.uint8, np.uint16, np.uint32, np.uint64,
                                                                                      np.integer, np.signedinteger, np.unsignedinteger,
                                                                                      pd.Int8Dtype, pd.Int16Dtype, pd.Int32Dtype, pd.Int64Dtype,
                                                                                      pd.UInt8Dtype, pd.UInt16Dtype, pd.UInt32Dtype, pd.UInt64Dtype}.union(additional_ints),
                           {'int32[pyarrow]', 'uint8[pyarrow]', 'uint32[pyarrow]', 'uint8', 'longtype', 'uint64', 'uint16', 'int64[pyarrow]', 'bool', 'integertype',
                           'int8[pyarrow]', 'int', 'uint64[pyarrow]', 'shorttype', 'bytetype', 'int16', 'int16[pyarrow]', 'int32', 'int64', 'int8', 'uint16[pyarrow]', 'uint32'})
    FLOAT = ("float", "Floating-point numeric types with decimal precision", {float, np.float16, np.float32, np.float64, np.longdouble,
                                                                              np.floating, pd.Float32Dtype, pd.Float64Dtype}.union(additional_floats),
                            {'double[pyarrow]', 'longdouble', 'doubletype', 'float32[pyarrow]', 'float16', 'float', 'float32', 'double', 'float64', 'float[pyarrow]',
                             'floattype', 'float64[pyarrow]'})
    COMPLEX = ("complex", "Complex numbers with real and imaginary components", {complex, np.complex64, np.complex128, np.clongdouble,
            np.complexfloating}, {'complex', 'struct<real: double, imag: double>[pyarrow]', 'complex128', 'struct<real: double, imag: double>', 
                           'structtype(list(structfield(real,doubletype,true),structfield(imag,doubletype,true)))', 'complex64'})
    BOOLEAN = ("boolean", "True/False logical values", {bool, np.bool_, np.dtypes.BoolDType, pd.BooleanDtype}.union(additional_bools),
               {'bool[pyarrow]', 'booleantype', 'boolean', 'bool'})
    DECIMAL = ("decimal", "High-precision decimal numbers with fixed scale", {Decimal}.union(additional_decimals),
               {'decimaltype(38,18)', 'decimal(precision=76, scale=38)', 'decimal128(38, 18)', 'decimaltype(76,38)', 'decimal(precision=38, scale=18)', 'decimal256(76, 38)', 
                'decimal', 'decimal128(38, 18)[pyarrow]', 'decimal256(76, 38)[pyarrow]'})
    NUMERIC = ("numeric", "Any numeric type (integer, float, complex)", {int, float, complex, Decimal}.union(additional_decimals).union(additional_ints).union(additional_floats),
               {'int32[pyarrow]', 'uint8[pyarrow]', 'uint32[pyarrow]', 'uint8', 'longtype', 'uint64', 'uint16', 'int64[pyarrow]', 'bool', 'integertype',
                           'int8[pyarrow]', 'int', 'uint64[pyarrow]', 'shorttype', 'bytetype', 'int16', 'int16[pyarrow]', 'int32', 'int64', 'int8', 'uint16[pyarrow]', 'uint32',
                           'double[pyarrow]', 'longdouble', 'doubletype', 'float32[pyarrow]', 'float16', 'float', 'float32', 'double', 'float64', 'float[pyarrow]',
                        'floattype', 'float64[pyarrow]', 'complex', 'struct<real: double, imag: double>[pyarrow]', 'complex128', 'struct<real: double, imag: double>',
                          'structtype(list(structfield(real,doubletype,true),structfield(imag,doubletype,true)))', 'complex64'})


    # Text and binary types
    STRING = ("string", "Text data and character sequences", {str, np.str_, pd.StringDtype}.union(additional_strings),
              {'string[pyarrow]', 'large_string', 'string', 'str', 'large_string[pyarrow]', 'stringtype', 'str_', 'str_str'})
    BYTES = ("bytes", "Binary data and byte sequences", {bytes, bytearray, np.bytes_, np.void}.union(additional_bytes),
             {'bytes[pyarrow]', 'bytes', 'binary', 'bytes[pyarrow]', 'binary[pyarrow]', 'bytestring'})
    UUID = ("uuid", "Universally unique identifiers", {uuid.UUID},
            {'uuid[pyarrow]', 'uuid', 'extension<arrow.uuid>[pyarrow]', 'extension<arrow.uuid>'})
    XML = ("xml", "XML document data", additional_xml_types, {'xml[pyarrow]', 'xml', 'extension<arrow.xml>[pyarrow]', 'extension<arrow.xml>', 'xml_string', 'xml_str'})
    
    # Temporal types
    DATETIME = ("datetime", "Date and time with timezone support", {datetime.datetime, np.datetime64, pd.Timestamp}.union(additional_datetimes),
                {'timestamp[us]', 'datetime64[ns]', 'datetime64[ns, utc]', 'datetime', 'datetime64[ms]', 'timestamp[ns, tz=utc]', 'timestamp[ns]', 'datetime64[us]',
                             'timestamp[ms, tz=utc]', 'timestamp[us][pyarrow]', 'timestamptype', 'timestamp[ns][pyarrow]', 'datetime64[ns, america/new_york]', 'datetime64[ns, tz]',
                              'timestamp[ns, tz=utc][pyarrow]', 'datetime64', 'timestamp[ms][pyarrow]', 'timestamp[us, tz=utc][pyarrow]', 'timestamp[us, tz=utc]', 'timestamp[ms]',
                                'datetime64[s]', 'timestamp[ms, tz=utc][pyarrow]'})
    DATE = ("date", "Calendar dates without time information", {datetime.date}.union(additional_dates),
            {'date64[pyarrow]', 'date', 'date64[ms][pyarrow]', 'datetime64[d]', 'date32[day][pyarrow]', 'date32[day]', 'date64[ms]', 'date32[pyarrow]', 'date_str'})
    TIME = ("time", "Time of day without date information", {datetime.time}.union(additional_times),
            {'time32[s]', 'time32[s][pyarrow]', 'time64[us]', 'time32[ms][pyarrow]', 'time', 'time32[ms]', 'time64[us][pyarrow]', 'time_str'})
    TIMEDELTA = ("timedelta", "Duration and time differences", {datetime.timedelta, np.timedelta64, pd.Timedelta}.union(additional_timedelta),
                 {'timedelta64[ms]', 'duration[ns][pyarrow]', 'timedelta64[s]', 'duration[us][pyarrow]', 'timedelta64[h]', 'duration[ms]', 'timedelta64',
                                "duration(time_unit='us')", "duration(time_unit='ns')", "duration(time_unit='ms')", 'duration[s]', 'duration[ms][pyarrow]', 'timedelta',
                                  'timedelta64[m]', 'duration[us]', 'timedelta64[d]', 'timedelta64[ns]', 'duration[s][pyarrow]', 'duration[ns]', 'duration', 'timedelta64[us]'})

    # Container types
    LIST = ("list", "Ordered sequences of elements", {list}.union(additional_lists),
            {'list<item: int64>', 'list<item: string>[pyarrow]', 'list(string)',  'list<item: string>',
                       'list', 'large_list<item: int64>[pyarrow]', 'large_list<item: int64>', 'list(int64)', 'large_list<item: string>', 'large_list<item: string>[pyarrow]',
                         'list<item: int64>[pyarrow]'})
    TUPLE = ("tuple", "Immutable ordered sequences", {tuple}, {'tuple'})
    SET = ("set", "Unordered collections of unique elements", {set, frozenset}, {'frozenset', 'set'})
    DICT = ("dict", "Key-value mappings and associative arrays", {dict, OrderedDict}, 
            {'map<string, int64>', 'map<string, string>', 'dict', 'map<string, int64>[pyarrow]', 'ordereddict',
             'maptype(stringtype,integertype,true)', 'maptype(stringtype,stringtype,true)', 'map<string, string>[pyarrow]', 'json', 'json_str'})
    ARRAY = ("array", "Multi-dimensional numeric arrays", {np.ndarray,  pd.arrays.IntegerArray, pd.arrays.BooleanArray, pd.arrays.StringArray, pd.arrays.Categorical},
             {'arraytype(doubletype,true)', 'ndarray', 'array', 'maskedarray', 'numpyextensionarray', 'arraytype(integertype,true)'})
    SERIES = ("series", "One-dimensional labeled arrays", {pd.Series}.union(additional_series), {'column', 'series'})
    DATAFRAME = ("dataframe", "Two-dimensional labeled data structures", {pd.DataFrame}.union(additional_dataframes), {'table', 'dataframe'})
    INDEX = ("index", "One or more-dimensional labeled arrays for indexing", {pd.Index, pd.MultiIndex, pd.RangeIndex}, set())

    # Special types
    NONE_TYPE = ("none", "Null, missing, or undefined values", {type(None), np.nan, pd.NA, pd.NaT, NaTType}.union(additional_none_types),
                 {'<na>', 'generic', 'nat', 'nonetype', 'null', 'nan', 'none',
                  # Standard None representations
            'none', 'null', 'nil', 'nothing', 'empty',
            
            # NaN variations
            'nan', 'n/a', 'na', 'n.a.', 'n.a', '#na', '#n/a',
            
            # Missing/undefined variations  
            'missing', 'undefined', 'undef', 'unknown', 'unkn',
            
            # Database null variations
            'null', 'isnull', 'is null', '<null>', '[null]', '(null)',
            
            # Excel/CSV common missing values
            '#null!', '#n/a!', '#value!', '#ref!', '#name?', '#num!', '#div/0!',
            
            # Programming language variations
            'nullptr', 'void', 'nul', 'nill',
            
            # Empty representations that often mean null
            '', ' ', '  ', '\t', '\n', '\r\n',
            
            # Special characters often used for missing
            '-', '--', '---', '_', '__', '___', '?', '??', '???',
            '.', '..', '...', '/', '//', 'n.d.', 'n.d', 'nd', 'no data',
            
            # Language-specific null representations
            'rien', 'niente', 'nada', 'nichts', 'sem', 'ingen',  # French, Italian, Spanish, German, Portuguese, Norwegian
            
            # Scientific/statistical missing values
            'missing value', 'mv', 'miss', 'not available', 'not applicable',
            'no value', 'no data', 'not specified', 'not defined', 'not set',
            
            # SQL variations
            'is null', 'isnull()', 'null()',
            
            # JSON null variations
            'null', 'undefined',
            
            # Additional common variations
            'blank', 'void', 'absent', 'omitted', 'skipped', 'bypass'})
    OBJECT = ("object", "Generic object references and mixed types", {object, np.object_}, {'object', 'object_'})
    CATEGORICAL = ("categorical", "Enumerated values with limited categories", {pd.CategoricalDtype, Enum}, {'categorical', 'category', 'enum'})
    ANY = ("any", "Unknown or dynamically typed values", {Any}, {'any'})
    UNKNOWN = ("unknown", "Unknown or unrecognized types", set(), set())
    
    def __init__(self, name: str, description: str, type_mapping: set, str_type_aliases: set):
        self.type_name = name
        self.description = description
        self.type_mapping = type_mapping
        self.str_type_aliases = str_type_aliases

    def __str__(self) -> str:
        return self.type_name
    
    def __repr__(self) -> str:
        return f"self.{self.name}"
    
    def __lt__(self, other):
        """Less than comparison based on enum value."""
        if isinstance(other, CoreDataType):
            return self.value[0] < other.value[0]
        return NotImplemented
    
    def __le__(self, other):
        """Less than or equal comparison based on enum value."""
        if isinstance(other, CoreDataType):
            return self.value[0] <= other.value[0]
        return NotImplemented
    
    def __gt__(self, other):
        """Greater than comparison based on enum value."""
        if isinstance(other, CoreDataType):
            return self.value[0] > other.value[0]
        return NotImplemented
    
    def __ge__(self, other):
        """Greater than or equal comparison based on enum value."""
        if isinstance(other, CoreDataType):
            return self.value[0] >= other.value[0]
        return NotImplemented
    
    @staticmethod
    def get_core_type(type_obj: Type | str) -> 'CoreDataType':
        """Get the core data type for a given type object."""
        for member in CoreDataType:
            if isinstance(type_obj, type):
                # Check if the type is directly in the type_mapping set
                if type_obj in member.type_mapping:
                    return member
            elif isinstance(type_obj, str):
                normalized: str = type_obj.strip().lower()
                if normalized in member.str_type_aliases:
                    return member
            else:
                term_lower = CoreDataType.get_name(type_obj).lower()
                for member in CoreDataType:
                    if term_lower in (alias.lower() for alias in member.str_type_aliases):
                        return member

        return CoreDataType.UNKNOWN
    
    @property
    def is_numeric(self) -> bool:
        return self in {self.INTEGER, self.FLOAT, self.COMPLEX, self.DECIMAL, self.NUMERIC}

    @staticmethod
    def is_numeric_type(type_obj: Type) -> bool:
        """Check if a type is numeric."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type.is_numeric

    @property
    def is_temporal(self) -> bool:
        return self in {self.DATETIME, self.DATE, self.TIME, self.TIMEDELTA}

    @staticmethod
    def is_temporal_type(type_obj: Type) -> bool:
        """Check if a type is temporal."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type.is_temporal

    @property
    def is_container(self) -> bool:
        return self in {self.LIST, self.TUPLE, self.SET, self.DICT, self.ARRAY, self.SERIES, self.DATAFRAME}

    @staticmethod
    def is_container_type(type_obj: Type) -> bool:
        """Check if a type is a container."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type.is_container

    @property
    def is_array_like(self) -> bool:
        return self in {self.ARRAY, self.SERIES}

    @staticmethod
    def is_array_like_type(type_obj: Type) -> bool:
        """Check if a type is array-like (array, series)."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type.is_array_like

    @staticmethod
    def is_dataframe_type(type_obj: Type) -> bool:
        """Check if a type is a dataframe."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type == CoreDataType.DATAFRAME
    
    @property
    def is_data_structure(self) -> bool:
        return self in {self.ARRAY, self.SERIES, self.DATAFRAME}

    @staticmethod
    def is_data_structure_type(type_obj: Type) -> bool:
        """Check if a type is a data science data structure (array, series, dataframe)."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type.is_data_structure

    @staticmethod
    def is_any_type(type_obj: Type) -> bool:
        """Check if a type is the Any type."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type == CoreDataType.ANY

    @staticmethod
    def is_special_type(type_obj: Type) -> bool:
        """Check if a type is a special type (None, object, Any, categorical)."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type in {CoreDataType.NONE_TYPE, CoreDataType.OBJECT, CoreDataType.ANY, CoreDataType.CATEGORICAL}

    @staticmethod
    def is_uuid_type(type_obj: Type) -> bool:
        """Check if a type is a UUID type."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type == CoreDataType.UUID

    @staticmethod
    def is_xml_type(type_obj: Type) -> bool:
        """Check if a type is an XML type."""
        core_type = CoreDataType.get_core_type(type_obj)
        return core_type == CoreDataType.XML

    @staticmethod
    def __get_type(value: Any) -> Type:
        if isinstance(value, Type):
            return value
        else:
            return type(value)

    @staticmethod
    def is_numeric_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is a numeric instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of numbers
        """
        if CoreDataType.is_numeric_type(CoreDataType.__get_type(value)):
            return True
        
        # Check string representations
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_integer_string(value) or CoreDataType._is_float_string(value)
        
        return False

    @staticmethod
    def is_temporal_instance(value: Any) -> bool:
        """Check if a value is a temporal instance."""
        if CoreDataType.is_temporal_type(CoreDataType.__get_type(value)):
            return True

        return CoreDataType._is_date_string(value) or CoreDataType._is_datetime_string(value) or \
               CoreDataType._is_time_string(value)

    @staticmethod
    def is_container_instance(value: Any) -> bool:
        """Check if a value is a container instance."""
        return CoreDataType.is_container_type(CoreDataType.__get_type(value))

    @staticmethod
    def is_array_like_instance(value: Any) -> bool:
        """Check if a value is an array-like instance (array, series)."""
        return CoreDataType.is_array_like_type(CoreDataType.__get_type(value))

    @staticmethod
    def is_dataframe_instance(value: Any) -> bool:
        """Check if a value is a dataframe instance."""
        return CoreDataType.is_dataframe_type(CoreDataType.__get_type(value))

    @staticmethod
    def is_data_structure_instance(value: Any) -> bool:
        """Check if a value is a data science data structure instance (array, series, dataframe)."""
        return CoreDataType.is_data_structure_type(CoreDataType.__get_type(value))

    @staticmethod
    def is_uuid_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is a UUID instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of UUIDs
        """
        if CoreDataType.is_uuid_type(CoreDataType.__get_type(value)):
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_uuid_string(value)

        return False

    @staticmethod
    def is_integer_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is an integer instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of integers
        """
        if CoreDataType.get_core_type(CoreDataType.__get_type(value)) == CoreDataType.INTEGER:
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_integer_string(value)

        return False

    @staticmethod
    def is_float_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is a float instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of floats
        """
        if CoreDataType.get_core_type(CoreDataType.__get_type(value)) == CoreDataType.FLOAT:
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_float_string(value)

        return False

    @staticmethod
    def is_boolean_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is a boolean instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of booleans
        """
        if CoreDataType.get_core_type(CoreDataType.__get_type(value)) == CoreDataType.BOOLEAN:
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_boolean_string(value)

        return False

    @staticmethod
    def is_json_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is a JSON instance (dict, list, or JSON string).
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of JSON
        """
        # JSON is represented as dict or list in Python
        if isinstance(value, dict):
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_json_string(value)
        
        return False

    @staticmethod
    def is_xml_instance(value: Any, include_string_repr: bool = True) -> bool:
        """
        Check if a value is an XML instance.
        
        Args:
            value: The value to check
            include_string_repr: Whether to include string representations of XML
        """
        if CoreDataType.get_core_type(CoreDataType.__get_type(value)) == CoreDataType.XML:
            return True
        
        if include_string_repr and isinstance(value, str):
            return CoreDataType._is_xml_string(value)

        return False


    @staticmethod
    def get_value_info(value: Any, parse_string: bool = True, return_type: Literal['type_only', 'full', 'abbreviated'] = 'full') -> Dict[str, Any] | 'CoreDataType':
        """
        Get comprehensive information about a value's type classification.
        
        Args:
            value: The object/value to analyze
            parse_string: Whether to parse string representations of JSON, XML, UUID, INT, FLOAT, BOOLEAN
            core_type_string_rep_only: If True, return only the core type and whether it's a string representation
            
        Returns:
            Dict containing detailed type information about the value
            
        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'a': [1, 2, 3]})
            >>> info = registry.get_value_info(df)
            >>> print(info['core_type'])
            self.DATAFRAME
        """
        value_type = type(value)
        raw_core_type = CoreDataType.get_core_type(value_type)
        
        if parse_string and isinstance(value, str):
            # Check for string representations of JSON, XML, UUID, INT, FLOAT, BOOLEAN
            core_type, is_string_repr = CoreDataType._detect_string_representation(value)
        else:
            core_type, is_string_repr = raw_core_type, False

        is_actually_int = CoreDataType._is_float_actually_integer(value) if core_type in [CoreDataType.FLOAT, CoreDataType.BOOLEAN] else False
        if is_actually_int:
            core_type = CoreDataType.INTEGER

        if return_type == 'type_only':
            return core_type

        elif return_type == 'abbreviated':
            return {'value_type': value_type, 'raw_core_type': raw_core_type, 'core_type': core_type, 'is_string_repr': is_string_repr}
        
        return {
            "value": value,
            "value_type": value_type,
            "type_name": value_type.__name__,
            "module": value_type.__module__,
            "raw_core_type": raw_core_type,
            "core_type": core_type,
            "string_representation": is_string_repr,
            "is_numeric": CoreDataType.is_numeric_instance(value),
            "is_integer": core_type == CoreDataType.INTEGER,
            "is_float": core_type == CoreDataType.FLOAT,
            "is_boolean": core_type == CoreDataType.BOOLEAN,
            "is_temporal": CoreDataType.is_temporal_instance(value),
            "is_container": CoreDataType.is_container_instance(value),
            "is_array_like": CoreDataType.is_array_like_instance(value),
            "is_dataframe": CoreDataType.is_dataframe_instance(value),
            "is_data_structure": CoreDataType.is_data_structure_instance(value),
            "is_uuid": core_type == CoreDataType.UUID,
            "is_json": CoreDataType.is_json_instance(value),
            "is_xml": core_type == CoreDataType.XML,
            "library": CoreDataType._get_library_from_type(value_type),
        }
    
    @staticmethod
    def _get_library_from_type(type_obj: Type) -> str:
        """Get the library name from a type object."""
        module = type_obj.__module__
        
        if bool(re.search(r'^pandas', module)):
            return 'pandas'
        elif bool(re.search(r'^polars', module)):
            return 'polars'
        elif bool(re.search(r'^numpy', module)):
            return 'numpy'
        elif bool(re.search(r'^dask', module)):
            return 'dask'
        elif bool(re.search(r'^pyspark', module)):
            return 'pyspark'
        elif 'universal' in module.lower() or type_obj.__name__.startswith('Universal'):
            return 'universal'
        elif module == 'builtins':
            return 'python'
        elif 'array' in module:
            return 'array'
        else:
            return module.split('.')[0]

    @staticmethod
    def _is_json_string(value: str) -> bool:
        """Check if a string represents valid JSON."""
        try:
            import json
            json.loads(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_xml_string(value: str) -> bool:
        """Check if a string represents valid XML."""
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_uuid_string(value: str) -> bool:
        """Check if a string represents a valid UUID."""
        try:
            from uuid import UUID
            UUID(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_integer_string(value: str) -> bool:
        """Check if a string represents a valid integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_float_string(value: str) -> bool:
        """Check if a string represents a valid float."""
        try:
            float(value)
            # Make sure it's not an integer (we want to classify integers separately)
            return '.' in value or 'e' in value.lower() or 'inf' in value.lower() or 'nan' in value.lower()
        except ValueError:
            return False
    
    @staticmethod
    def _is_boolean_string(value: str) -> bool:
        """Check if a string represents a boolean value."""
        value_lower = value.lower().strip()
        # Standard boolean strings
        if value_lower in ('true', 'false', 'yes', 'no', 'on', 'off', '1', '0', '1.0', '0.0', '1.00', '0.00', 'y', 'n'):
            return True

        return False

    @staticmethod
    def _is_float_actually_integer(value: Any) -> bool:
        """Check if a float value is actually an integer (no fractional part)."""
        if isinstance(value, float):
            # Check if the float has no fractional part
            return value.is_integer()
        elif isinstance(value, (int, bool)):
            # Integers and booleans are definitely integers
            return True
        elif isinstance(value, str):
            try:
                float_val = float(value)
                return float_val.is_integer()
            except ValueError:
                return False
        else:
            # Try to convert other numeric types
            try:
                # Handle numpy types and other numeric types
                if hasattr(value, 'is_integer'):
                    return value.is_integer()
                elif hasattr(value, '__float__'):
                    float_val = float(value)
                    return float_val.is_integer()
                else:
                    return False
            except (ValueError, TypeError, AttributeError):
                return False

    @staticmethod
    def _detect_string_representation(value: Any) -> tuple['CoreDataType', bool]:
        """
        Detect if a value is a string representation of JSON, XML, UUID, or numeric types.
        
        Returns:
            tuple: (CoreDataType, is_string_representation)
        """
        if not isinstance(value, str):
            return CoreDataType.get_core_type(type(value)), False
        
        # Check for None/null string representations first
        if CoreDataType._is_None_string(value):
            return CoreDataType.NONE_TYPE, True
        
        # Check for boolean strings first (before numeric checks)
        if CoreDataType._is_boolean_string(value):
            return CoreDataType.BOOLEAN, True
        
        # Check for integer strings
        if CoreDataType._is_integer_string(value):
            return CoreDataType.INTEGER, True
        
        # Check for float strings
        if CoreDataType._is_float_string(value):
            return CoreDataType.FLOAT, True

        if CoreDataType._is_date_string(value):
            return CoreDataType.DATE, True

        if CoreDataType._is_datetime_string(value):
            return CoreDataType.DATETIME, True
        
        if CoreDataType._is_time_string(value):
            return CoreDataType.TIME, True

        # Check for XML string
        if CoreDataType._is_xml_string(value):
            return CoreDataType.XML, True

        # Check for JSON string
        if CoreDataType._is_json_string(value):
            return CoreDataType.DICT, True

        # Check for UUID string
        if CoreDataType._is_uuid_string(value):
            return CoreDataType.UUID, True
        
        # If none match, return the normal string type
        return CoreDataType.STRING, False

    @staticmethod
    def _is_None_string(value: Any) -> bool:
        """
        Check if a value is a None string representation.

        Args:
            value: The value to check

        Returns:
            bool: True if the value represents None, False otherwise
        """
        if value is None:
            return True
        if not isinstance(value, str):
            return False

        # Normalize the value for comparison
        return value.strip().lower() in CoreDataType.NONE_TYPE.str_type_aliases

    @staticmethod
    def _is_time_string(value: Any) -> bool:
        """
        Check if a value is a time string representation.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value represents a time, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        import re
        # Common time patterns: HH:MM:SS, HH:MM, HH:MM:SS.fff
        time_patterns = [
            r'^\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?$',  # HH:MM or HH:MM:SS or HH:MM:SS.ffffff
            r'^\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM)$',    # 12-hour format with AM/PM
        ]
        
        return any(re.match(pattern, value.strip(), re.IGNORECASE) for pattern in time_patterns)

    @staticmethod
    def _is_date_string(value: Any) -> bool:
        """
        Check if a value is a date string representation.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value represents a date, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        import re
        # Common date patterns: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.
        date_patterns = [
            r'^\d{4}-\d{1,2}-\d{1,2}$',              # YYYY-MM-DD
            r'^\d{1,2}/\d{1,2}/\d{4}$',              # MM/DD/YYYY or DD/MM/YYYY
            r'^\d{1,2}-\d{1,2}-\d{4}$',              # MM-DD-YYYY or DD-MM-YYYY
            r'^\d{4}/\d{1,2}/\d{1,2}$',              # YYYY/MM/DD
            r'^\d{1,2}\.\d{1,2}\.\d{4}$',            # DD.MM.YYYY
            r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}$',  # Month DD, YYYY
        ]
        
        return any(re.match(pattern, value.strip()) for pattern in date_patterns)

    @staticmethod
    def _is_datetime_string(value: Any) -> bool:
        """
        Check if a value is a datetime string representation.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value represents a datetime, False otherwise
        """
        if not isinstance(value, str):
            return False
        
        import re
        # Common datetime patterns combining date and time
        datetime_patterns = [
            r'^\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?$',           # YYYY-MM-DD HH:MM:SS
            r'^\d{4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{2}(:\d{2})?(\.\d{1,6})?(Z|[+-]\d{2}:\d{2})?$',  # ISO format
            r'^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}(:\d{2})?(\s*(AM|PM))?$',          # MM/DD/YYYY HH:MM:SS
            r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}(:\d{2})?$',           # Month DD, YYYY HH:MM:SS
        ]
        
        return any(re.match(pattern, value.strip(), re.IGNORECASE) for pattern in datetime_patterns)
    
    @staticmethod
    def get_name(obj: Any) -> str:
        return str(obj.__name__ if hasattr(obj, '__name__') else obj.name if hasattr(obj, 'name') else str(obj))
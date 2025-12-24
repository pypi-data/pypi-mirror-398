"""
Extended Serialization Module (XSer)

This module provides destination-aware serialization with a resilient fallback chain
for Python objects. It supports multiple serialization formats including JSON, YAML,
CBOR, and Pickle, with intelligent fallback strategies for complex or unpickleable objects.

Key Features:
- Multi-format serialization (JSON, YAML, HDF5, Parquet, Pickle)
- Structured JSON/YAML-safe intermediate representation
- Automatic fallback chain: Structured -> CBOR -> Pickle
- NumPy array and scalar support with special float handling
- Generic class serialization via to_dict/from_dict patterns
- Cycle detection and handling
- Base64 encoding for binary-safe storage
- Optional class import allow-lists for security

Supported Destinations:
- JSON strings (json.dumps/json.loads)
- YAML strings (yaml.safe_dump/safe_load)
- HDF5 attributes (single bytes blob with magic header)
- Parquet/PyArrow metadata (bytes with base64 encoding)
- File I/O (read/write JSON, YAML, Pickle)

Supported Data Types:
- Primitives: None, bool, int, float, str, bytes, complex, Decimal
- Temporal: datetime, date, time, timedelta, timezone
- Collections: list, dict, tuple, set, frozenset
- NumPy: arrays (non-object dtype), scalars (including special floats)
- Special: UUID, pathlib.Path
- Generic: Any class with to_dict/from_dict or to_list/from_list methods

Fallback Strategy:
1. Structured encoding (JSON/YAML compatible with type tags)
2. CBOR blob (if structured fails and cbor2 available)
3. Pickle blob (protocol 5, if all else fails)

Usage Example:
    ```python
    from src.serialization import XSer
    import numpy as np

    # Serialize to JSON
    data = {'array': np.array([1, 2, 3]), 'value': 42}
    json_str = XSer.dump_json(data)
    restored = XSer.load_json(json_str)

    # Serialize to HDF5 attribute
    h5_bytes = XSer.to_hdf5_attr(data)
    restored = XSer.from_hdf5_attr(h5_bytes)

    # Safe file operations
    XSer.write_json('data.json', data, indent=2)
    loaded = XSer.read_json('data.json')

    # Set class import restrictions
    XSer.set_class_allowlist({'myapp.', 'trusted.module.'})
    ```

Security Considerations:
- Use CLASS_ALLOWLIST to restrict which classes can be imported during deserialization
- Pickle fallback can execute arbitrary code - validate data sources
- Dynamic imports pose security risks with untrusted data

Author: @Ruppert20
Version: 0.0.1
"""

from __future__ import annotations

import base64
import importlib
import json
import math
import yaml
import pickle
import sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Mapping, Union, Literal, cast, Optional
import numpy as np
from pathlib import Path
import os

# Support both package-relative and direct imports
try:
    from .iterables import deep_stats
except ImportError:
    from iterables import deep_stats

try:
    import cbor2
except Exception:  # pragma: no cover
    cbor2 = None  # type: ignore



__all__ = ["XSer", "XSER_MAGIC", "XSER_TAG", "XSER_VER"]

# -----------------------------
# Public constants & helpers
# -----------------------------
XSER_MAGIC = b"XSER\x01"  # header for HDF5 attrs & Parquet metadata bytes
XSER_TAG = "__xser__"     # marks a tagged structure in the intermediate form
XSER_VER = 1              # schema version


def _b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _is_b64_bytes(b: bytes) -> bool:
    try:
        base64.b64decode(b, validate=True)
        return True
    except Exception:
        return False


def _b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _class_path_of(obj: Any) -> str:
    cls = obj.__class__
    return f"{cls.__module__}:{cls.__qualname__}"


def _import_class(path: str):
    """Import a class by '<module>:<qualname>' path."""
    mod_name, _, qual = path.partition(":")
    if not mod_name or not qual:
        raise ValueError(f"Invalid class path: {path!r}")
    mod = importlib.import_module(mod_name)
    attr = mod
    for part in qual.split("."):
        attr = getattr(attr, part)
    return attr


# -----------------------------
# Internal exceptions & CBOR helpers
# -----------------------------
class _XSerCycleDetected(RuntimeError):
    """Raised internally when a cycle is detected during structured encoding."""
    pass


class _XSerCBORFailed(RuntimeError):
    """Raised internally when CBOR encoding is requested but fails (or lib missing)."""
    pass


def _try_cbor_dumps(obj) -> bytes | None:
    """Attempt CBOR dumps; return None if lib missing or encoding fails."""
    if cbor2 is None:
        return None
    try:
        return cbor2.dumps(obj)
    except Exception:
        return None


def _must_cbor_loads(b: bytes):
    """CBOR loads with explicit, distinct errors for 'missing' vs 'decode failed'."""
    if cbor2 is None:
        raise RuntimeError(
            "CBOR payload found but 'cbor2' is not installed. Install 'cbor2' to decode."
        )
    try:
        return cbor2.loads(b)
    except Exception as e:
        raise ValueError(f"CBOR decode failed: {e.__class__.__name__}: {e}") from e


# -----------------------------
# Core encoder/decoder
# -----------------------------
class XSer:
    """
    Destination-aware serialization with a resilient fallback chain:
      1) Structured, JSON/YAML-safe intermediate (tagged)
      2) CBOR blob (if structured fails)
      3) Pickle blob (protocol 5)

    Destinations:
      - JSON (json.dumps/json.loads)
      - YAML safe (yaml.safe_dump/safe_load)
      - HDF5 attributes (single bytes blob with XSER magic header)
      - Parquet/pyarrow metadata KV (bytes; same blob format)

    Numpy:
      - Non-object ndarrays encoded as dtype/shape/order + base64 payload
      - Object-dtype ndarrays -> fallback to CBOR or Pickle blob
      - Numpy scalars supported (including special floats)

    Generic classes:
      - If object has to_dict()/from_dict() or to_list()/from_list() (or tolist()/fromlist()),
        encode as a tagged 'generic' with fully qualified class path.
      - On decode, call from_* if present; else try cls(decoded_payload).

    Cycles:
      - Cycle detection during structured encoding -> immediate Pickle blob.

    Security:
      - Optional import allow-list for decoding generic classes.
    """

    # --------- Optional safety: restrict which classes may be imported on decode ---------
    # If None: allow all. Otherwise a set of module-prefix strings (e.g., {"myapp.", "pkg.subpkg."}).
    CLASS_ALLOWLIST: set[str] | None = None

    @classmethod
    def set_class_allowlist(cls, prefixes: set[str] | None) -> None:
        cls.CLASS_ALLOWLIST = prefixes

    # ---------- High-level public API ----------

    @classmethod
    def dump_json(cls, obj: Any, *, ensure_ascii: bool = False, indent: int | None = None, **kwargs) -> str:
        """Serialize to a JSON string (strict; no bare NaN/Inf)."""
        inter = cls._to_intermediate(obj)
        return json.dumps(inter, ensure_ascii=ensure_ascii, indent=indent, allow_nan=False, **kwargs)

    @classmethod
    def load_json(cls, s: str, **kwargs) -> Any:
        inter = json.loads(s, **kwargs)
        return cls._from_intermediate(inter)

    @classmethod
    def dump_yaml(cls, obj: Any, **kwargs) -> str:
        """Serialize to YAML using yaml.safe_dump."""
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Install 'pyyaml' to use dump_yaml/load_yaml.")
        inter = cls._to_intermediate(obj)
        return yaml.safe_dump(inter, sort_keys=False, **kwargs)

    @classmethod
    def load_yaml(cls, s: str, **kwargs) -> Any:
        """Deserialize from YAML using yaml.safe_load."""
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Install 'pyyaml' to use dump_yaml/load_yaml.")
        inter = yaml.safe_load(s, **kwargs)
        return cls._from_intermediate(inter)

    @classmethod
    def to_hdf5_attr(cls, obj: Any) -> bytes:
        """
        Produce a single bytes payload appropriate for h5py attributes.
        Binary format:
            XSER_MAGIC + b'C' + cbor(intermediate)
            or
            XSER_MAGIC + b'P' + pickle(intermediate)
        """
        inter = cls._to_intermediate(obj)
        data = _try_cbor_dumps(inter)
        if data is not None:
            return XSER_MAGIC + b"C" + data
        payload = pickle.dumps(inter, protocol=5)
        return XSER_MAGIC + b"P" + payload

    @classmethod
    def from_hdf5_attr(cls, b: bytes | memoryview | bytearray) -> Any:
        bb = bytes(b)
        if not (len(bb) >= len(XSER_MAGIC) + 1 and bb[:len(XSER_MAGIC)] == XSER_MAGIC):
            raise ValueError("Bad XSER payload: missing/invalid magic header")
        fmt = chr(bb[len(XSER_MAGIC)])
        content = bb[len(XSER_MAGIC) + 1:]
        if fmt == "C":
            inter = _must_cbor_loads(content)
        elif fmt == "P":
            inter = pickle.loads(content)
        else:
            raise ValueError(f"Unknown XSER payload format code: {fmt!r}")
        return cls._from_intermediate(inter)

    @classmethod
    def to_parquet_kv(cls, obj: Any, *, key: str | bytes | None = None) -> Dict[bytes, bytes] | bytes:
        """
        Return {key: value} where value is **base64-UTF8 bytes** of the XSER blob.
        This keeps Parquet metadata values valid UTF-8 for tooling that requires it.
        """
        if isinstance(obj, dict):
            return {(k.encode("utf-8") if isinstance(k, str) else k): base64.b64encode(cls.to_hdf5_attr(v)).decode("ascii").encode() for k, v in obj.items()}
        raw = cls.to_hdf5_attr(obj)                              # XSER binary
        b64 = base64.b64encode(raw).decode("ascii").encode()     # UTF-8 bytes
        k = key.encode("utf-8") if isinstance(key, str) else key
        return b64 if k is None else {cast(bytes, k): b64}


    @classmethod
    def from_parquet_kv(cls, val: bytes | memoryview | bytearray) -> Any:
        """
        Accepts either raw XSER bytes (legacy) or base64-UTF8 bytes of the XSER blob.
        """
        vb = bytes(val)

        # Prefer base64 path (most writers will store UTF-8 values)
        if _is_b64_bytes(vb):
            try:
                raw = base64.b64decode(vb, validate=True)
                if raw.startswith(XSER_MAGIC):
                    return cls.from_hdf5_attr(raw)
            except Exception:
                pass

        # Fallback: legacy raw XSER blob
        if vb.startswith(XSER_MAGIC):
            return cls.from_hdf5_attr(vb)

        raise ValueError("Parquet KV value is neither base64-encoded XSER nor raw XSER bytes")


    @classmethod
    def from_dict(
        cls,
        attrs_or_metadata: Mapping[Union[str, bytes], Any],
        *,
        decode_keys: bool = True,
        strict: bool = False,
    ) -> Dict[Union[str, bytes], Any]:
        out: Dict[Union[str, bytes], Any] = {}

        def _maybe_decode_value(v: Any) -> Any:
            # bytes-like value?
            if isinstance(v, (bytes, bytearray, memoryview)):
                bb = bytes(v)

                # 1) raw XSER blob
                if len(bb) >= len(XSER_MAGIC) + 1 and bb.startswith(XSER_MAGIC):
                    try:
                        return cls.from_hdf5_attr(bb)
                    except Exception:
                        if strict:
                            raise
                        return v

                # 2) base64 -> XSER blob
                if _is_b64_bytes(bb):
                    try:
                        raw = base64.b64decode(bb, validate=True)
                        if raw.startswith(XSER_MAGIC):
                            return cls.from_hdf5_attr(raw)
                    except Exception:
                        if strict:
                            raise

                # 3) UTF-8 -> JSON -> XSer intermediate
                try:
                    s = bb.decode("utf-8")
                except Exception:
                    return v if not strict else (_ for _ in ()).throw(ValueError("Non-UTF8 bytes and not XSER blob"))
                try:
                    j = json.loads(s)
                    try:
                        return cls._from_intermediate(j)
                    except Exception:
                        return j  # plain JSON not produced by XSer
                except Exception:
                    return s  # plain UTF-8 text

            # string value?
            if isinstance(v, str):
                # 1) base64 -> XSER blob
                try:
                    raw = base64.b64decode(v.encode("ascii"), validate=True)
                    if raw.startswith(XSER_MAGIC):
                        return cls.from_hdf5_attr(raw)
                except Exception:
                    pass

                # 2) JSON -> XSer intermediate
                try:
                    j = json.loads(v)
                    try:
                        return cls._from_intermediate(j)
                    except Exception:
                        return j
                except Exception:
                    return v

            # already a tagged intermediate dict?
            if isinstance(v, dict) and XSER_TAG in v:
                try:
                    return cls._from_intermediate(v)
                except Exception:
                    if strict:
                        raise
                    return v

            return v

        for k, v in attrs_or_metadata.items():
            new_k: Union[str, bytes] = k
            if isinstance(k, (bytes, bytearray)) and decode_keys:
                try:
                    new_k = bytes(k).decode("utf-8")
                except Exception:
                    new_k = bytes(k)  # keep as bytes if not decodable
            out[new_k] = _maybe_decode_value(v)

        return out

    # ---------- Intermediate representation ----------

    @classmethod
    def _to_intermediate(cls, obj: Any) -> Any:
        memo: set[int] = set()
        try:
            return cls._enc(obj, memo)
        except _XSerCycleDetected:
            return cls._blob(obj, enc="pickle", memo=memo)
        except Exception:
            try:
                return cls._blob(obj, enc="cbor", memo=memo)
            except _XSerCBORFailed:
                return cls._blob(obj, enc="pickle", memo=memo)

    @classmethod
    def _from_intermediate(cls, node: Any) -> Any:
        return cls._dec(node)

    # ---------- Encoding helpers ----------

    @classmethod
    def _enc(cls, obj: Any, memo: set[int]) -> Any:
        oid = id(obj)

        # Primitives
        if obj is None or isinstance(obj, (bool, int, str)):
            return obj

        if isinstance(obj, float):
            if math.isfinite(obj):
                return obj
            return {XSER_TAG: XSER_VER, "t": "float",
                    "v": ("nan" if math.isnan(obj) else ("inf" if obj > 0 else "-inf"))}

        # bytes-like
        if isinstance(obj, (bytes, bytearray, memoryview)):
            return {XSER_TAG: XSER_VER, "t": "bytes", "b64": _b64e(bytes(obj))}

        # complex, Decimal
        if isinstance(obj, complex):
            return {XSER_TAG: XSER_VER, "t": "complex", "v": [obj.real, obj.imag]}
        if isinstance(obj, Decimal):
            return {XSER_TAG: XSER_VER, "t": "decimal", "v": str(obj)}

        # datetime family
        if isinstance(obj, datetime):
            return {XSER_TAG: XSER_VER, "t": "datetime", "v": obj.isoformat()}
        if isinstance(obj, date):
            return {XSER_TAG: XSER_VER, "t": "date", "v": obj.isoformat()}
        if isinstance(obj, time):
            return {XSER_TAG: XSER_VER, "t": "time", "v": obj.isoformat()}
        if isinstance(obj, timedelta):
            us = int(round(obj.total_seconds() * 1_000_000))
            return {XSER_TAG: XSER_VER, "t": "timedelta_us", "v": us}
        if isinstance(obj, timezone):
            # compute fixed offset seconds robustly
            seconds = int(obj.utcoffset(datetime(1970, 1, 1, tzinfo=obj)).total_seconds())  # type: ignore[arg-type]
            return {XSER_TAG: XSER_VER, "t": "timezone", "v": seconds}

        # uuid, pathlib.Path
        try:
            import uuid
            if isinstance(obj, uuid.UUID):
                return {XSER_TAG: XSER_VER, "t": "uuid", "v": str(obj)}
        except Exception:
            pass
        try:
            from pathlib import Path
            if isinstance(obj, Path):
                return {XSER_TAG: XSER_VER, "t": "path", "v": str(obj)}
        except Exception:
            pass

        # numpy scalars/arrays
        if np is not None:
            if isinstance(obj, np.generic):
                dt = obj.dtype.str
                if obj.dtype.kind in ("i", "u"):
                    return {XSER_TAG: XSER_VER, "t": "np_scalar", "dtype": dt, "v": int(obj)}
                if obj.dtype.kind == "b":
                    return {XSER_TAG: XSER_VER, "t": "np_scalar", "dtype": dt, "v": bool(obj)}
                if obj.dtype.kind == "f":
                    fv = float(obj)
                    if math.isfinite(fv):
                        return {XSER_TAG: XSER_VER, "t": "np_scalar", "dtype": dt, "v": fv}
                    return {XSER_TAG: XSER_VER, "t": "np_scalar", "dtype": dt,
                            "v": ("nan" if math.isnan(fv) else ("inf" if fv > 0 else "-inf"))}
                return {XSER_TAG: XSER_VER, "t": "np_scalar_bytes", "dtype": dt, "b64": _b64e(bytes(obj))}
            if isinstance(obj, np.ndarray):
                if obj.dtype.kind == "O":
                    raise ValueError("object-dtype ndarray -> fallback")
                memo.add(oid)
                try:
                    arr = obj
                    order = "F" if arr.flags.f_contiguous and not arr.flags.c_contiguous else "C"
                    raw = arr.tobytes(order=order)
                    return {
                        XSER_TAG: XSER_VER,
                        "t": "ndarray",
                        "dtype": (arr.dtype.descr if arr.dtype.fields else arr.dtype.str),
                        "shape": list(arr.shape),
                        "order": order,
                        "b64": _b64e(raw),
                    }
                finally:
                    memo.discard(oid)

        # handle large objects that would require recursion
        if (deep_stats(obj=obj)[0] > 20000):
            raise _XSerCycleDetected

        # tuples/sets/frozensets
        if isinstance(obj, tuple):
            memo.add(oid)
            try:
                return {XSER_TAG: XSER_VER, "t": "tuple", "v": [cls._enc(x, memo) for x in obj]}
            finally:
                memo.discard(oid)
        if isinstance(obj, set):
            memo.add(oid)
            try:
                return {XSER_TAG: XSER_VER, "t": "set", "v": [cls._enc(x, memo) for x in obj]}
            finally:
                memo.discard(oid)
        if isinstance(obj, frozenset):
            memo.add(oid)
            try:
                return {XSER_TAG: XSER_VER, "t": "frozenset", "v": [cls._enc(x, memo) for x in obj]}
            finally:
                memo.discard(oid)

        # dict (mapping)
        if isinstance(obj, dict):
            memo.add(oid)
            try:
                all_str = all(isinstance(k, str) for k in obj.keys())
                if all_str:
                    return {k: cls._enc(v, memo) for k, v in obj.items()}
                items = []
                for k, v in obj.items():
                    items.append([cls._enc(k, memo), cls._enc(v, memo)])
                return {XSER_TAG: XSER_VER, "t": "dict_items", "v": items}
            finally:
                memo.discard(oid)

        # list
        if isinstance(obj, list):
            memo.add(oid)
            try:
                return [cls._enc(x, memo) for x in obj]
            finally:
                memo.discard(oid)

        # ---------- Generic class support ----------
        to_dict = getattr(obj, "to_dict", None)
        to_list = getattr(obj, "to_list", None)
        tolist = getattr(obj, "tolist", None)

        if callable(to_dict) or callable(to_list) or callable(tolist):
            memo.add(oid)
            try:
                if callable(to_dict):
                    payload = to_dict()
                    fmt = "dict"
                elif callable(to_list):
                    payload = to_list()
                    fmt = "list"
                else:
                    assert callable(tolist)
                    payload = tolist()
                    fmt = "list"
                return {
                    XSER_TAG: XSER_VER,
                    "t": "generic",
                    "cls": _class_path_of(obj),
                    "fmt": fmt,  # "dict" | "list"
                    "v": cls._enc(payload, memo),
                }
            finally:
                memo.discard(oid)

        # Unknown -> structured fallback will be decided by caller
        raise ValueError(f"Unsupported type for structured encoding: {type(obj)}")

    @classmethod
    def _blob(cls, obj: Any, *, enc: str, memo: set[int]) -> Dict[str, Any]:
        """Wrap arbitrary object as a tagged base64 blob (CBOR or Pickle)."""
        if enc == "cbor":
            data = _try_cbor_dumps(obj)
            if data is None:
                raise _XSerCBORFailed("cbor2.dumps failed or cbor2 unavailable")
            return {XSER_TAG: XSER_VER, "t": "blob", "enc": "cbor", "b64": _b64e(data)}
        if enc == "pickle":
            data = pickle.dumps(obj, protocol=5)
            return {
                XSER_TAG: XSER_VER,
                "t": "blob",
                "enc": "pickle",
                "proto": 5,
                "py": sys.version.split()[0],
                "b64": _b64e(data),
            }
        raise ValueError(f"Unknown blob encoding: {enc}")

    # ---------- Decoding helpers ----------

    @classmethod
    def _dec(cls, node: Any) -> Any:
        # Pass-through primitives
        if not isinstance(node, dict) or XSER_TAG not in node:
            if isinstance(node, list):
                return [cls._dec(x) for x in node]
            if isinstance(node, dict):
                return {k: cls._dec(v) for k, v in node.items()}
            return node

        tag = node.get("t")

        if tag == "float":
            v = node["v"]
            if v == "nan":
                return float("nan")
            if v == "inf":
                return float("inf")
            if v == "-inf":
                return float("-inf")
            raise ValueError("Invalid float tag payload")

        if tag == "bytes":
            return _b64d(node["b64"])

        if tag == "tuple":
            return tuple(cls._dec(x) for x in node["v"])
        if tag == "set":
            return set(cls._dec(x) for x in node["v"])
        if tag == "frozenset":
            return frozenset(cls._dec(x) for x in node["v"])

        if tag == "complex":
            r, i = node["v"]
            return complex(r, i)

        if tag == "decimal":
            return Decimal(node["v"])

        if tag == "datetime":
            return datetime.fromisoformat(node["v"])
        if tag == "date":
            return date.fromisoformat(node["v"])
        if tag == "time":
            return time.fromisoformat(node["v"])
        if tag == "timedelta_us":
            us = int(node["v"])
            return timedelta(microseconds=us)
        if tag == "timezone":
            off = int(node["v"])
            return timezone(timedelta(seconds=off))

        if tag == "uuid":
            import uuid
            return uuid.UUID(node["v"])

        if tag == "path":
            from pathlib import Path
            return Path(node["v"])

        if tag == "np_scalar":
            if np is None:
                raise RuntimeError("Decoding numpy scalar requires numpy installed.")
            dt = np.dtype(node["dtype"])
            v = node["v"]
            if dt.kind == "f" and isinstance(v, str):
                if v == "nan":
                    return dt.type(float("nan"))
                if v == "inf":
                    return dt.type(float("inf"))
                if v == "-inf":
                    return dt.type(float("-inf"))
                raise ValueError("Invalid np_scalar float payload")
            return dt.type(v)

        if tag == "np_scalar_bytes":
            if np is None:
                raise RuntimeError("Decoding numpy scalar requires numpy installed.")
            dt = np.dtype(node["dtype"])
            b = _b64d(node["b64"])
            return np.frombuffer(b, dtype=dt)[0]

        if tag == "ndarray":
            if np is None:
                raise RuntimeError("Decoding ndarray requires numpy installed.")
            dtype_desc = node["dtype"]
            dt = np.dtype(dtype_desc if not isinstance(dtype_desc, list) else dtype_desc)
            shape = tuple(int(x) for x in node["shape"])
            order = node.get("order", "C")
            raw = _b64d(node["b64"])
            arr = np.frombuffer(raw, dtype=dt).reshape(shape, order=order)
            return np.array(arr, order=order, copy=True)

        if tag == "dict_items":
            items = node["v"]
            return {cls._dec(k): cls._dec(v) for k, v in items}

        if tag == "blob":
            enc = node["enc"]
            b = _b64d(node["b64"])
            if enc == "cbor":
                return _must_cbor_loads(b)
            if enc == "pickle":
                return pickle.loads(b)
            raise ValueError(f"Unknown blob enc: {enc}")

        if tag == "generic":
            cls_path = node["cls"]
            fmt = node["fmt"]  # "dict" | "list"
            payload = cls._dec(node["v"])  # decode inner first

            # Optional allow-list check
            if XSer.CLASS_ALLOWLIST is not None:
                mod_prefix = cls_path.split(":", 1)[0] + "."
                if not any(mod_prefix.startswith(pfx) for pfx in XSer.CLASS_ALLOWLIST):
                    raise RuntimeError(
                        f"Decoding class {cls_path!r} is not allowed; set allow-list via XSer.set_class_allowlist(...)"
                    )

            target_cls = _import_class(cls_path)

            # Choose constructor method
            if fmt == "dict":
                creator = getattr(target_cls, "from_dict", None) or getattr(target_cls, "fromdict", None)
                if callable(creator):
                    return creator(payload)
                try:
                    return target_cls(payload) # type: ignore[call-arg]
                except Exception as e:
                    raise TypeError(
                        f"Failed to construct {cls_path} from dict payload via from_dict/fromdict or cls(payload): {e}"
                    ) from e

            if fmt == "list":
                creator = getattr(target_cls, "from_list", None) or getattr(target_cls, "fromlist", None)
                if callable(creator):
                    return creator(payload)
                try:
                    return target_cls(payload) # type: ignore[call-arg]
                except Exception as e:
                    raise TypeError(
                        f"Failed to construct {cls_path} from list payload via from_list/fromlist or cls(payload): {e}"
                    ) from e

            raise ValueError(f"Unknown generic fmt: {fmt!r}")

        raise ValueError(f"Unsupported or malformed tagged node: {tag!r}")

    # --- To/From File Methods ---
    @classmethod
    def write_json(cls, path: str, obj: Any, *, indent: int | None = None, **kwargs) -> None:
        s = cls.dump_json(obj, indent=indent, **kwargs)
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)

    @classmethod
    def read_json(cls, path: str, **kwargs) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return cls.load_json(f.read(), **kwargs)

    @classmethod
    def write_yaml(cls, path: str, obj: Any, **kwargs) -> None:
        y = cls.dump_yaml(obj, **kwargs)
        with open(path, "w", encoding="utf-8") as f:
            f.write(y)

    @classmethod
    def read_yaml(cls, path: str, **kwargs) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return cls.load_yaml(f.read(), **kwargs)
        

    @classmethod
    def safe_load(cls, obj: Path | str | bytes | dict | list, **kwargs) -> Any:
        if isinstance(obj, Path) or ((isinstance(obj, str) and str(obj).endswith(('.json', '.jsonl', '.yaml', '.yml', '.pkl', '.pickle')))):
            assert os.path.exists(obj), f"Could not find path: {obj}"
            if isinstance(obj, Path):
                assert str(obj).endswith(('.json', '.jsonl', '.yaml', '.yml', '.pkl', '.pickle')), f"Unable to infer the file format from the file extension"
            if str(obj).endswith(( '.pkl', '.pickle')):
                return pickle.load(open(obj, 'rb'))
            elif str(obj).endswith(('.json', '.jsonl')):
                return cls.read_json(obj, **kwargs) # type: ignore
            elif str(obj).endswith(('.yaml', '.yml')):
                return cls.read_yaml(obj, **kwargs) # type: ignore
        elif isinstance(obj, dict):
            return cls.from_dict(obj, **kwargs)
        elif isinstance(obj, (bytes, list)):
            return cls._dec(obj)
        else:
            raise ValueError(f'Unexpected input of type: {type(obj)}')
        
    @classmethod
    def safe_dump(cls, obj: Any, target: Literal['h5_attr', 'parquet_dataset_metadata', 'json', 'yaml', 'pickle'], out_fp: Optional[str | Path] = None, **kwargs):
        if target == 'h5_attr':
            return cls.to_hdf5_attr(obj)
        elif target == 'parquet_dataset_metadata':
            return cls.to_parquet_kv(obj=obj, **kwargs)
        elif target == 'json':
            if isinstance(out_fp, (str, Path)):
                return cls.write_json(path=str(out_fp), obj=obj, **kwargs)
            return cls.dump_json(obj, **kwargs)
        elif target == 'yaml':
            if isinstance(out_fp, (str, Path)):
                return cls.write_yaml(path=str(out_fp), obj=obj, **kwargs)
            return cls.dump_yaml(obj, **kwargs)
        elif target == 'pickle':
            assert isinstance(out_fp, (str, Path))
            pickle.dump(obj, open(out_fp, 'wb'))
            return
        else:
            raise ValueError(f'Unexpected value for parameter target: {target}')

if __name__ == '__main__':
    a = XSer.to_parquet_kv({'example_key': 'example_value', 'another_key': ['another_value']*1})
    print(str(a))
    b = XSer.from_dict(a) # type: ignore
    print(str(b))
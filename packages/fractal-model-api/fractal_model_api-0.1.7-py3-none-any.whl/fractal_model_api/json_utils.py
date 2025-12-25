import json
from typing import Any


def _build_path(prefix: str, key: Any) -> str:
    if isinstance(key, int):
        segment = f"[{key}]"
    else:
        segment = f".{key}" if prefix else str(key)
    return f"{prefix}{segment}"


def _walk(obj: Any, path: str = "") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _walk(v, _build_path(path, k))
        return

    if isinstance(obj, (list, tuple)):
        for idx, v in enumerate(obj):
            _walk(v, _build_path(path, idx))
        return

    try:
        json.dumps(obj)
    except TypeError as exc:
        msg = str(exc)
        location = path or "<root>"
        raise TypeError(f"{msg} (at path {location})") from exc


def robust_json_dumps(obj: Any, **kwargs: Any) -> str:
    """Dump JSON, raising TypeError with path to the bad value."""
    _walk(obj)
    return json.dumps(obj, **kwargs)


def dump_json_to_file(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)


def _compact_long_arrays(obj: Any) -> Any:
    """Return a copy of obj where long arrays are compacted.

    If a list/tuple has more than 20 elements, it is replaced with
    `[first, second, "... too long array"]`.
    """
    if isinstance(obj, dict):
        return {k: _compact_long_arrays(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        if len(obj) > 20:
            # Preserve the original element types, but truncate.
            first = _compact_long_arrays(obj[0])
            second = _compact_long_arrays(obj[1]) if len(obj) > 1 else None
            compact_list = [first]
            if len(obj) > 1:
                compact_list.append(second)
            compact_list.append("... too long array")
            return compact_list
        return [_compact_long_arrays(v) for v in obj]

    return obj


def dump_json_file_compact(obj: Any, path: str) -> None:
    """Dump JSON to file with long arrays compacted.

    Any list/tuple with more than 20 elements is truncated to
    `[first, second, "... too long array"]` before dumping.
    """
    compact_obj = _compact_long_arrays(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(compact_obj, f, indent=2, default=str)

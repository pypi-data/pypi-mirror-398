import json
import os
from typing import Any, Dict, Iterable, List, Optional, Set

from loguru import logger


def _has_flag_value(v: Optional[object]) -> bool:
    """
    Returns True if the flag has any non-empty content.

    Handles:
    - None → False
    - Strings → True if non-empty after stripping spaces
    - Iterables (list, tuple, set) → True if any element is non-empty
    - Other objects → True if string representation is non-empty

    Examples:
        _has_flag_value(None)                  → False
        _has_flag_value("")                    → False
        _has_flag_value("   ")                 → False
        _has_flag_value("ok")                  → True
        _has_flag_value([None, ""])            → False
        _has_flag_value(["", "  ", "x"])       → True
        _has_flag_value([1, 0])                → True   # "1" and "0" are non-empty strings
        _has_flag_value(set())                 → False
        _has_flag_value({" "})                 → False
        _has_flag_value(123)                   → True
    """
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, Iterable) and not isinstance(v, (str, bytes)):
        # Check if any element in the iterable is non-empty
        for item in v:
            if isinstance(item, str):
                if item.strip():
                    return True
            else:
                if str(item).strip():
                    return True
        return False
    # Fallback: check the string representation of any other type
    return bool(str(v).strip())


def _iter_flag_patterns(flag_value: Optional[object]) -> Iterable[str]:
    """
    Accepts:
      - None
      - CSV string: "a, b"
      - list/tuple/set of strings; each element may itself be CSV
    Yields trimmed, non-empty patterns.
    """
    if flag_value is None:
        return
    if isinstance(flag_value, str):
        items = [flag_value]
    elif isinstance(flag_value, (list, tuple, set)):
        items = [str(x) for x in flag_value]
    else:
        items = [str(flag_value)]
    for item in items:
        for piece in item.split(","):
            piece = piece.strip()
            if piece:
                yield piece


def _parse_rules_file_json(path: str) -> Dict[str, Any]:
    """
    Accepts either:
      { "exclude": ["**/tests", "docs/*"] }
    or:
      { "rules": { "exclude": ["**/tests", "docs/*"] } }
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON rules file '{path}': {e}") from e

    if isinstance(data.get("exclude"), list):
        return {"exclude": data["exclude"]}
    if isinstance(data.get("rules"), dict) and isinstance(
        data["rules"].get("exclude"), list
    ):
        return {"exclude": data["rules"]["exclude"]}
    return {"exclude": []}


def resolve_excludes_from_flag_and_rules(
    exclude_flag: Optional[str], rules_file_path: Optional[str]
) -> List[str]:
    """
    Precedence:
      1) If --exclude has any value -> use ONLY defaults + flag (IGNORE rules file)
      2) Else, if rules file exists -> defaults + rules file
      3) Else -> defaults only
    Returns a sorted list.
    """
    patterns: Set[str] = set()

    if _has_flag_value(exclude_flag):
        logger.debug("--exclude provided; ignoring external rules file.")
        return sorted(_iter_flag_patterns(exclude_flag))

    if rules_file_path:
        file_excludes = _parse_rules_file_json(rules_file_path).get("exclude", [])
        if not isinstance(file_excludes, list):
            raise RuntimeError(
                "The 'exclude' key in the JSON rules file must be a list of glob strings."
            )
        patterns.update(map(str, file_excludes))
        logger.debug(
            f"Using excludes from rules file: {os.path.relpath(rules_file_path or '.')}"
        )
    else:
        logger.debug("No JSON rules file found; using defaults only.")
    return sorted(patterns)

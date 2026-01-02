"""Helper functions for building unified statistical analysis payloads."""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from .schemas import ANALYSIS_SCHEMA_LIBRARY


def _set_nested_value(container: Any, key: str, value: Any) -> bool:
    """Set ``key`` within ``container`` recursively, mirroring legacy behavior."""

    if isinstance(container, dict):
        if key in container:
            container[key] = value
            return True
        for nested in container.values():
            if _set_nested_value(nested, key, value):
                return True
    elif isinstance(container, list):
        for item in container:
            if _set_nested_value(item, key, value):
                return True
    return False


def _normalize_kruskal_effect_size(value: Any) -> List[str]:
    canonical_map = {"epsilon2": "epsilon2", "eta2h": "eta2H"}
    if value is None:
        return ["epsilon2"]
    if isinstance(value, str):
        key = value.strip().lower()
        if not key:
            return ["epsilon2"]
        if key == "none":
            return []
        if key == "both":
            return ["epsilon2", "eta2H"]
        canonical = canonical_map.get(key)
        if canonical:
            return [canonical]
        return ["epsilon2"]
    if isinstance(value, (list, tuple, set)):
        result: List[str] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                key = item.strip().lower()
                if not key or key == "none":
                    continue
                if key == "both":
                    return ["epsilon2", "eta2H"]
                canonical = canonical_map.get(key)
                if canonical and canonical not in result:
                    result.append(canonical)
            else:
                canonical = canonical_map.get(str(item).strip().lower())
                if canonical and canonical not in result:
                    result.append(canonical)
        return result or ["epsilon2"]
    return ["epsilon2"]


def build_analysis_payload(test_name: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Merge ``overrides`` with the default schema for ``test_name``.

    The returned payload matches the unified analysis spec consumed by the
    Figlinq backend. It mirrors the behavior that previously lived in
    ``streambed.shelly.ai.agent_tools`` so that downstream callers can rely on
    a single implementation.
    """

    schema = ANALYSIS_SCHEMA_LIBRARY.get(test_name)
    if schema is None:
        raise KeyError(test_name)

    payload = copy.deepcopy(schema.get("default_spec", {})) or {}
    payload["test"] = test_name
    payload.setdefault("data_mode", "tidy")

    numeric_fields = {"alpha"}
    boolean_fields = {"equal_var", "show_annotations", "continuity_correction", "hl_estimator"}

    for key, value in overrides.items():
        if value is None or key == "test":
            continue
        coerced_value: Any = value
        if key == "computation_mode":
            params = payload.setdefault("params", {})
            params["mode"] = coerced_value
            continue
        if key in numeric_fields:
            try:
                coerced_value = float(value)
            except (TypeError, ValueError):
                coerced_value = value
        elif key in boolean_fields and isinstance(value, str):
            coerced_value = value.lower() in {"1", "true", "yes", "y", "on"}
        if not _set_nested_value(payload, key, coerced_value):
            if key in {"a", "b"}:
                payload.setdefault("groups", {})[key] = coerced_value
            elif key == "row_filter" and isinstance(coerced_value, dict):
                base_filter = payload.setdefault("row_filter", {})
                base_filter.update(coerced_value)
            else:
                payload[key] = coerced_value

    if payload.get("test") == "kruskal_wallis":
        params = payload.setdefault("params", {})
        params["effect_size"] = _normalize_kruskal_effect_size(params.get("effect_size"))
        post_hoc_val = params.get("post_hoc")
        if isinstance(post_hoc_val, str) and post_hoc_val.strip().lower() in {"none", "null", ""}:
            params["post_hoc"] = None

    return payload


__all__ = ["build_analysis_payload"]

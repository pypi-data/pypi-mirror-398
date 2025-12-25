from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ResponsePolicy:
    """Controls how much data is allowed into the LLM context."""

    summary_max_chars: int = 1000
    preview_max_rows: int = 10
    preview_max_chars: int = 6000


def _bounded_value(value: Any, *, max_str_chars: int, max_list_items: int, max_dict_keys: int) -> Any:
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        try:
            value = value.model_dump()
        except Exception:
            return {"_unserializable": True, "type": type(value).__name__}

    if isinstance(value, str):
        if len(value) <= max_str_chars:
            return value
        return value[: max_str_chars - 1] + "…"

    if isinstance(value, (bytes, bytearray)):
        return {"_bytes": len(value)}

    if isinstance(value, Mapping):
        items = list(value.items())
        trimmed = items[:max_dict_keys]
        out = {k: _bounded_value(v, max_str_chars=max_str_chars, max_list_items=max_list_items, max_dict_keys=max_dict_keys) for k, v in trimmed}
        if len(items) > max_dict_keys:
            out["_truncated_keys"] = len(items) - max_dict_keys
        return out

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        seq = list(value)
        trimmed = seq[:max_list_items]
        out = [_bounded_value(v, max_str_chars=max_str_chars, max_list_items=max_list_items, max_dict_keys=max_dict_keys) for v in trimmed]
        if len(seq) > max_list_items:
            out.append({"_truncated_items": len(seq) - max_list_items})
        return out

    return value


def _bounded_row(row: dict[str, Any], *, policy: ResponsePolicy) -> dict[str, Any]:
    # Keep previews compact and stable. Full data is always available via data_key.
    return {
        k: _bounded_value(v, max_str_chars=240, max_list_items=5, max_dict_keys=30)
        for k, v in row.items()
    }


def _coerce_row(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, Mapping):
        return dict(obj)
    return {"value": obj}


def _truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    if max_chars <= 0:
        return "", True
    return text[: max_chars - 1] + "…", True


def build_preview(
    value: Any,
    *,
    policy: ResponsePolicy,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Build a bounded preview + metrics for arbitrary tool output."""

    metrics: dict[str, Any] = {}

    if value is None:
        return None, metrics

    import json

    # List[rows]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rows = [_coerce_row(v) for v in value]
        metrics["row_count"] = len(rows)

        preview_rows = [_bounded_row(r, policy=policy) for r in rows[: policy.preview_max_rows]]
        preview = {"rows": preview_rows}

        # Best-effort schema
        if preview_rows:
            columns: list[str] = []
            for row in preview_rows:
                for k in row.keys():
                    if k not in columns:
                        columns.append(k)
            metrics["columns"] = columns

        # Char cap (rough): serialize-ish
        preview_json = json.dumps(preview_rows, ensure_ascii=False)
        metrics["preview_size_chars"] = len(preview_json)
        if len(preview_json) > policy.preview_max_chars:
            # shrink rows until within char cap
            shrunk = preview_rows
            while shrunk and len(json.dumps(shrunk, ensure_ascii=False)) > policy.preview_max_chars:
                shrunk = shrunk[:-1]
            preview["rows"] = shrunk
            metrics["preview_truncated"] = True
        return preview, metrics

    # Mapping/object -> one row
    row = _bounded_row(_coerce_row(value), policy=policy)
    metrics["row_count"] = 1
    metrics["columns"] = list(row.keys())

    row_json = json.dumps(row, ensure_ascii=False, default=str)
    metrics["preview_size_chars"] = len(row_json)
    if len(row_json) > policy.preview_max_chars:
        # If still too large, fall back to keys-only to avoid blowing up envelopes.
        metrics["preview_truncated"] = True
        row = {
            "_truncated": True,
            "keys": list(metrics["columns"]),
        }

    return {"rows": [row]}, metrics


def normalize_summary(summary: str, *, policy: ResponsePolicy) -> tuple[str, bool]:
    return _truncate_text(summary, policy.summary_max_chars)

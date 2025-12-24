from typing import Any, Dict, Optional


def dict_to_sorted_str(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return ""
    items = []
    for key in sorted(data.keys()):
        val = data[key]
        items.append(f"{key}:{val}")
    return "; ".join(items)


def summarize_state(env_state: Optional[Dict[str, Any]], internal_state: Optional[Dict[str, Any]]) -> str:
    env_part = dict_to_sorted_str(env_state)
    internal_part = dict_to_sorted_str(internal_state)
    return f"env: {env_part} | internal: {internal_part}"

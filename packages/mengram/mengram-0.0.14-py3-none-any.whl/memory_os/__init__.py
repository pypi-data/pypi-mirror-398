"""
Backward compatibility alias to support legacy imports (`import memory_os`).
Prefer importing from `mengram`.
"""

from mengram import MemoryClient, init_memory_os_schema  # type: ignore

__all__ = ["MemoryClient", "init_memory_os_schema"]

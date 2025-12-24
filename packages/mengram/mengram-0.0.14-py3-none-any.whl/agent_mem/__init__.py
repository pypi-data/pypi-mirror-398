"""
Backward compatibility alias for users migrating from `agent-mem` to `mengram`.
"""

from mengram import MemoryClient, init_memory_os_schema  # type: ignore

__all__ = ["MemoryClient", "init_memory_os_schema"]

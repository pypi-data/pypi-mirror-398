from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence

from pydantic import BaseModel, ConfigDict

Role = Literal["user", "assistant", "system", "tool"]
MemoryType = Literal["semantic", "episodic"]
ALLOWED_MEMORY_TYPES = {"semantic", "episodic"}
ALLOWED_SCOPES = {"session", "user", "org"}


class Interaction(BaseModel):
    """Single interaction/turn/tool message fed into the auto-ingest pipeline."""

    model_config = ConfigDict(extra="allow")

    role: Role
    content: str
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class MemoryCandidate(BaseModel):
    """Extractor output that can be turned into a stored memory."""

    model_config = ConfigDict(extra="allow")

    content: str
    type: MemoryType
    importance: Optional[float] = None
    scope: Optional[str] = None
    entity_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


# Extractor contract: callable that accepts interactions and returns candidates.
Extractor = Callable[[List[Interaction]], List[MemoryCandidate]]


def interactions_from_dicts(records: Sequence[Dict[str, Any]]) -> List[Interaction]:
    """Small helper to build Interaction objects from a simple list of dicts."""
    return [Interaction(**record) for record in records]

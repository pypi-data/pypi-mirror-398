from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

Scope = str


class ExperienceIn(BaseModel):
    scope: str
    entity_id: Optional[str] = None
    task_type: Optional[str] = None
    env_state: Optional[Dict[str, Any]] = None
    internal_state: Optional[Dict[str, Any]] = None
    action_type: str
    action_payload: Optional[Dict[str, Any]] = None
    reasoning_summary: Optional[str] = None
    success: bool = False
    reward: Optional[float] = None
    error_type: Optional[str] = None
    latency_ms: Optional[float] = None
    cost: Optional[float] = None
    tags: Optional[List[str]] = None


class ExperienceOut(BaseModel):
    id: str
    scope: str
    entity_id: Optional[str]
    task_type: Optional[str]
    env_state: Optional[Dict[str, Any]]
    internal_state: Optional[Dict[str, Any]]
    action_type: str
    action_payload: Optional[Dict[str, Any]]
    reasoning_summary: Optional[str]
    success: bool
    reward: Optional[float]
    error_type: Optional[str]
    latency_ms: Optional[float]
    cost: Optional[float]
    tags: Optional[List[str]]
    created_at: datetime
    score: Optional[float] = Field(default=None, description="Similarity score for retrieval")


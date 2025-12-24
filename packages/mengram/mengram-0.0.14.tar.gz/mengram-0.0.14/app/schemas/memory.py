from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

MemType = Literal["episodic", "semantic", "profile", "tool"]
Scope = Literal["session", "user", "org"]


class RememberIn(BaseModel):
    content: str
    type: MemType
    scope: Scope
    entity_id: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[float] = 0.0
    ttl_hours: Optional[int] = None
    metadata: Optional[dict] = None


class MemoryOut(BaseModel):
    id: str
    content: str
    type: MemType
    scope: Scope
    entity_id: Optional[str]
    score: Optional[float] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class ReflectIn(BaseModel):
    session_id: str
    budget_tokens: int = 1500


class PlanCondition(BaseModel):
    event_type: str
    tool_name: Optional[str] = None
    scope: Optional[Scope] = None
    entity_id: Optional[str] = None
    window_minutes: int = Field(..., gt=0)
    threshold_count: int = Field(..., gt=0)


class ProspectiveAction(BaseModel):
    type: str
    channel: Optional[str] = None
    target: Optional[str] = None
    message: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PlanThen(BaseModel):
    actions: List[ProspectiveAction]


class PlanIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    if_: PlanCondition = Field(..., alias="if")
    then: PlanThen
    guardrails: Optional[dict] = None


class ForgetIn(BaseModel):
    id: Optional[str] = None
    policy: Optional[str] = None
    reason: Optional[str] = "unspecified"


class EventIn(BaseModel):
    event_type: str
    tool_name: Optional[str] = None
    scope: Optional[Scope] = None
    entity_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class TriggeredAction(BaseModel):
    type: str
    channel: Optional[str] = None
    target: Optional[str] = None
    message: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TriggeredRuleOut(BaseModel):
    rule_id: str
    actions: List[TriggeredAction]


class EventResponse(BaseModel):
    ok: bool = True
    triggered: List[TriggeredRuleOut]

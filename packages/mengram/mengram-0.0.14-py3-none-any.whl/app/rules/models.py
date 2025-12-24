from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence, Union

from pydantic import BaseModel, Field

Scope = Literal["session", "user", "org"]


class RuleCondition(BaseModel):
    event_type: str
    tool_name: Optional[str] = None
    window_minutes: int = Field(..., gt=0)
    threshold_count: int = Field(..., gt=0)
    scope: Optional[Scope] = None
    entity_id: Optional[str] = None

    @classmethod
    def tool_error(
        cls,
        *,
        tool_name: str,
        window_minutes: int,
        threshold_count: int,
        scope: Optional[Scope] = None,
        entity_id: Optional[str] = None,
    ) -> "RuleCondition":
        return cls(
            event_type="tool:error",
            tool_name=tool_name,
            window_minutes=window_minutes,
            threshold_count=threshold_count,
            scope=scope,
            entity_id=entity_id,
        )


class NotifyAction(BaseModel):
    type: Literal["notify"] = "notify"
    channel: str
    target: str
    message: str


class InjectMemoryAction(BaseModel):
    type: Literal["inject_memory"] = "inject_memory"
    content: str
    scope: Optional[Scope] = None
    entity_id: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[float] = None


RuleAction = Union[NotifyAction, InjectMemoryAction]


class RuleOut(BaseModel):
    id: str
    condition: RuleCondition
    actions: List[RuleAction]
    description: Optional[str] = None
    enabled: bool = True
    created_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None


class RuleEvaluationResult(BaseModel):
    triggered_rule_ids: List[str]
    actions: List[RuleAction]
    new_memories: List[Dict[str, Any]]


def normalize_actions(actions: Sequence[Union[RuleAction, Dict[str, Any]]]) -> List[RuleAction]:
    normalized: List[RuleAction] = []
    for action in actions:
        if isinstance(action, NotifyAction) or isinstance(action, InjectMemoryAction):
            normalized.append(action)
            continue
        if not isinstance(action, dict):
            raise ValueError("Rule action must be a dict or a RuleAction instance.")
        action_type = action.get("type")
        if action_type == "notify":
            normalized.append(NotifyAction(**action))
        elif action_type == "inject_memory":
            normalized.append(InjectMemoryAction(**action))
        else:
            raise ValueError(f"Unsupported rule action type: {action_type}")
    return normalized

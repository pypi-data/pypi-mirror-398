from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.db import get_db
from app.core import MemoryClient
from app.schemas.memory import (
    EventIn,
    ForgetIn,
    MemoryOut,
    PlanIn,
    ReflectIn,
    RememberIn,
    Scope,
)
from app.rules.models import RuleEvaluationResult

router = APIRouter(prefix="/v0")


@router.post("/remember", response_model=MemoryOut)
def remember(payload: RememberIn, db: Session = Depends(get_db)):
    client = MemoryClient()
    return client.remember(
        content=payload.content,
        type=payload.type,
        scope=payload.scope,
        entity_id=payload.entity_id,
        tags=payload.tags,
        importance=payload.importance or 0.0,
        ttl_hours=payload.ttl_hours,
        metadata=payload.metadata,
        session=db,
    )


@router.get("/recall", response_model=List[MemoryOut])
def recall(
    query: str,
    k: int = 8,
    scope: Optional[Scope] = None,
    entity_id: Optional[str] = None,
    as_of: Optional[str] = None,
    db: Session = Depends(get_db),
):
    client = MemoryClient()
    return client.recall(
        query=query,
        k=k,
        scope=scope,
        entity_id=entity_id,
        as_of=as_of,
        session=db,
    )


@router.post("/reflect")
def reflect(payload: ReflectIn, db: Session = Depends(get_db)):
    client = MemoryClient()
    return client.reflect(
        session_id=payload.session_id,
        budget_tokens=payload.budget_tokens,
        session=db,
    )


@router.post("/plan")
def plan(payload: PlanIn, db: Session = Depends(get_db)):
    client = MemoryClient()
    return client.create_rule(
        condition=payload.if_.model_dump(),
        actions=payload.then.model_dump(),
        guardrails=payload.guardrails,
        session=db,
    )


@router.post("/forget")
def forget(payload: ForgetIn, db: Session = Depends(get_db)):
    client = MemoryClient()
    return client.forget(
        id=payload.id,
        policy=payload.policy,
        reason=payload.reason,
        session=db,
    )


@router.post("/event", response_model=RuleEvaluationResult)
def ingest_event(payload: EventIn, db: Session = Depends(get_db)):
    client = MemoryClient()
    return client.record_event(
        event_type=payload.event_type,
        tool_name=payload.tool_name,
        scope=payload.scope,
        entity_id=payload.entity_id,
        payload=payload.payload,
        session=db,
    )

from datetime import datetime, timedelta
from typing import Any, Callable, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.memory import Memory, Rule
from app.schemas.memory import (
    ForgetIn,
    MemoryOut,
    PlanIn,
    ReflectIn,
    RememberIn,
    Scope,
)
from app.services.embedding import embed_text, str_to_vec, vec_to_str
from app.services.pii import redact_pii
from app.services.scoring import cosine_sim, lexical_sim
from app.utils.time import new_id, now_utc

EmbedFn = Callable[[str], Any]


def remember_memory(
    db: Session,
    payload: RememberIn,
    *,
    embed_fn: EmbedFn = embed_text,
    redact: bool = True,
) -> MemoryOut:
    text = payload.content
    pii_tags: List[str] = []
    if redact:
        text, pii_tags = redact_pii(payload.content)
    embedding = embed_fn(text)
    memory_id = new_id()

    ttl = None
    if payload.ttl_hours is not None:
        ttl = now_utc() + timedelta(hours=payload.ttl_hours)

    memory = Memory(
        id=memory_id,
        type=payload.type,
        scope=payload.scope,
        entity_id=payload.entity_id,
        content=text,
        metadata_json=payload.metadata or {},
        tags=(payload.tags or []) + pii_tags,
        importance=payload.importance or 0.0,
        created_at=now_utc(),
        ttl=ttl,
        embedding=vec_to_str(embedding),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    return MemoryOut(
        id=memory.id,
        content=memory.content,
        type=memory.type,
        scope=memory.scope,
        entity_id=memory.entity_id,
        tags=memory.tags,
        metadata=memory.metadata_json or {},
    )


def recall_memories(
    db: Session,
    *,
    query: str,
    k: int = 8,
    scope: Optional[Scope] = None,
    entity_id: Optional[str] = None,
    as_of: Optional[str] = None,
    embed_fn: EmbedFn = embed_text,
) -> List[MemoryOut]:
    query_embedding = embed_fn(query)

    q = db.query(Memory)
    if scope:
        q = q.filter(Memory.scope == scope)
    if entity_id:
        q = q.filter(Memory.entity_id == entity_id)

    if as_of:
        try:
            as_of_dt = datetime.fromisoformat(as_of)
            q = q.filter(Memory.created_at <= as_of_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid as_of datetime format. Use ISO8601.")

    memories = q.all()
    results = []
    current_time = now_utc()

    for memory in memories:
        if memory.ttl and memory.ttl < current_time:
            continue
        mem_vec = str_to_vec(memory.embedding) if memory.embedding else None
        vector_score = cosine_sim(query_embedding, mem_vec)
        lexical_score = lexical_sim(query, memory.content)
        score = 0.7 * vector_score + 0.3 * lexical_score
        results.append((score, memory))

    results.sort(key=lambda item: item[0], reverse=True)
    top_results = results[:k]

    for _, memory in top_results:
        memory.last_accessed = current_time
    db.commit()

    return [
        MemoryOut(
            id=memory.id,
            content=memory.content,
            type=memory.type,
            scope=memory.scope,
            entity_id=memory.entity_id,
            score=float(score),
            tags=memory.tags,
            metadata=memory.metadata_json or {},
        )
        for score, memory in top_results
    ]


def reflect_session(db: Session, payload: ReflectIn, *, embed_fn: EmbedFn = embed_text):
    query = (
        db.query(Memory)
        .filter(
            Memory.scope == "session",
            Memory.entity_id == payload.session_id,
            Memory.type == "episodic",
        )
        .order_by(Memory.created_at.desc())
        .limit(20)
    )
    events = query.all()
    if not events:
        return {"ok": False, "summary_id": None, "message": "No episodic memories found for this session."}

    summary_lines = [f"- {m.content[:200]}" for m in reversed(events)]
    summary = "Session summary (naive V0):\n" + "\n".join(summary_lines)

    embedding = embed_fn(summary)
    summary_id = new_id()
    summary_memory = Memory(
        id=summary_id,
        type="semantic",
        scope="session",
        entity_id=payload.session_id,
        content=summary,
        metadata_json={"summary_of": [m.id for m in events]},
        tags=["summary"],
        importance=0.6,
        created_at=now_utc(),
        embedding=vec_to_str(embedding),
    )
    db.add(summary_memory)
    db.commit()

    return {"ok": True, "summary_id": summary_id}


def store_plan(db: Session, payload: PlanIn):
    rule_id = new_id()
    rule = Rule(
        id=rule_id,
        if_json=payload.if_.model_dump(),
        then_json=payload.then.model_dump(),
        guardrails_json=payload.guardrails or {},
        active=True,
        created_at=now_utc(),
    )
    db.add(rule)
    db.commit()
    return {"ok": True, "rule_id": rule_id}


def forget_memory(db: Session, payload: ForgetIn):
    if payload.id:
        memory = db.query(Memory).filter(Memory.id == payload.id).first()
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        db.delete(memory)
        db.commit()
        return {"ok": True, "deleted": payload.id}

    if payload.policy:
        policy = payload.policy
        if policy.startswith("older_than:"):
            try:
                days_str = policy.split(":", 1)[1]
                days = int(days_str.replace("d", ""))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid older_than policy. Example: older_than:90d")
            cutoff = now_utc() - timedelta(days=days)
            deleted = db.query(Memory).filter(Memory.created_at < cutoff).delete()
            db.commit()
            return {"ok": True, "deleted_count": deleted, "policy": policy}
        raise HTTPException(status_code=400, detail="Unsupported policy. Supported: older_than:Nd")

    raise HTTPException(status_code=400, detail="Provide either id or policy in the request body")

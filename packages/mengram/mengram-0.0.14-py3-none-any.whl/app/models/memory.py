from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, JSON, String, Text

from app.db.base import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    scope = Column(String, index=True)
    entity_id = Column(String, index=True, nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column("metadata", JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    importance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    ttl = Column(DateTime, nullable=True)
    embedding = Column(Text, nullable=True)


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, index=True)
    if_json = Column(JSON, nullable=False)
    then_json = Column(JSON, nullable=False)
    guardrails_json = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    description = Column(String, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    event_type = Column(String, index=True, nullable=False)
    tool_name = Column(String, index=True, nullable=True)
    scope = Column(String, index=True, nullable=True)
    entity_id = Column(String, index=True, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(String, primary_key=True, index=True)
    scope = Column(String, index=True)
    entity_id = Column(String, index=True, nullable=True)
    task_type = Column(String, index=True, nullable=True)
    env_state = Column(JSON, nullable=True)
    internal_state = Column(JSON, nullable=True)
    action_type = Column(String, index=True)
    action_payload = Column(JSON, nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    reward = Column(Float, nullable=True)
    error_type = Column(String, nullable=True)
    latency_ms = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    embedding = Column(Text, nullable=True)

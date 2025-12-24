"""
Primary public package surface for mengram.

Exports:
- MemoryClient: programmatic API for memories/rules/events/experiences
- init_memory_os_schema: creates required tables (idempotent)
- Interaction / MemoryCandidate: data models for auto-ingest
- LLMMemoryExtractor: reference LLM-based extractor
- RuleCondition / NotifyAction / InjectMemoryAction: prospective rules
- ExperienceIn / ExperienceOut: procedural memory traces
"""

from app.core import MemoryClient
from app.db.init_db import init_memory_os_schema
from app.auto import Interaction, MemoryCandidate, LLMMemoryExtractor, interactions_from_dicts
from app.rules.models import RuleCondition, NotifyAction, InjectMemoryAction, RuleEvaluationResult, RuleOut
from app.schemas.experience import ExperienceIn, ExperienceOut

__all__ = [
    "MemoryClient",
    "init_memory_os_schema",
    "Interaction",
    "MemoryCandidate",
    "LLMMemoryExtractor",
    "interactions_from_dicts",
    "RuleCondition",
    "NotifyAction",
    "InjectMemoryAction",
    "RuleEvaluationResult",
    "RuleOut",
    "ExperienceIn",
    "ExperienceOut",
]

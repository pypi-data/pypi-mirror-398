from __future__ import annotations

import json
from typing import Callable, List, Optional

from app.auto.models import Interaction, MemoryCandidate


class MemoryExtractionError(Exception):
    """Raised when the LLM extractor cannot produce valid candidates."""


def format_interactions(interactions: List[Interaction]) -> str:
    """Human-friendly text block for the LLM prompt."""
    lines = []
    for idx, item in enumerate(interactions, start=1):
        ts = f"[{item.timestamp.isoformat()}] " if item.timestamp else ""
        role = item.role.upper()
        tool_name = item.metadata.get("tool_name") if item.role == "tool" else None
        role_label = f"{role}({tool_name})" if tool_name else role
        lines.append(f"{idx}. {ts}{role_label}: {item.content}")
    return "\n".join(lines)


class LLMMemoryExtractor:
    """
    Reference extractor that uses an LLM to propose memories.

    llm_client signature:
        llm_client(prompt: str, *, model: Optional[str] = None, temperature: Optional[float] = None) -> str
    You are responsible for calling your provider (OpenAI/Anthropic/local) and returning the raw text output.
    """

    def __init__(
        self,
        llm_client: Callable[..., str],
        *,
        model: Optional[str] = None,
        max_memories: int = 5,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ):
        self.llm_client = llm_client
        self.model = model
        self.max_memories = max_memories
        self.temperature = temperature
        self.system_prompt = system_prompt or self._default_system_prompt()

    def __call__(self, interactions: List[Interaction]) -> List[MemoryCandidate]:
        if not interactions:
            return []
        prompt = self._build_prompt(interactions)
        raw = self.llm_client(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        parsed = self._parse_response(raw)
        candidates = [MemoryCandidate(**item) for item in parsed]
        if self.max_memories and len(candidates) > self.max_memories:
            candidates = candidates[: self.max_memories]
        return candidates

    def _build_prompt(self, interactions: List[Interaction]) -> str:
        history = format_interactions(interactions)
        return (
            f"{self.system_prompt}\n\n"
            "Interaction history:\n"
            f"{history}\n\n"
            f"Extract up to {self.max_memories} long-term memories. "
            "Return ONLY a JSON array of objects matching this schema:\n"
            "{\n"
            '  "content": str,\n'
            '  "type": "semantic" | "episodic",\n'
            '  "importance": float (0.0-1.0, optional),\n'
            '  "scope": str (optional),\n'
            '  "entity_id": str (optional),\n'
            '  "tags": [str],\n'
            '  "metadata": { }\n'
            "}\n"
            "No prose, no explanation—just JSON."
        )

    def _parse_response(self, raw: str):
        try:
            loaded = json.loads(self._strip_fences(raw))
        except Exception as exc:
            raise MemoryExtractionError(f"Failed to parse LLM extractor output as JSON: {raw}") from exc

        if not isinstance(loaded, list):
            raise MemoryExtractionError(
                f"LLM extractor output must be a JSON array of objects, got: {type(loaded)}"
            )
        return loaded

    def _strip_fences(self, text: str) -> str:
        if text.strip().startswith("```"):
            return "\n".join(
                line for line in text.strip().splitlines() if not line.strip().startswith("```")
            )
        return text

    def _default_system_prompt(self) -> str:
        return (
            "You are a memory extraction module for an AI agent.\n"
            "From the interaction history, extract concise long-term memories.\n"
            '- Use type "semantic" for stable facts/preferences; "episodic" for specific events.\n'
            "Set importance from 0.0 to 1.0 when useful. Be brief and precise."
        )

import tempfile
from pathlib import Path
import unittest

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from mengram import Interaction, MemoryCandidate, MemoryClient


def fake_embed(_: str):
    return np.ones(384, dtype=np.float32)


def fake_extractor(_: list[Interaction]):
    return [
        MemoryCandidate(
            content="User prefers morning deliveries.",
            type="semantic",
            importance=0.8,
            scope=None,
            entity_id=None,
            tags=["preference"],
        ),
        MemoryCandidate(
            content="System outage occurred at noon.",
            type="episodic",
            importance=0.3,
            scope=None,
            entity_id=None,
            tags=["incident"],
        ),
    ]


class AutoIngestTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "auto.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.client = MemoryClient(session_factory=session_factory, embed_fn=fake_embed)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_auto_ingest_overrides_scope_and_entity(self):
        interactions = [
            Interaction(role="user", content="Morning deliveries please."),
        ]
        stored = self.client.auto_ingest(
            interactions=interactions,
            extractor=fake_extractor,
            scope="user",
            entity_id="user-123",
            min_importance=0.2,
            max_memories=1,
        )
        self.assertEqual(len(stored), 1)
        mem = stored[0]
        self.assertEqual(mem.scope, "user")
        self.assertEqual(mem.entity_id, "user-123")
        self.assertIn("preference", mem.tags)

    def test_auto_ingest_filters_low_importance(self):
        interactions = [Interaction(role="user", content="test")]
        stored = self.client.auto_ingest(
            interactions=interactions,
            extractor=fake_extractor,
            min_importance=0.5,
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "User prefers morning deliveries.")

    def test_auto_ingest_clamps_scope(self):
        def scoped_extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="Travel memory with bad scope.",
                    type="semantic",
                    scope="travel",
                    entity_id=None,
                )
            ]

        interactions = [Interaction(role="user", content="test")]
        stored = self.client.auto_ingest(
            interactions=interactions,
            extractor=scoped_extractor,
            scope="user",
            entity_id="user-999",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].scope, "user")
        self.assertEqual(stored[0].entity_id, "user-999")

    def test_auto_ingest_skips_exact_existing_duplicate(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="user",
            entity_id="user-dedupe",
        )

        def duplicate_extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=duplicate_extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 0)

    def test_auto_ingest_skips_normalized_duplicate_case_and_spaces(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="user",
            entity_id="user-dedupe",
        )

        def noisy_extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="  user PREFERS   morning  deliveries. ",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=noisy_extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 0)

    def test_auto_ingest_does_not_dedupe_across_entities(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="user",
            entity_id="user-A",
        )

        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-B",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-B",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].entity_id, "user-B")

    def test_auto_ingest_does_not_dedupe_across_scopes(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="session",
            entity_id="sess-123",
        )

        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].scope, "user")

    def test_auto_ingest_dedupes_across_types_for_same_content(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="user",
            entity_id="user-dedupe",
        )

        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="episodic",
                    scope="user",
                    entity_id="user-dedupe",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 0)

    def test_auto_ingest_dedupes_within_batch_exact(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                ),
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "User prefers morning deliveries.")

    def test_auto_ingest_skips_only_duplicate_and_keeps_new_in_batch(self):
        self.client.remember(
            content="User prefers morning deliveries.",
            type="semantic",
            scope="user",
            entity_id="user-dedupe",
        )

        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                ),
                MemoryCandidate(
                    content="User lives in Toronto.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-dedupe",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "User lives in Toronto.")

    def test_auto_ingest_keeps_high_importance_duplicate_when_one_low_one_high(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                    importance=0.2,
                ),
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-dedupe",
                    importance=0.9,
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-dedupe",
            min_importance=0.5,
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "User prefers morning deliveries.")

    def test_auto_ingest_respects_min_importance(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="A",
                    type="semantic",
                    scope="user",
                    entity_id="user-min",
                    importance=0.3,
                ),
                MemoryCandidate(
                    content="B",
                    type="semantic",
                    scope="user",
                    entity_id="user-min",
                    importance=0.7,
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-min",
            min_importance=0.5,
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "B")

    def test_auto_ingest_respects_max_memories_after_dedupe_and_sort(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="A",
                    type="semantic",
                    scope="user",
                    entity_id="user-max",
                    importance=0.1,
                ),
                MemoryCandidate(
                    content="B",
                    type="semantic",
                    scope="user",
                    entity_id="user-max",
                    importance=0.9,
                ),
                MemoryCandidate(
                    content="C",
                    type="semantic",
                    scope="user",
                    entity_id="user-max",
                    importance=0.7,
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-max",
            max_memories=2,
        )
        self.assertEqual(len(stored), 2)
        contents = {m.content for m in stored}
        self.assertEqual(contents, {"B", "C"})

    def test_auto_ingest_ignores_empty_or_whitespace_content(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="",
                    type="semantic",
                    scope="user",
                    entity_id="user-empty",
                ),
                MemoryCandidate(
                    content="   ",
                    type="semantic",
                    scope="user",
                    entity_id="user-empty",
                ),
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="user",
                    entity_id="user-empty",
                ),
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-empty",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].content, "User prefers morning deliveries.")

    def test_auto_ingest_clamps_invalid_candidate_scope_to_outer_scope(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="User prefers morning deliveries.",
                    type="semantic",
                    scope="travel",
                    entity_id="user-clamp",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="user-clamp",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].scope, "user")

    def test_auto_ingest_allows_valid_candidate_scope_override(self):
        def extractor(_: list[Interaction]):
            return [
                MemoryCandidate(
                    content="This is a session-scoped memory.",
                    type="semantic",
                    scope="session",
                    entity_id="sess-override",
                )
            ]

        stored = self.client.auto_ingest(
            interactions=[Interaction(role="user", content="test")],
            extractor=extractor,
            scope="user",
            entity_id="sess-override",
        )
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].scope, "session")


if __name__ == "__main__":
    unittest.main()

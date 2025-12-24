import tempfile
from pathlib import Path
import unittest

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from mengram import MemoryClient


def fake_embed(_: str):
    return np.ones(384, dtype=np.float32)


class MemoryClientTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.client = MemoryClient(session_factory=self.SessionLocal, embed_fn=fake_embed)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_remember_and_recall(self):
        memory = self.client.remember(
            content="Discussed refund policy with Alice.",
            type="episodic",
            scope="session",
            entity_id="test-session",
            tags=["support"],
        )
        hits = self.client.recall(
            query="refund policy",
            scope="session",
            entity_id="test-session",
        )
        self.assertTrue(any(hit.id == memory.id for hit in hits))

    def test_rule_trigger_after_two_events(self):
        self.client.create_rule(
            condition={
                "event_type": "tool:error",
                "tool_name": "unit_test_tool",
                "window_minutes": 5,
                "threshold_count": 2,
            },
            actions={
                "actions": [
                    {
                        "type": "notify",
                        "channel": "stdout",
                        "target": "#ops",
                        "message": "unit_test_tool failed twice.",
                    }
                ]
            },
        )
        first = self.client.record_event(
            event_type="tool:error",
            tool_name="unit_test_tool",
            scope="session",
            entity_id="test-session",
        )
        self.assertEqual(first.triggered_rule_ids, [])

        second = self.client.record_event(
            event_type="tool:error",
            tool_name="unit_test_tool",
            scope="session",
            entity_id="test-session",
        )
        self.assertGreaterEqual(len(second.triggered_rule_ids), 1)

    def test_forget_removes_memory(self):
        memory = self.client.remember(
            content="Temporary note to forget.",
            type="episodic",
            scope="session",
            entity_id="forget-session",
        )
        self.client.forget(id=memory.id)
        hits = self.client.recall(query="Temporary", scope="session", entity_id="forget-session")
        self.assertTrue(all(hit.id != memory.id for hit in hits))


if __name__ == "__main__":
    unittest.main()

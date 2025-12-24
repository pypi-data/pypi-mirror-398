import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import unittest

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from mengram import ExperienceIn, MemoryClient


def simple_embed(text: str):
    # Deterministic vector based on length to get different sims
    val = float(len(text))
    return np.array([val, val, val], dtype=np.float32)


class ExperiencesTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "exp.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.client = MemoryClient(session_factory=session_factory, embed_fn=simple_embed)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_store_and_retrieve_experience(self):
        trace = ExperienceIn(
            scope="user",
            entity_id="u1",
            task_type="planning",
            env_state={"tool": "forecast"},
            internal_state={"goal": "update model"},
            action_type="call_tool",
            action_payload={"name": "forecast", "args": {"region": "US"}},
            reasoning_summary="Needed updated forecast for US.",
            success=True,
            reward=0.8,
        )
        self.client.record_experience(trace)
        results = self.client.retrieve_experiences(
            env_state={"tool": "forecast"},
            internal_state={"goal": "update model"},
            scope="user",
            entity_id="u1",
            k=3,
        )
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].action_type, "call_tool")

    def test_scope_isolation(self):
        trace = ExperienceIn(
            scope="user",
            entity_id="u1",
            task_type="planning",
            env_state={"tool": "forecast"},
            internal_state={"goal": "update model"},
            action_type="call_tool",
            success=True,
        )
        self.client.record_experience(trace)
        results = self.client.retrieve_experiences(
            env_state={"tool": "forecast"},
            internal_state={"goal": "update model"},
            scope="user",
            entity_id="other",
            k=3,
        )
        self.assertEqual(len(results), 0)

    def test_suggest_actions_prefers_success_and_reward(self):
        # Successful, higher reward
        self.client.record_experience(
            ExperienceIn(
                scope="user",
                entity_id="u1",
                env_state={"tool": "forecast"},
                internal_state={"goal": "update model"},
                action_type="call_tool",
                success=True,
                reward=0.9,
            )
        )
        # Unsuccessful
        self.client.record_experience(
            ExperienceIn(
                scope="user",
                entity_id="u1",
                env_state={"tool": "forecast"},
                internal_state={"goal": "update model"},
                action_type="retry",
                success=False,
                reward=0.0,
            )
        )
        suggestions = self.client.suggest_actions(
            env_state={"tool": "forecast"},
            internal_state={"goal": "update model"},
            scope="user",
            entity_id="u1",
            top_n=1,
        )
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].action_type, "call_tool")


if __name__ == "__main__":
    unittest.main()

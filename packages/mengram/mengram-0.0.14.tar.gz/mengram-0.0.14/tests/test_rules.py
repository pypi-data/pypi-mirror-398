import tempfile
from pathlib import Path
import unittest

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from mengram import (
    InjectMemoryAction,
    MemoryClient,
    NotifyAction,
    RuleCondition,
)


def fake_embed(_: str):
    return np.ones(384, dtype=np.float32)


class RulesTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "rules.db"
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.client = MemoryClient(session_factory=session_factory, embed_fn=fake_embed)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_rule_fires_on_third_error_in_window(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=3,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 3 times in 10 minutes.",
                )
            ],
        )

        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(len(result.triggered_rule_ids), 1)
        self.assertEqual(len(result.actions), 1)

    def test_rule_does_not_fire_before_threshold(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=3,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 3 times in 10 minutes.",
                )
            ],
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(result.triggered_rule_ids, [])

    def test_rule_does_not_retrigger_immediately_after_firing(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=2,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 2 times in 10 minutes.",
                )
            ],
        )
        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        fired = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(len(fired.triggered_rule_ids), 1)
        after = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(after.triggered_rule_ids, [])

    def test_rule_scoped_by_entity(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=2,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 2 times in 10 minutes.",
                )
            ],
        )
        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="other-user",
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="other-user",
        )
        self.assertEqual(result.triggered_rule_ids, [])

    def test_inject_memory_action_creates_memory(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=1,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                InjectMemoryAction(
                    content="node_forecast is unstable, consider fallback.",
                    scope="user",
                    entity_id="dhruv",
                    importance=0.6,
                    tags=["alert"],
                )
            ],
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(len(result.new_memories), 1)
        memories = self.client.recall(query="fallback", scope="user", entity_id="dhruv", k=5)
        self.assertTrue(any("fallback" in m.content for m in memories))

    def test_disabled_rule_does_not_fire(self):
        rule = self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=2,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 2 times in 10 minutes.",
                )
            ],
        )
        self.client.disable_rule(rule.id)

        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(result.actions, [])

        enabled = self.client.list_rules(scope="user", entity_id="dhruv", enabled_only=True)
        all_rules = self.client.list_rules(scope="user", entity_id="dhruv", enabled_only=False)
        self.assertEqual(len(enabled), 0)
        self.assertEqual(len(all_rules), 1)

    def test_tool_name_mismatch_does_not_fire(self):
        self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=2,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="node_forecast failed 2 times in 10 minutes.",
                )
            ],
        )
        self.client.record_event(
            event_type="tool:error",
            tool_name="other_tool",
            scope="user",
            entity_id="dhruv",
        )
        result = self.client.record_event(
            event_type="tool:error",
            tool_name="other_tool",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(result.actions, [])

    def test_multiple_rules_edge_triggered(self):
        rule_a = self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=2,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="A fired",
                )
            ],
        )
        rule_b = self.client.create_rule(
            condition=RuleCondition.tool_error(
                tool_name="node_forecast",
                window_minutes=10,
                threshold_count=3,
                scope="user",
                entity_id="dhruv",
            ),
            actions=[
                NotifyAction(
                    channel="stdout",
                    target="#ops",
                    message="B fired",
                )
            ],
        )

        self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        second = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(set(second.triggered_rule_ids), {rule_a.id})

        third = self.client.record_event(
            event_type="tool:error",
            tool_name="node_forecast",
            scope="user",
            entity_id="dhruv",
        )
        self.assertEqual(set(third.triggered_rule_ids), {rule_b.id})


if __name__ == "__main__":
    unittest.main()

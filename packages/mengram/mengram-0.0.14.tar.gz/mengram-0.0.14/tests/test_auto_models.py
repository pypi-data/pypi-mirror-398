import unittest
from datetime import datetime

from mengram import Interaction, interactions_from_dicts


class InteractionHelperTest(unittest.TestCase):
    def test_interactions_from_dicts_basic(self):
        records = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        interactions = interactions_from_dicts(records)
        self.assertEqual(len(interactions), 2)
        self.assertEqual(interactions[0].role, "user")
        self.assertEqual(interactions[0].content, "Hi")
        self.assertEqual(interactions[0].metadata, {})
        self.assertEqual(interactions[1].role, "assistant")
        self.assertEqual(interactions[1].content, "Hello")

    def test_interactions_from_dicts_with_optional_fields(self):
        ts = datetime.utcnow()
        records = [
            {
                "role": "tool",
                "content": "Search results",
                "timestamp": ts,
                "metadata": {"tool_name": "search_tool", "query": "abc"},
            }
        ]
        interactions = interactions_from_dicts(records)
        self.assertEqual(interactions[0].timestamp, ts)
        self.assertEqual(interactions[0].metadata["tool_name"], "search_tool")
        self.assertEqual(interactions[0].metadata["query"], "abc")


if __name__ == "__main__":
    unittest.main()

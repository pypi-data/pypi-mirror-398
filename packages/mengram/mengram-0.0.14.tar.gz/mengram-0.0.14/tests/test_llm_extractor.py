import json
import unittest

from mengram import Interaction, LLMMemoryExtractor, MemoryCandidate
from app.auto.extractors import MemoryExtractionError


def fake_llm_ok(prompt: str, model=None, temperature=None) -> str:
    # Return two candidates as JSON
    return json.dumps(
        [
            {
                "content": "User prefers morning deliveries.",
                "type": "semantic",
                "importance": 0.8,
                "tags": ["preference"],
            },
            {
                "content": "System outage occurred at noon.",
                "type": "episodic",
                "importance": 0.3,
                "tags": ["incident"],
            },
        ]
    )


def fake_llm_bad_json(prompt: str, model=None, temperature=None) -> str:
    return "not-json"


def fake_llm_object(prompt: str, model=None, temperature=None) -> str:
    return json.dumps({"memories": []})


def fake_llm_overflow(prompt: str, model=None, temperature=None) -> str:
    return json.dumps(
        [
            {"content": f"Memory {i}", "type": "semantic", "importance": 1.0}
            for i in range(5)
        ]
    )


class LLMMemoryExtractorTest(unittest.TestCase):
    def setUp(self):
        self.interactions = [
            Interaction(role="user", content="Hi"),
            Interaction(role="assistant", content="Hello"),
        ]

    def test_happy_path_parses_candidates(self):
        extractor = LLMMemoryExtractor(llm_client=fake_llm_ok, max_memories=5)
        candidates = extractor(self.interactions)
        self.assertEqual(len(candidates), 2)
        self.assertIsInstance(candidates[0], MemoryCandidate)
        self.assertEqual(candidates[0].content, "User prefers morning deliveries.")
        self.assertEqual(candidates[0].type, "semantic")

    def test_invalid_json_raises(self):
        extractor = LLMMemoryExtractor(llm_client=fake_llm_bad_json)
        with self.assertRaises(MemoryExtractionError):
            extractor(self.interactions)

    def test_non_array_raises(self):
        extractor = LLMMemoryExtractor(llm_client=fake_llm_object)
        with self.assertRaises(MemoryExtractionError):
            extractor(self.interactions)

    def test_max_memories_cap(self):
        extractor = LLMMemoryExtractor(llm_client=fake_llm_overflow, max_memories=2)
        candidates = extractor(self.interactions)
        self.assertEqual(len(candidates), 2)


if __name__ == "__main__":
    unittest.main()

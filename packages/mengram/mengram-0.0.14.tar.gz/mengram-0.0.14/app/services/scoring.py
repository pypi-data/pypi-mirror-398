from typing import Iterable, Set

import numpy as np


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)


def lexical_sim(query: str, doc: str) -> float:
    """Tiny lexical similarity based on Jaccard overlap."""
    q_tokens: Set[str] = _tokenize(query)
    d_tokens: Set[str] = _tokenize(doc)
    if not q_tokens or not d_tokens:
        return 0.0
    return len(q_tokens & d_tokens) / len(q_tokens | d_tokens)


def _tokenize(text: str) -> Set[str]:
    return set(text.lower().split())

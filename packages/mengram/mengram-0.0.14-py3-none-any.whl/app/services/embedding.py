from typing import Optional

import numpy as np

_embedder = None


def get_embedder():
    """Lazy-load the sentence-transformers model."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required. Install it with 'pip install sentence-transformers'."
            ) from exc
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def embed_text(text: str) -> np.ndarray:
    model = get_embedder()
    return model.encode([text], normalize_embeddings=True)[0].astype(np.float32)


def vec_to_str(vec) -> str:
    """
    Convert an embedding vector to a space-separated string.

    Accepts:
    - numpy arrays
    - Python lists / tuples
    - any iterable of numeric values
    """
    # If the object already supports .tolist(), use it (numpy arrays etc.)
    if hasattr(vec, "tolist"):
        values = vec.tolist()
    else:
        # Fallback: try to interpret it as an iterable
        values = list(vec)

    return " ".join(str(x) for x in values)


def str_to_vec(data: Optional[str]) -> np.ndarray:
    if not data:
        return np.zeros(384, dtype=np.float32)
    floats = [float(x) for x in data.split()]
    return np.array(floats, dtype=np.float32)

import re


_whitespace_re = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """
    Lightweight normalization for deduping:
    - trim
    - collapse whitespace
    - lowercase
    """
    collapsed = _whitespace_re.sub(" ", text.strip())
    return collapsed.lower()

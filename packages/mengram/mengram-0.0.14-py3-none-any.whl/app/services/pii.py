import re
from typing import List, Tuple

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\+?\d[\d\-\s]{7,}\d")


def redact_pii(text: str) -> Tuple[str, List[str]]:
    """Very small helper that redacts obvious emails/phone numbers."""
    tags: List[str] = []
    if EMAIL_RE.search(text):
        tags.append("pii:email")
        text = EMAIL_RE.sub("[EMAIL]", text)
    if PHONE_RE.search(text):
        tags.append("pii:phone")
        text = PHONE_RE.sub("[PHONE]", text)
    return text, tags

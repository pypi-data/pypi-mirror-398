from datetime import datetime
import uuid


def now_utc() -> datetime:
    return datetime.utcnow()


def new_id() -> str:
    return uuid.uuid4().hex

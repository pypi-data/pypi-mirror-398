from datetime import timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.memory import Event, Rule
from app.schemas.memory import EventIn, EventResponse, TriggeredRuleOut
from app.utils.time import new_id, now_utc


def handle_event(db: Session, payload: EventIn) -> EventResponse:
    event = Event(
        id=new_id(),
        event_type=payload.event_type,
        tool_name=payload.tool_name,
        scope=payload.scope,
        entity_id=payload.entity_id,
        payload=payload.payload or {},
        created_at=now_utc(),
    )
    db.add(event)
    db.flush()  # ensure this event is visible for aggregation

    triggered: List[TriggeredRuleOut] = []
    active_rules = db.query(Rule).filter(Rule.active.is_(True)).all()
    for rule in active_rules:
        condition = rule.if_json or {}
        if not _condition_matches(condition, payload):
            continue
        if not _threshold_met(db, condition):
            continue
        actions = _extract_actions(rule.then_json)
        if not actions:
            continue
        triggered.append(TriggeredRuleOut(rule_id=rule.id, actions=actions))

    db.commit()
    return EventResponse(triggered=triggered)


def _condition_matches(condition: Dict[str, Any], payload: EventIn) -> bool:
    event_type = condition.get("event_type")
    if not event_type or event_type != payload.event_type:
        return False
    for field in ("tool_name", "scope", "entity_id"):
        expected = condition.get(field)
        if expected is not None and getattr(payload, field) != expected:
            return False
    return True


def _threshold_met(db: Session, condition: Dict[str, Any]) -> bool:
    window_minutes = condition.get("window_minutes")
    threshold_count = condition.get("threshold_count")
    if not window_minutes or not threshold_count:
        return False

    window_start = now_utc() - timedelta(minutes=window_minutes)
    query = db.query(Event).filter(Event.created_at >= window_start)

    event_type = condition.get("event_type")
    query = query.filter(Event.event_type == event_type)

    for field in ("tool_name", "scope", "entity_id"):
        value = condition.get(field)
        if value is not None:
            query = query.filter(getattr(Event, field) == value)

    count = query.count()
    return count >= threshold_count


def _extract_actions(then_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = (then_json or {}).get("actions", [])
    valid_actions: List[Dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get("type")
        if not action_type:
            continue
        valid_actions.append(action)
    return valid_actions

import uuid

_EVENT_REGISTRY = {}


def register_event(handler):
    """
    Registers a Python function and returns an event ID
    """
    event_id = f"pyui_{uuid.uuid4().hex}"
    _EVENT_REGISTRY[event_id] = handler
    return event_id


def get_registered_events():
    return _EVENT_REGISTRY

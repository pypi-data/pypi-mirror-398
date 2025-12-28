from contextvars import ContextVar
from typing import Optional, Set, Type

# context variables (async-safe)
_current_actor: ContextVar[Optional[str]] = ContextVar(
    "activity_tracker_current_actor", default=None
)

_request_metadata: ContextVar[Optional[dict]] = ContextVar(
    "activity_tracker_request_metadata", default={}
)

_audited_models: ContextVar[Set[Type]] = ContextVar(
    "activity_tracker_audited_models", default=set()
)


def mark_model_audited(model_cls):
    audited = set(_audited_models.get())
    audited.add(model_cls)
    _audited_models.set(audited)


def is_model_audited(model_cls) -> bool:
    return model_cls in _audited_models.get()


def clear_audited_models():
    _audited_models.set(set())


def set_actor(actor: Optional[str]):
    """
    Set the current actor for the context.
    """
    _current_actor.set(actor)


def get_actor() -> Optional[str]:
    """
    Get the current actor from the context.
    """
    return _current_actor.get()


def clear_actor():
    """
    Clear the current actor from the context.
    """
    _current_actor.set(None)


def set_request_metadata(metadata: dict):
    """
    Set the request metadata for the context.
    """
    _request_metadata.set(metadata or {})


def get_request_metadata() -> dict:
    """
    Get the request metadata from the context.
    """
    return _request_metadata.get() or {}


def clear_request_metadata():
    """
    Clear the request metadata from the context.
    """
    _request_metadata.set({})

import importlib
from typing import Optional

from .context import get_actor
from .settings import get_setting


# action normalization
def normalize_action(action: str) -> str:
    """
    Normalize action name.

    :param action: The action name to normalize.
    """
    if not action:
        return ""
    return action.strip().upper().replace(" ", "_")


# drf detection
def is_drf_request(request) -> bool:
    """
    Check whether the request looks like a DRF request
    without importing DRF directly.
    """
    return hasattr(request, "auth") and hasattr(request, "accepted_renderer")


# actor resolution
def default_actor_resolver(request) -> Optional[object]:
    """
    Default logic to extract actor from request.
    Works for Django and DRF.
    """
    if not request:
        return None

    user = getattr(request, "user", None)

    if not user:
        return None

    if not user.is_authenticated:
        if not get_setting("TRACK_ANONYMOUS"):
            return None

    return user


def load_actor_resolver():
    """
    Load custom actor resolver if configured.

    settings:
    ACTIVITY_TRACKER = {
        "ACTOR_RESOLVER": "path.to.custom.actor.resolver"
    }
    """
    path = get_setting("ACTOR_RESOLVER")

    if not path:
        return default_actor_resolver

    try:
        module_path, func_name = path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        resolver = getattr(module, func_name)
        return resolver
    except Exception:
        return default_actor_resolver


def resolve_actor(request) -> Optional[object]:
    """
    Resolve actor in priority order:
    1. Explicit actor via request
    2. Context-propagated actor (middleware)
    """
    if request is not None:
        resolver = load_actor_resolver()
        actor = resolver(request)
        if actor:
            return actor
    return get_actor()

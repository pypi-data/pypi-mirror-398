from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .context import get_request_metadata
from .models import ActivityLog
from .settings import get_setting
from .utils import normalize_action, resolve_actor


def track_activity(
    *,
    action: str,
    request: Optional[object] = None,
    actor: Optional[object] = None,
    target: Optional[object] = None,
    metadata: Optional[dict] = None,
    fail_silently: bool = True,
) -> ActivityLog:
    """
    Central service to record an activity event.
    This function MUST be safe to call from anywhere.
    """
    # Master kill switch
    if not get_setting("ENABLED"):
        return None

    try:
        # normalize action
        action_value = normalize_action(action)

        if not action_value:
            return None

        # resolve actor
        if actor is None:
            actor = resolve_actor(request)

        # ignore anonymous users if configured
        if actor is None and get_setting("TRACK_ANONYMOUS"):
            return None

        # ignore unwanted actions
        ignored = get_setting("IGNORE_ACTIONS")
        if action_value in ignored:
            return None

        # prepare target
        content_type = None
        object_id = None

        if target is not None:
            content_type = ContentType.objects.get_for_model(
                target, for_concrete_model=False
            )
            object_id = str(target.pk)

        # Persist
        if not get_setting("PERSIST"):
            return None

        final_metadata = {}
        final_metadata.update(get_request_metadata())
        final_metadata.update(metadata or {})

        with transaction.atomic():
            activity = ActivityLog.objects.create(
                action=action_value,
                actor=actor,
                target_content_type=content_type,
                target_object_id=object_id,
                metadata=final_metadata,
            )
        return activity

    except Exception as e:
        if fail_silently:
            return None
        raise e

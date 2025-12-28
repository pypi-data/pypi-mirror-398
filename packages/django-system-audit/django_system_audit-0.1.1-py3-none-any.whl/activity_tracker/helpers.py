from typing import Optional

from .constants import ActivityAction
from .services import track_activity


# CRUD Helpers
def audit_create(*, instance, request, metadata: Optional[dict] = None):
    return track_activity(
        action=ActivityAction.CREATE,
        request=request,
        actor=getattr(request, "user", None),
        target=instance,
        metadata=_with_source(metadata, "api"),
    )


def audit_update(
    *, instance, request, validated_data: dict, metadata: Optional[dict] = None
):
    """
    Audit an UPDATE action using serializer.validated_data
    (intent-level diff).
    """
    diffs = {
        field: {
            "old": getattr(instance, field, None),
            "new": value,
        }
        for field, value in validated_data.items()
        if getattr(instance, field, None) != value
    }

    if not diffs:
        return None

    return track_activity(
        action=ActivityAction.UPDATE,
        request=request,
        actor=getattr(request, "user", None),
        target=instance,
        metadata=_with_source(
            {
                "diffs": diffs,
                **(metadata or {}),
            },
            source="api",
        ),
    )


def audit_delete(*, instance, request, metadata: Optional[dict] = None):
    """
    Audit a DELETE action from APIView / GenericAPIView.
    """
    return track_activity(
        action=ActivityAction.DELETE,
        request=request,
        actor=getattr(request, "user", None),
        target=instance,
        metadata=_with_source(metadata, source="api"),
    )


def _with_source(metadata: Optional[dict], *, source: str) -> dict:
    data = metadata.copy() if metadata else {}
    data.setdefault("source", source)
    return data

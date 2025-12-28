"""
DRF integration helpers for activity tracking.

These helpers are INTENT-LEVEL.
They must be called explicitly from auth views.
"""

from typing import Optional

from .constants import ActivityAction
from .services import track_activity


def track_login(
    *, request, user, auth_type: str = "jwt", metadata: Optional[dict] = None
):
    """
    Track a login event for stateless auth systems (JWT / OAuth).

    Should be called AFTER credentials are validated
    and tokens are issued.
    """
    data = metadata or {}
    data.setdefault("auth_type", auth_type)
    return track_activity(
        action=ActivityAction.LOGIN,
        actor=user,
        request=request,
        metadata=data,
    )


def track_logout(
    *, request, user, auth_type: str = "jwt", metadata: Optional[dict] = None
):
    """
    Track a logout / token revoke / client sign-out event.

    Even if tokens are not technically revoked,
    this represents user intent.
    """
    data = metadata or {}
    data.setdefault("auth_type", auth_type)
    return track_activity(
        action=ActivityAction.LOGOUT,
        actor=user,
        request=request,
        metadata=data,
    )


def track_auth_event(
    *,
    action: str,
    request,
    user=None,
    auth_type: str = "jwt",
    metadata: Optional[dict] = None
):
    """
    Generic helper for custom auth-related events.

    Examples:
    - TOKEN_REFRESH
    - PASSWORD_RESET
    - MFA_VERIFIED
    """
    data = metadata or {}
    data.setdefault("auth_type", auth_type)
    return track_activity(
        action=action,
        actor=user,
        request=request,
        metadata=data,
    )

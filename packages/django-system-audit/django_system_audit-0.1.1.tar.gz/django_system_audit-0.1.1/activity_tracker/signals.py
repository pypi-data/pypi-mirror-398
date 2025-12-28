from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .constants import ActivityAction
from .services import track_activity
from .settings import get_setting


@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """
    Track user login.
    """
    if not get_setting("ENABLED"):
        return

    track_activity(
        action=ActivityAction.LOGIN,
        actor=user,
        request=request,
    )


@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """
    Track user logout.
    """
    if not get_setting("ENABLED"):
        return

    track_activity(
        action=ActivityAction.LOGOUT,
        actor=user,
        request=request,
    )

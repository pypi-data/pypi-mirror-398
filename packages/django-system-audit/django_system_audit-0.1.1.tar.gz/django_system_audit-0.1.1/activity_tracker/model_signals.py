from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from activity_tracker.context import is_model_audited

from .constants import ActivityAction
from .diff import compute_field_diff
from .services import track_activity
from .settings import get_setting


class TrackModelActivityMixin:
    """
    Opt-in mixin for models that want CRUD activity tracking.

    Usage:
        class Article(TrackModelActivityMixin, models.Model):
            ...
    """

    # Fields to track diffs for (None = all non-sensitive fields)
    TRACK_FIELDS = None

    #  Fields to exclude from tracking diffs
    #  (e.g. password, tokens, etc.)
    SENSITIVE_FIELDS = set()

    class Meta:
        abstract = True


@receiver(post_save)
def track_model_save(sender, instance, created, **kwargs):
    """
    Track CREATE and UPDATE events for opted-in models only.
    """
    if not get_setting("ENABLED"):
        return

    if not isinstance(instance, TrackModelActivityMixin):
        return

    if is_model_audited(instance.__class__):
        return

    # create
    if created:
        track_activity(
            action=ActivityAction.CREATE,
            target=instance,
        )
        return

    # update: compute diffs
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    diffs = compute_field_diff(
        old=old,
        new=instance,
        track_fields=instance.TRACK_FIELDS,
        sensitive_fields=instance.SENSITIVE_FIELDS,
    )

    if not diffs:
        return

    track_activity(
        action=ActivityAction.UPDATE,
        target=instance,
        metadata={
            "diff": diffs,
        },
    )


@receiver(pre_delete)
def track_model_delete(sender, instance, **kwargs):
    """
    Track DELETE events for opted-in models only.
    """
    if not get_setting("ENABLED"):
        return

    if not isinstance(instance, TrackModelActivityMixin):
        return

    if is_model_audited(instance.__class__):
        return

    track_activity(
        action=ActivityAction.DELETE,
        target=instance,
    )

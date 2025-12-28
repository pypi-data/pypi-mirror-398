from activity_tracker.constants import ActivityAction
from activity_tracker.context import mark_model_audited
from activity_tracker.services import track_activity


class AuditModelViewSetMixin:
    """
    DRF ViewSet mixin for precise audit tracking.
    Must be placed BEFORE ModelViewSet in inheritance order.
    """

    audit_create_action = ActivityAction.CREATE
    audit_update_action = ActivityAction.UPDATE
    audit_delete_action = ActivityAction.DELETE

    def perform_create(self, serializer):
        instance = serializer.save()
        mark_model_audited(instance.__class__)
        track_activity(
            action=self.audit_create_action,
            request=self.request,
            actor=self.request.user,
            target=instance,
            metadata={
                "source": "api",
                "serializer": serializer.__class__.__name__,
            },
        )
        return instance

    def perform_update(self, serializer):
        instance = self.get_object()

        # serializer.validated_data contains INTENT
        diffs = {
            field: {
                "old": getattr(instance, field, None),
                "new": value,
            }
            for field, value in serializer.validated_data.items()
            if getattr(instance, field, None) != value
        }

        instance = serializer.save()
        mark_model_audited(instance.__class__)
        track_activity(
            action=self.audit_update_action,
            request=self.request,
            actor=self.request.user,
            target=instance,
            metadata={
                "source": "api",
                "serializer": serializer.__class__.__name__,
                "diffs": diffs,
            },
        )
        return instance

    def perform_destroy(self, instance):
        mark_model_audited(instance.__class__)
        track_activity(
            action=self.audit_delete_action,
            request=self.request,
            actor=self.request.user,
            target=instance,
            metadata={
                "source": "api",
            },
        )
        instance.delete()

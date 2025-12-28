from activity_tracker.constants import ActivityAction
from activity_tracker.context import mark_model_audited
from activity_tracker.services import track_activity


class AuditModelAdminMixin:
    """
    Admin mixin for precise audit tracking.
    Must be mixed BEFORE admin.ModelAdmin.
    """

    audit_create_action = ActivityAction.CREATE
    audit_update_action = ActivityAction.UPDATE
    audit_delete_action = ActivityAction.DELETE

    def save_model(self, request, obj, form, change):
        """Track CREATE and UPDATE from admin."""
        if change:
            diffs = {
                field: {
                    "old": form.initial.get(field),
                    "new": form.cleaned_data.get(field),
                }
                for field in form.changed_data
            }

            super().save_model(request, obj, form, change)

            if diffs:
                mark_model_audited(obj.__class__)
                track_activity(
                    action=self.audit_update_action,
                    request=request,
                    actor=request.user,
                    target=obj,
                    metadata={
                        "source": "admin",
                        "diffs": diffs,
                        "admin": self.__class__.__name__,
                    },
                )
        else:
            super().save_model(request, obj, form, change)
            mark_model_audited(obj.__class__)
            track_activity(
                action=self.audit_create_action,
                request=request,
                actor=request.user,
                target=obj,
                metadata={
                    "source": "admin",
                    "admin": self.__class__.__name__,
                },
            )

    def delete_model(self, request, obj):
        """Track DELETE from admin."""
        mark_model_audited(obj.__class__)
        track_activity(
            action=self.audit_delete_action,
            request=request,
            actor=request.user,
            target=obj,
            metadata={
                "source": "admin",
                "admin": self.__class__.__name__,
            },
        )

        super().delete_model(request, obj)

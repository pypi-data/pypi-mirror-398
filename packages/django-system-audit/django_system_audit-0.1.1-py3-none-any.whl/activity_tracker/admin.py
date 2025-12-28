from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "actor",
        "action",
        "target",
        "created_at",
    ]
    list_filter = [
        "action",
        "created_at",
    ]
    search_fields = [
        "actor__username",
        "actor__email",
        "target_object_id",
    ]
    ordering = ["-created_at"]

    readonly_fields = [
        "actor",
        "action",
        "target_content_type",
        "target_object_id",
        "metadata",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

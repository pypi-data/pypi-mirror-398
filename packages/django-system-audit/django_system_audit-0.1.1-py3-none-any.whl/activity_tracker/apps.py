from django.apps import AppConfig


class ActivityTrackerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity_tracker"
    verbose_name = "Activity Tracker"

    def ready(self):
        from . import signals  # noqa
        from . import model_signals # CRUD
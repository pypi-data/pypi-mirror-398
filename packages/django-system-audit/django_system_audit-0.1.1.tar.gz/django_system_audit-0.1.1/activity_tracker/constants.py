from django.db import models


class ActivityAction(models.TextChoices):
    """
    Canonical list of actions that can be tracked.

    This is a PUBLIC CONTRACT.
    Changing existing values is a breaking change.
    """

    # Authentication
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"

    # CRUD
    VIEW = "VIEW", "View"
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"

    # System
    SYSTEM = "SYSTEM", "System"
    CUSTOM = "CUSTOM", "Custom"

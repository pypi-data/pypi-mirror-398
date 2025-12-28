from django.conf import settings as django_settings

DEFAULTS = {
    # Master Switch
    "ENABLED": True,
    # Track unauthenticated users
    "TRACK_ANONYMOUS": True,
    # Persists records to DB
    "PERSIST": True,
    # Allow DRF integration if present
    "ENABLE_DRF": True,
    # List of actions to ignore
    "IGNORE_ACTIONS": [],
    # Callable path for custom actor resolver.
    # Example: "path.to.custom.actor.resolver"
    "ACTOR_RESOLVER": None,
}


def get_user_settings():
    """
    Safely fetch user defined activity tracker settings.
    """
    if not django_settings.configured:
        return {}
    return getattr(django_settings, "ACTIVITY_TRACKER", {})


def get_setting(key):
    """
    Read a single resolved setting value.

    :param key: The setting key to read.
    """
    user_settings = get_user_settings()
    return user_settings.get(key, DEFAULTS[key])


def get_settings():
    """
    Read merged settings dict (DEFAULTS overriden by user settings).
    """
    user_settings = get_user_settings()
    return {**DEFAULTS, **user_settings}

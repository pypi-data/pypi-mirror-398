MASK = "***REDACTED***"


def compute_field_diff(old, new, *, track_fields=None, sensitive_fields=None):
    """
    Compute field-level diffs between two model instances.

    Returns:
        {
            "field_name": {
                "old": old_value,
                "new": new_value
            }
        }
    """
    diffs = {}
    sensitive_fields = sensitive_fields or set()

    for field in old._meta.fields:
        name = field.name

        if track_fields is not None and name not in track_fields:
            continue

        old_value = getattr(old, name, None)
        new_value = getattr(new, name, None)

        if old_value == new_value:
            continue

        if name in sensitive_fields:
            diffs[name] = {"old": MASK, "new": MASK}
        else:
            diffs[name] = {"old": old_value, "new": new_value}

    return diffs

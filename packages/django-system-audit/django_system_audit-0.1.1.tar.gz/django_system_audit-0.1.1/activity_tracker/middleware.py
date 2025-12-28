from .context import (
    clear_actor,
    clear_audited_models,
    clear_request_metadata,
    set_actor,
    set_request_metadata,
)


class ActivityTrackerMiddleware:
    """
    Stores request-scoped context for activity tracking.
    Must be placed AFTER AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # actor
            user = getattr(request, "user", None)
            if user and user.is_authenticated:
                set_actor(user)

            # Metadata
            meta = {
                "ip": self._get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "path": request.path,
                "method": request.method,
            }
            set_request_metadata(meta)

            response = self.get_response(request)
            return response
        finally:
            # IMPORTANT: always clean up
            clear_actor()
            clear_request_metadata()
            clear_audited_models()

    def _get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

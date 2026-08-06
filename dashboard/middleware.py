from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class StaffAreaAccessMiddleware:
    """
    Blocks any request under /<STAFF_LOGIN_PATH>/ that is not made by an
    authenticated user with is_staff=True. Anonymous users are bounced to
    the staff login page; authenticated non-staff users get a redirect
    to the public homepage rather than a revealing 403.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        raw_prefix = settings.STAFF_LOGIN_PATH.strip("/")
        self.prefix = f"/{raw_prefix}/"
        self.prefix_without_slash = f"/{raw_prefix}"

    def __call__(self, request):
        path = request.path
        normalized_path = path if path.endswith("/") else f"{path}/"
        login_path = f"{self.prefix}login/"

        if (normalized_path.startswith(self.prefix) or path == self.prefix_without_slash) and path != login_path and path != login_path.rstrip("/"):
            if not request.user.is_authenticated:
                return redirect(f"{login_path}?next={path}")
            if not request.user.is_staff:
                return redirect("catalog:home")

        return self.get_response(request)

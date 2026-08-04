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
        self.prefix = f"/{settings.STAFF_LOGIN_PATH}/"

    def __call__(self, request):
        path = request.path
        login_path = f"{self.prefix}login/"

        if path.startswith(self.prefix) and path != login_path:
            if not request.user.is_authenticated:
                return redirect(f"{login_path}?next={path}")
            if not request.user.is_staff:
                return redirect("catalog:home")

        return self.get_response(request)

from functools import wraps
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


ALLOWED_MUNICIPAL_ROLES = {
    "municipal_employee",
    "municipal_manager",
}


def municipal_required(view_function):
    @wraps(view_function)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse(
                "municipal_portal:login"
            )

            query_string = urlencode(
                {
                    "next": request.get_full_path(),
                }
            )

            return redirect(
                f"{login_url}?{query_string}"
            )

        is_allowed = (
            request.user.is_superuser
            or request.user.role
            in ALLOWED_MUNICIPAL_ROLES
        )

        if not is_allowed:
            return redirect(
                "municipal_portal:login"
            )

        return view_function(
            request,
            *args,
            **kwargs,
        )

    return wrapped_view
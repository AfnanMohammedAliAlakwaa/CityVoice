from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def municipal_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        allowed_roles = [
            "municipal_employee",
            "municipal_manager",
        ]

        if (
            not request.user.is_superuser
            and request.user.role not in allowed_roles
        ):
            raise PermissionDenied(
                "ليس لديك صلاحية الدخول إلى بوابة البلدية."
            )

        return view_function(request, *args, **kwargs)

    return wrapped_view
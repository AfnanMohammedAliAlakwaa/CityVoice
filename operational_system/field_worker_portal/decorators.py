from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def field_worker_required(view_func):
    """السماح للعامل الميداني النشط فقط بدخول بوابة العامل."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("field_worker_portal:login")

        if not request.user.is_active:
            messages.error(request, "هذا الحساب غير نشط.")
            return redirect("field_worker_portal:login")

        if request.user.role != "field_worker":
            messages.error(request, "هذه البوابة مخصصة للعاملين الميدانيين.")

            if request.user.role in {
                "municipal_employee",
                "municipal_manager",
            }:
                return redirect("municipal_portal:dashboard")

            return redirect("citizen_portal:home")

        return view_func(request, *args, **kwargs)

    return wrapped_view

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .decorators import field_worker_required


def redirect_authenticated_user(user):
    if user.role == "field_worker":
        return redirect("field_worker_portal:dashboard")

    if user.role in {"municipal_employee", "municipal_manager"}:
        return redirect("municipal_portal:dashboard")

    return redirect("citizen_portal:home")


@require_http_methods(["GET", "POST"])
def worker_login(request):
    if request.user.is_authenticated:
        return redirect_authenticated_user(request.user)

    username = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "أدخل اسم المستخدم وكلمة المرور.")
        else:
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:
                messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")
            elif not user.is_active:
                messages.error(request, "هذا الحساب غير نشط. راجع مدير البلدية.")
            elif user.role != "field_worker":
                messages.error(request, "هذا الحساب غير مصرح له بدخول بوابة العامل.")
            else:
                login(request, user)
                return redirect("field_worker_portal:dashboard")

    return render(
        request,
        "field_worker_portal/login.html",
        {"username": username},
    )


@field_worker_required
def dashboard(request):
    return render(request, "field_worker_portal/dashboard.html")


@require_POST
def worker_logout(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج بنجاح.")
    return redirect("field_worker_portal:login")

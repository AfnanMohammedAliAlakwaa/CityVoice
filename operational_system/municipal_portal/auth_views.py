from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)


MUNICIPAL_ROLES = {
    "municipal_employee",
    "municipal_manager",
}


def is_municipal_user(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.role in MUNICIPAL_ROLES
        )
    )


@require_http_methods(["GET", "POST"])
def municipal_login(request):
    if is_municipal_user(request.user):
        return redirect(
            "municipal_portal:dashboard"
        )

    # إذا كان هناك مواطن أو عامل مسجل في المتصفح،
    # ننهي جلسته للسماح بالدخول بحساب البلدية.
    if request.user.is_authenticated:
        logout(request)

    username = ""

    if request.method == "POST":
        username = request.POST.get(
            "username",
            "",
        ).strip()

        password = request.POST.get(
            "password",
            "",
        )

        if not username or not password:
            messages.error(
                request,
                "أدخل اسم المستخدم وكلمة المرور.",
            )

        else:
            user = authenticate(
                request,
                username=username,
                password=password,
            )

            if user is None:
                messages.error(
                    request,
                    "اسم المستخدم أو كلمة المرور غير صحيحة.",
                )

            elif not user.is_active:
                messages.error(
                    request,
                    "هذا الحساب غير نشط. راجع مدير النظام.",
                )

            elif (
                not user.is_superuser
                and user.role not in MUNICIPAL_ROLES
            ):
                messages.error(
                    request,
                    "هذا الحساب غير مصرح له بدخول بوابة البلدية.",
                )

            else:
                login(request, user)

                next_url = request.POST.get(
                    "next",
                    "",
                )

                if (
                    next_url
                    and next_url.startswith("/")
                    and not next_url.startswith("//")
                ):
                    return redirect(next_url)

                return redirect(
                    "municipal_portal:dashboard"
                )

    return render(
        request,
        "municipal_portal/login.html",
        {
            "username": username,
            "next": request.GET.get(
                "next",
                request.POST.get("next", ""),
            ),
        },
    )


@require_POST
def municipal_logout(request):
    logout(request)

    messages.success(
        request,
        "تم تسجيل الخروج من بوابة البلدية بنجاح.",
    )

    return redirect(
        "municipal_portal:login"
    )
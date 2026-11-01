from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from maintenance.models import WorkOrder

from .decorators import field_worker_required


def redirect_authenticated_user(user):
    if user.role == "field_worker":
        return redirect("field_worker_portal:dashboard")

    if user.role in {
        "municipal_employee",
        "municipal_manager",
    }:
        return redirect("municipal_portal:dashboard")

    return redirect("citizen_portal:home")


@require_http_methods(["GET", "POST"])
def worker_login(request):
    if request.user.is_authenticated:
        return redirect_authenticated_user(request.user)

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
                    "هذا الحساب غير نشط. راجع مدير البلدية.",
                )
            elif user.role != "field_worker":
                messages.error(
                    request,
                    "هذا الحساب غير مصرح له بدخول بوابة العامل.",
                )
            else:
                login(request, user)

                return redirect(
                    "field_worker_portal:dashboard"
                )

    return render(
        request,
        "field_worker_portal/login.html",
        {
            "username": username,
        },
    )


@field_worker_required
def dashboard(request):
    selected_status = request.GET.get(
        "status",
        "all",
    ).strip()

    allowed_filters = {
        "all",
        "new",
        "active",
        "completed",
    }

    if selected_status not in allowed_filters:
        selected_status = "all"

    worker_orders = (
        WorkOrder.objects
        .filter(assigned_to=request.user)
        .select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "assigned_by",
        )
    )

    today = timezone.localdate()

    new_count = worker_orders.filter(
        status=WorkOrder.Status.ASSIGNED,
    ).count()

    active_count = worker_orders.filter(
        status__in=[
            WorkOrder.Status.ACCEPTED,
            WorkOrder.Status.IN_PROGRESS,
        ],
    ).count()

    completed_today_count = worker_orders.filter(
        status=WorkOrder.Status.COMPLETED,
        completed_at__date=today,
    ).count()

    visible_orders = worker_orders

    if selected_status == "new":
        visible_orders = visible_orders.filter(
            status=WorkOrder.Status.ASSIGNED,
        )

    elif selected_status == "active":
        visible_orders = visible_orders.filter(
            status__in=[
                WorkOrder.Status.ACCEPTED,
                WorkOrder.Status.IN_PROGRESS,
            ],
        )

    elif selected_status == "completed":
        visible_orders = visible_orders.filter(
            status=WorkOrder.Status.COMPLETED,
        )

    else:
        visible_orders = visible_orders.filter(
            Q(
                status=WorkOrder.Status.ASSIGNED,
            )
            | Q(
                status=WorkOrder.Status.ACCEPTED,
            )
            | Q(
                status=WorkOrder.Status.IN_PROGRESS,
            )
        )

    visible_orders = visible_orders.order_by(
        "-created_at",
    )

    context = {
        "work_orders": visible_orders,
        "selected_status": selected_status,
        "new_count": new_count,
        "active_count": active_count,
        "completed_today_count": completed_today_count,
    }

    return render(
        request,
        "field_worker_portal/dashboard.html",
        context,
    )


@require_POST
def worker_logout(request):
    logout(request)

    messages.success(
        request,
        "تم تسجيل الخروج بنجاح.",
    )

    return redirect(
        "field_worker_portal:login"
    )
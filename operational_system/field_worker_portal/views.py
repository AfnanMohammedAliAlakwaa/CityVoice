from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.db.models import Q

from django.utils import timezone
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
)

from maintenance.models import WorkOrder

from .decorators import field_worker_required
from .forms import WorkOrderCompletionForm


def redirect_authenticated_user(user):
    if user.role == "field_worker":
        return redirect(
            "field_worker_portal:dashboard"
        )

    if user.role in {
        "municipal_employee",
        "municipal_manager",
    }:
        return redirect(
            "municipal_portal:dashboard"
        )

    return redirect(
        "citizen_portal:home"
    )


@require_http_methods(["GET", "POST"])
def worker_login(request):
    if request.user.is_authenticated:
        return redirect_authenticated_user(
            request.user
        )

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


def worker_order_queryset(request):
    return (
        WorkOrder.objects
        .filter(assigned_to=request.user)
        .select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "complaint__asset",
            "complaint__neighborhood",
            "assigned_by",
        )
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

    worker_orders = worker_order_queryset(request)

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
            Q(status=WorkOrder.Status.ASSIGNED)
            | Q(status=WorkOrder.Status.ACCEPTED)
            | Q(status=WorkOrder.Status.IN_PROGRESS)
        )

    visible_orders = visible_orders.order_by(
        "-created_at",
    )

    return render(
        request,
        "field_worker_portal/dashboard.html",
        {
            "work_orders": visible_orders,
            "selected_status": selected_status,
            "new_count": new_count,
            "active_count": active_count,
            "completed_today_count": (
                completed_today_count
            ),
        },
    )

def build_task_detail_context(
    work_order,
    completion_form=None,
):
    complaint_latitude = None
    complaint_longitude = None

    if work_order.complaint.location:
        complaint_latitude = format(
            work_order.complaint.location.y,
            ".8f",
        )

        complaint_longitude = format(
            work_order.complaint.location.x,
            ".8f",
        )

    if completion_form is None:
        completion_form = WorkOrderCompletionForm()

    return {
        "work_order": work_order,
        "completion_form": completion_form,
        "complaint_latitude": complaint_latitude,
        "complaint_longitude": complaint_longitude,
    }
@field_worker_required
def task_detail(request, order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "assigned_by",
        ),
        pk=order_id,
        assigned_to=request.user,
    )

    return render(
        request,
        "field_worker_portal/task_detail.html",
        build_task_detail_context(work_order),
    )

@field_worker_required
@require_POST
def accept_task(request, order_id):
    work_order = get_object_or_404(
        WorkOrder,
        pk=order_id,
        assigned_to=request.user,
    )

    if work_order.status != WorkOrder.Status.ASSIGNED:
        messages.error(
            request,
            "لا يمكن قبول هذه المهمة في حالتها الحالية.",
        )
    else:
        work_order.status = WorkOrder.Status.ACCEPTED
        work_order.save()

        messages.success(
            request,
            "تم قبول المهمة بنجاح.",
        )

    return redirect(
        "field_worker_portal:task_detail",
        order_id=work_order.pk,
    )


@field_worker_required
@require_POST
def start_task(request, order_id):
    work_order = get_object_or_404(
        WorkOrder,
        pk=order_id,
        assigned_to=request.user,
    )

    if work_order.status != WorkOrder.Status.ACCEPTED:
        messages.error(
            request,
            "يجب قبول المهمة قبل بدء التنفيذ.",
        )
    else:
        work_order.status = WorkOrder.Status.IN_PROGRESS
        work_order.save()

        messages.success(
            request,
            "تم بدء تنفيذ المهمة.",
        )

    return redirect(
        "field_worker_portal:task_detail",
        order_id=work_order.pk,
    )


@field_worker_required
@require_POST
def complete_task(request, order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "assigned_by",
        ),
        pk=order_id,
        assigned_to=request.user,
    )

    if work_order.status != WorkOrder.Status.IN_PROGRESS:
        messages.error(
            request,
            "لا يمكن إكمال المهمة قبل بدء التنفيذ.",
        )

        return redirect(
    "field_worker_portal:task_detail",
    order_id=work_order.pk,
)

    completion_form = WorkOrderCompletionForm(
        request.POST,
        request.FILES,
        instance=work_order,
    )

    if completion_form.is_valid():
        completed_order = completion_form.save(
            commit=False,
        )

        completed_order.status = (
            WorkOrder.Status.COMPLETED
        )

        completed_order.save()

        messages.success(
            request,
            "تم تسجيل إنجاز المهمة بنجاح.",
        )

        return redirect(
    "field_worker_portal:task_detail",
    order_id=work_order.pk,
)

    return render(
        request,
        "field_worker_portal/task_detail.html",
        build_task_detail_context(
            work_order,
            completion_form,
        ),
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
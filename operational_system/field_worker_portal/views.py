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
from .forms import (
    WorkerAvatarForm,
    WorkOrderCompletionForm,
)

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
                "Ø£Ø¯Ø®Ù„ Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… ÙˆÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ±.",
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
                    "Ø§Ø³Ù… Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù… Ø£Ùˆ ÙƒÙ„Ù…Ø© Ø§Ù„Ù…Ø±ÙˆØ± ØºÙŠØ± ØµØ­ÙŠØ­Ø©.",
                )

            elif not user.is_active:
                messages.error(
                    request,
                    "Ù‡Ø°Ø§ Ø§Ù„Ø­Ø³Ø§Ø¨ ØºÙŠØ± Ù†Ø´Ø·. Ø±Ø§Ø¬Ø¹ Ù…Ø¯ÙŠØ± Ø§Ù„Ø¨Ù„Ø¯ÙŠØ©.",
                )

            elif user.role != "field_worker":
                messages.error(
                    request,
                    "Ù‡Ø°Ø§ Ø§Ù„Ø­Ø³Ø§Ø¨ ØºÙŠØ± Ù…ØµØ±Ø­ Ù„Ù‡ Ø¨Ø¯Ø®ÙˆÙ„ Ø¨ÙˆØ§Ø¨Ø© Ø§Ù„Ø¹Ø§Ù…Ù„.",
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
def build_dashboard_context(request, tasks_page=False):
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
        if tasks_page:
            # ÙÙŠ ØµÙØ­Ø© Ø§Ù„Ù…Ù‡Ø§Ù… ÙŠØ¸Ù‡Ø± Ø§Ù„ÙƒÙ„ØŒ Ø¨Ù…Ø§ ÙÙŠÙ‡ Ø§Ù„Ù…Ù‡Ø§Ù… Ø§Ù„Ù…ÙƒØªÙ…Ù„Ø©
            visible_orders = visible_orders.filter(
                status__in=[
                    WorkOrder.Status.ASSIGNED,
                    WorkOrder.Status.ACCEPTED,
                    WorkOrder.Status.IN_PROGRESS,
                    WorkOrder.Status.COMPLETED,
                ],
            )
        else:
            # ÙÙŠ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© ØªØ¸Ù‡Ø± Ø§Ù„Ù…Ù‡Ø§Ù… Ø§Ù„Ø­Ø§Ù„ÙŠØ© ÙÙ‚Ø·
            visible_orders = visible_orders.filter(
                Q(status=WorkOrder.Status.ASSIGNED)
                | Q(status=WorkOrder.Status.ACCEPTED)
                | Q(status=WorkOrder.Status.IN_PROGRESS)
            )

    visible_orders = visible_orders.order_by(
        "-created_at",
    )

    return {
        "work_orders": visible_orders,
        "selected_status": selected_status,
        "new_count": new_count,
        "active_count": active_count,
        "completed_today_count": completed_today_count,
        "tasks_page": tasks_page,
    }


@field_worker_required
def dashboard(request):
    return render(
        request,
        "field_worker_portal/dashboard.html",
        build_dashboard_context(
            request,
            tasks_page=False,
        ),
    )
@field_worker_required
def task_list(request):
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

    if selected_status == "new":
        visible_orders = worker_orders.filter(
            status=WorkOrder.Status.ASSIGNED,
        )

    elif selected_status == "active":
        visible_orders = worker_orders.filter(
            status__in=[
                WorkOrder.Status.ACCEPTED,
                WorkOrder.Status.IN_PROGRESS,
            ],
        )

    elif selected_status == "completed":
        visible_orders = worker_orders.filter(
            status=WorkOrder.Status.COMPLETED,
        )

    else:
        visible_orders = worker_orders

    visible_orders = visible_orders.order_by(
        "-created_at",
    )

    return render(
        request,
        "field_worker_portal/tasks.html",
        {
            "work_orders": visible_orders,
            "selected_status": selected_status,
            "total_count": worker_orders.count(),
            "new_count": worker_orders.filter(
                status=WorkOrder.Status.ASSIGNED,
            ).count(),
            "active_count": worker_orders.filter(
                status__in=[
                    WorkOrder.Status.ACCEPTED,
                    WorkOrder.Status.IN_PROGRESS,
                ],
            ).count(),
            "completed_count": worker_orders.filter(
                status=WorkOrder.Status.COMPLETED,
            ).count(),
        },
    )

@field_worker_required
def tasks(request):
    return render(
        request,
        "field_worker_portal/dashboard.html",
        build_dashboard_context(
            request,
            tasks_page=True,
        ),
    )
@field_worker_required
def notifications(request):
    notification_orders = (
        worker_order_queryset(request)
        .filter(
            status=WorkOrder.Status.ASSIGNED,
        )
        .order_by("-created_at")
    )

    new_notifications_count = (
        notification_orders.count()
    )

    return render(
        request,
        "field_worker_portal/notifications.html",
        {
            "notification_orders": notification_orders,
            "new_notifications_count": (
                new_notifications_count
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
            "Ù„Ø§ ÙŠÙ…ÙƒÙ† Ù‚Ø¨ÙˆÙ„ Ù‡Ø°Ù‡ Ø§Ù„Ù…Ù‡Ù…Ø© ÙÙŠ Ø­Ø§Ù„ØªÙ‡Ø§ Ø§Ù„Ø­Ø§Ù„ÙŠØ©.",
        )
    else:
        work_order.status = WorkOrder.Status.ACCEPTED
        work_order.save()

        messages.success(
            request,
            "ØªÙ… Ù‚Ø¨ÙˆÙ„ Ø§Ù„Ù…Ù‡Ù…Ø© Ø¨Ù†Ø¬Ø§Ø­.",
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
            "ÙŠØ¬Ø¨ Ù‚Ø¨ÙˆÙ„ Ø§Ù„Ù…Ù‡Ù…Ø© Ù‚Ø¨Ù„ Ø¨Ø¯Ø¡ Ø§Ù„ØªÙ†ÙÙŠØ°.",
        )
    else:
        work_order.status = WorkOrder.Status.IN_PROGRESS
        work_order.save()

        messages.success(
            request,
            "ØªÙ… Ø¨Ø¯Ø¡ ØªÙ†ÙÙŠØ° Ø§Ù„Ù…Ù‡Ù…Ø©.",
        )

    return redirect(
        "field_worker_portal:task_detail",
        order_id=work_order.pk,
    )

@field_worker_required
def achievements(request):
    achievement_orders = (
        worker_order_queryset(request)
        .filter(
            status__in=[
                WorkOrder.Status.IN_PROGRESS,
                WorkOrder.Status.COMPLETED,
            ],
        )
        .order_by("-updated_at")
    )

    in_progress_orders = achievement_orders.filter(
        status=WorkOrder.Status.IN_PROGRESS,
    )

    completed_orders = achievement_orders.filter(
        status=WorkOrder.Status.COMPLETED,
    )

    return render(
        request,
        "field_worker_portal/achievements.html",
        {
            "achievement_orders": achievement_orders,
            "in_progress_count": in_progress_orders.count(),
            "completed_count": completed_orders.count(),
        },
    )
@field_worker_required
def achievement_detail(request, order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "complaint__asset",
            "complaint__neighborhood",
            "assigned_by",
        ),
        pk=order_id,
        assigned_to=request.user,
        status=WorkOrder.Status.COMPLETED,
    )

    return render(
        request,
        "field_worker_portal/achievement_detail.html",
        {
            "work_order": work_order,
        },
        )
@field_worker_required
@require_http_methods(["GET", "POST"])
def complete_task(request, order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
            "complaint__asset",
            "complaint__neighborhood",
            "assigned_by",
        ),
        pk=order_id,
        assigned_to=request.user,
    )

    if work_order.status != WorkOrder.Status.IN_PROGRESS:
        messages.error(
            request,
            "Ù„Ø§ ÙŠÙ…ÙƒÙ† ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¥Ù†Ø¬Ø§Ø² Ù‚Ø¨Ù„ Ø¨Ø¯Ø¡ ØªÙ†ÙÙŠØ° Ø§Ù„Ù…Ù‡Ù…Ø©.",
        )

        return redirect(
            "field_worker_portal:completion_success",
                order_id=completed_order.pk,
            )

    if request.method == "POST":
        completion_form = WorkOrderCompletionForm(
            request.POST,
            request.FILES,
            instance=work_order,
        )

        if completion_form.is_valid():
            with transaction.atomic():
                completed_order = completion_form.save(
                    commit=False,
                )

                completed_order.status = (
                    WorkOrder.Status.COMPLETED
                )

                completed_order.completed_at = timezone.now()
                completed_order.save()

            messages.success(
                request,
                "ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø¥Ù†Ø¬Ø§Ø² Ø§Ù„Ù…Ù‡Ù…Ø© Ø¨Ù†Ø¬Ø§Ø­.",
            )

            return redirect(
                "field_worker_portal:completion_success",
                order_id=completed_order.pk,
            )

    else:
        completion_form = WorkOrderCompletionForm(
            instance=work_order,
        )

    return render(
        request,
        "field_worker_portal/task_completion.html",
        {
            "work_order": work_order,
            "completion_form": completion_form,
        },
    )
@field_worker_required
def completion_success(request, order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related(
            "complaint",
            "complaint__service",
            "complaint__category",
        ),
        pk=order_id,
        assigned_to=request.user,
        status=WorkOrder.Status.COMPLETED,
    )

    return render(
        request,
        "field_worker_portal/task_completion_success.html",
        {
            "work_order": work_order,
        },
    )
@field_worker_required
@require_http_methods(["GET", "POST"])
def account(request):
    worker_orders = worker_order_queryset(request)

    if request.method == "POST":
        avatar_form = WorkerAvatarForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if avatar_form.is_valid():
            avatar_form.save()

            messages.success(
                request,
                "ØªÙ… ØªØ­Ø¯ÙŠØ« Ø§Ù„ØµÙˆØ±Ø© Ø§Ù„Ø´Ø®ØµÙŠØ© Ø¨Ù†Ø¬Ø§Ø­.",
            )

            return redirect(
                "field_worker_portal:account"
            )

        messages.error(
            request,
            "ØªØ¹Ø°Ø± ØªØ­Ø¯ÙŠØ« Ø§Ù„ØµÙˆØ±Ø©. ØªØ£ÙƒØ¯ Ù…Ù† Ø§Ø®ØªÙŠØ§Ø± ØµÙˆØ±Ø© ØµØ­ÙŠØ­Ø©.",
        )

    else:
        avatar_form = WorkerAvatarForm(
            instance=request.user,
        )

    account_stats = {
        "assigned": worker_orders.filter(
            status=WorkOrder.Status.ASSIGNED,
        ).count(),
        "active": worker_orders.filter(
            status__in=[
                WorkOrder.Status.ACCEPTED,
                WorkOrder.Status.IN_PROGRESS,
            ],
        ).count(),
        "completed": worker_orders.filter(
            status=WorkOrder.Status.COMPLETED,
        ).count(),
    }

    return render(
        request,
        "field_worker_portal/account.html",
        {
            "account_stats": account_stats,
            "avatar_form": avatar_form,
        },
    )


@require_POST
def worker_logout(request):
    logout(request)

    messages.success(
        request,
        "ØªÙ… ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø®Ø±ÙˆØ¬ Ø¨Ù†Ø¬Ø§Ø­.",
    )

    return redirect(
        "field_worker_portal:login"
    )
